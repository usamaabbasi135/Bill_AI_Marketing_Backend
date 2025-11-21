import csv
import io

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt
from urllib.parse import urlparse

from app.extensions import db
from app.models.profile import Profile

bp = Blueprint('profiles', __name__)


def _normalize_linkedin_url(raw_url: str):
    """Validate and normalize LinkedIn profile URLs."""
    if not raw_url:
        return None, None, "linkedin_url cannot be empty"

    url = raw_url.strip()
    if not url:
        return None, None, "linkedin_url cannot be empty"

    if not url.lower().startswith(('http://', 'https://')):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
    except ValueError:
        return None, None, "Invalid linkedin_url format"

    netloc = parsed.netloc.lower()
    if netloc not in ('linkedin.com', 'www.linkedin.com'):
        return None, None, "linkedin_url must point to linkedin.com"

    path = parsed.path.strip('/')
    if not path:
        return None, None, "linkedin_url must include profile path"

    segments = path.split('/')
    section = segments[0].lower()
    if section not in ('in', 'pub', 'profile', 'sales'):
        return None, None, "linkedin_url must point to a profile page"

    username = segments[1] if len(segments) > 1 else ''
    if not username:
        return None, None, "linkedin_url must include a profile username"

    username = username.strip()
    normalized = f"https://www.linkedin.com/{section}/{username}"
    return normalized, username, None


@bp.route('', methods=['POST'])
@jwt_required()
def add_profile():
    """Allow tenants to submit a LinkedIn profile URL manually."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    linkedin_url = data.get('linkedin_url')
    if linkedin_url is None:
        return jsonify({"error": "linkedin_url required"}), 400

    normalized_url, username, error = _normalize_linkedin_url(linkedin_url)
    if error:
        return jsonify({"error": error}), 400

    current_app.logger.debug(
        "Profiles: tenant=%s submitted URL=%s normalized=%s username=%s",
        tenant_id,
        linkedin_url,
        normalized_url,
        username,
    )

    existing = Profile.query.filter_by(
        tenant_id=tenant_id,
        linkedin_url=normalized_url
    ).first()
    if existing:
        return jsonify({
            "error": "Profile already exists",
            "profile_id": existing.profile_id
        }), 400

    profile = Profile(
        tenant_id=tenant_id,
        linkedin_url=normalized_url,
        status='url_only'
    )
    db.session.add(profile)
    db.session.commit()

    response = {
        "profile_id": profile.profile_id,
        "tenant_id": profile.tenant_id,
        "linkedin_url": profile.linkedin_url,
        "username": username,
        "status": profile.status,
        "person_name": profile.person_name,
        "headline": profile.headline,
        "created_at": profile.created_at.isoformat() if profile.created_at else None
    }
    return jsonify({"profile": response}), 201


def _parse_csv(file_storage):
    content = file_storage.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8-sig')
    stream = io.StringIO(content)
    try:
        reader = csv.reader(stream)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    except csv.Error:
        return None, "Invalid CSV format"
    return rows, None


def _extract_url_from_row(row, header_map=None):
    if header_map:
        idx = header_map.get('linkedin_url')
        if idx is None or idx >= len(row):
            return None, None, "linkedin_url column missing"
        name = None
        if 'name' in header_map:
            name_idx = header_map['name']
            if name_idx is not None and name_idx < len(row):
                name = row[name_idx].strip() or None
        return row[idx], name, None

    # simple CSV: first column only
    return row[0] if row else '', None, None


@bp.route('/bulk-upload', methods=['POST'])
@jwt_required()
def bulk_upload_profiles():
    """Allow tenants to upload multiple LinkedIn profile URLs via CSV."""
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401

    uploaded_file = request.files.get('file')
    if not uploaded_file:
        return jsonify({"error": "No file provided"}), 400

    if not uploaded_file.filename.lower().endswith('.csv'):
        return jsonify({"error": "File must be CSV format"}), 400

    rows, parse_error = _parse_csv(uploaded_file)
    if parse_error:
        return jsonify({"error": parse_error}), 400

    if not rows:
        return jsonify({"error": "Invalid CSV format"}), 400

    if len(rows) > 1000:
        return jsonify({"error": "Maximum 1000 profiles allowed"}), 400

    header_map = None
    first_row_lower = [cell.strip().lower() for cell in rows[0]]
    if 'linkedin_url' in first_row_lower:
        header_map = {name: idx for idx, name in enumerate(first_row_lower)}
        data_rows = rows[1:]
    else:
        data_rows = rows

    if not data_rows:
        return jsonify({"error": "No profile rows found"}), 400

    normalized_existing = {
        p.linkedin_url for p in Profile.query.filter_by(tenant_id=tenant_id).all()
    }
    normalized_in_batch = set()
    to_insert = []
    errors = []
    skipped = 0

    for idx, row in enumerate(data_rows, start=1):
        raw_url, person_name, row_error = _extract_url_from_row(row, header_map)
        if row_error:
            errors.append({"row": idx, "error": row_error})
            continue

        normalized_url, username, normalize_error = _normalize_linkedin_url(raw_url)
        if normalize_error:
            errors.append({"row": idx, "error": normalize_error})
            continue

        if normalized_url in normalized_existing or normalized_url in normalized_in_batch:
            skipped += 1
            continue

        profile = Profile(
            tenant_id=tenant_id,
            linkedin_url=normalized_url,
            status='url_only',
            person_name=person_name
        )
        to_insert.append(profile)
        normalized_in_batch.add(normalized_url)

    if not to_insert and not errors and skipped == 0:
        return jsonify({"error": "No valid profiles found in CSV"}), 400

    added = 0
    try:
        if to_insert:
            db.session.add_all(to_insert)
            db.session.commit()
            added = len(to_insert)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Bulk upload failed: %s", exc)
        return jsonify({"error": "Database error occurred"}), 500

    summary = {
        "added": added,
        "skipped": skipped,
        "failed": len(errors),
        "errors": errors,
        "total_rows": len(data_rows)
    }
    return jsonify(summary), 201


@bp.route('/bulk-upload/template', methods=['GET'])
@jwt_required()
def download_bulk_template():
    """Provide CSV template for bulk profile uploads."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['linkedin_url', 'name', 'notes'])
    writer.writerow(['https://www.linkedin.com/in/example/', 'Jane Doe', 'VP Marketing'])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=profile_upload_template.csv'
    return response
