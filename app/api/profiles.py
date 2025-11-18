from flask import Blueprint, request, jsonify, current_app
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

