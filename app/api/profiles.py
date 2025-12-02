import csv
import io
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt
from urllib.parse import urlparse
from sqlalchemy import or_

from app.extensions import db
from app.models.profile import Profile

bp = Blueprint('profiles', __name__)


def _profile_to_dict(profile):
    """Convert Profile model to dictionary for API response."""
    return {
        "profile_id": profile.profile_id,
        "tenant_id": profile.tenant_id,
        "person_name": profile.person_name,
        "headline": profile.headline,
        "linkedin_url": profile.linkedin_url,
        "status": profile.status,
        "email": profile.email,
        "phone": profile.phone,
        "company": profile.company,
        "job_title": profile.job_title,
        "location": profile.location,
        "industry": profile.industry,
        "scraped_at": profile.scraped_at.isoformat() if profile.scraped_at else None,
        "created_at": profile.created_at.isoformat() if profile.created_at else None
    }


@bp.route('', methods=['GET'])
@jwt_required()
def list_profiles():
    """
    List all profiles for the current tenant with filtering, search, pagination, and sorting.
    
    Query Parameters:
        - page: int (default: 1)
        - limit: int (default: 20, max: 100)
        - status: str (url_only, scraped, scraping_failed)
        - company: str (filter by company name)
        - location: str (filter by location)
        - industry: str (filter by industry)
        - search: str (search in person_name, headline, company - case-insensitive, partial match)
        - sort: str (created_at, person_name, scraped_at - default: created_at)
        - order: str (asc, desc - default: desc)
    
    Returns:
        - profiles: array of profile objects
        - pagination: {page, limit, total, pages}
        - stats: {total, scraped, pending, failed}
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        current_app.logger.warning("List profiles: Missing tenant_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    current_app.logger.debug(f"List profiles: Request for tenant_id={tenant_id}")
    
    # Parse pagination parameters
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
        current_app.logger.debug(f"List profiles: Invalid page parameter, defaulting to 1")
    
    try:
        limit = int(request.args.get('limit', 20))
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 20
        current_app.logger.debug(f"List profiles: Invalid limit parameter, defaulting to 20")
    
    # Parse sorting parameters
    sort_field = request.args.get('sort', 'created_at').strip().lower()
    sort_order = request.args.get('order', 'desc').strip().lower()
    
    # Validate sort field
    valid_sort_fields = {'created_at', 'person_name', 'scraped_at'}
    if sort_field not in valid_sort_fields:
        sort_field = 'created_at'
        current_app.logger.debug(f"List profiles: Invalid sort field, defaulting to created_at")
    
    # Validate sort order
    if sort_order not in {'asc', 'desc'}:
        sort_order = 'desc'
        current_app.logger.debug(f"List profiles: Invalid sort order, defaulting to desc")
    
    # Build base query with tenant filter
    query = Profile.query.filter_by(tenant_id=tenant_id)
    
    # Apply filters
    status_filter = request.args.get('status', '').strip()
    if status_filter and status_filter in ['url_only', 'scraped', 'scraping_failed']:
        query = query.filter(Profile.status == status_filter)
        current_app.logger.debug(f"List profiles: Applied status filter={status_filter}")
    
    company_filter = request.args.get('company', '').strip()
    if company_filter:
        query = query.filter(Profile.company.ilike(f'%{company_filter}%'))
        current_app.logger.debug(f"List profiles: Applied company filter={company_filter}")
    
    location_filter = request.args.get('location', '').strip()
    if location_filter:
        query = query.filter(Profile.location.ilike(f'%{location_filter}%'))
        current_app.logger.debug(f"List profiles: Applied location filter={location_filter}")
    
    industry_filter = request.args.get('industry', '').strip()
    if industry_filter:
        query = query.filter(Profile.industry.ilike(f'%{industry_filter}%'))
        current_app.logger.debug(f"List profiles: Applied industry filter={industry_filter}")
    
    # Apply search (case-insensitive, partial match on person_name, headline, company)
    search_term = request.args.get('search', '').strip()
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            or_(
                Profile.person_name.ilike(search_pattern),
                Profile.headline.ilike(search_pattern),
                Profile.company.ilike(search_pattern)
            )
        )
        current_app.logger.debug(f"List profiles: Applied search term={search_term}")
    
    # Get total count (with filters applied) for pagination
    total_count = query.count()
    
    # Get stats for all profiles (without filters) - for overall tenant stats
    # Stats show total counts across all profiles for the tenant
    all_profiles_query = Profile.query.filter_by(tenant_id=tenant_id)
    total_all = all_profiles_query.count()
    scraped_count = all_profiles_query.filter(Profile.status == 'scraped').count()
    pending_count = all_profiles_query.filter(Profile.status == 'url_only').count()
    failed_count = all_profiles_query.filter(Profile.status == 'scraping_failed').count()
    
    current_app.logger.debug(
        f"List profiles: Stats - total={total_all}, scraped={scraped_count}, "
        f"pending={pending_count}, failed={failed_count}"
    )
    
    # Apply sorting
    sort_column = getattr(Profile, sort_field)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    current_app.logger.debug(f"List profiles: Sorting by {sort_field} {sort_order}")
    
    # Apply pagination
    offset = (page - 1) * limit
    profiles = query.offset(offset).limit(limit).all()
    
    current_app.logger.debug(
        f"List profiles: Returning page={page}, limit={limit}, "
        f"total={total_count}, profiles_returned={len(profiles)}"
    )
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    
    # Convert profiles to dictionaries
    profiles_data = [_profile_to_dict(profile) for profile in profiles]
    
    return jsonify({
        "profiles": profiles_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": total_pages
        },
        "stats": {
            "total": total_all,
            "scraped": scraped_count,
            "pending": pending_count,
            "failed": failed_count
        }
    }), 200


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


@bp.route('/scrape', methods=['POST'])
@jwt_required()
def scrape_all_profiles():
    """
    Scrape all profiles with status='url_only' for the current tenant.
    
    Returns job_id immediately (async task). Processes up to 50 profiles per job.
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        current_app.logger.warning("Profile scrape: Missing tenant_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    current_app.logger.debug(f"Profile scrape: Starting scrape for tenant_id={tenant_id}")
    
    # Import here to avoid circular imports
    from app.tasks.scraper import scrape_profiles
    from app.models.job import Job
    import uuid
    
    try:
        # Get profiles count and limit in single optimized query
        profiles_query = Profile.query.filter_by(
            tenant_id=tenant_id,
            status='url_only'
        )
        profile_count = profiles_query.count()
        
        if profile_count == 0:
            current_app.logger.debug(f"Profile scrape: No profiles to scrape for tenant_id={tenant_id}")
            return jsonify({
                "message": "No profiles to scrape",
                "profiles_found": 0
            }), 200
        
        # Create job record
        job_id = str(uuid.uuid4())
        batch_size = min(profile_count, 50)  # Batch limit: 50
        job = Job(
            job_id=job_id,
            tenant_id=tenant_id,
            job_type='profile_scrape',
            status='pending',
            total_items=batch_size
        )
        db.session.add(job)
        db.session.commit()
        
        current_app.logger.debug(f"Profile scrape: Created job_id={job_id} for tenant_id={tenant_id}")
        
        # Check if Celery is properly configured before starting task
        try:
            from app.tasks.celery_app import celery_app
            # Check if broker is configured
            broker_url = celery_app.conf.broker_url
            if not broker_url or broker_url == 'memory://':
                raise ValueError("Celery broker is not properly configured. Please check Redis connection.")
        except Exception as celery_check_error:
            current_app.logger.error(f"Profile scrape: Celery configuration error: {str(celery_check_error)}")
            job.status = 'failed'
            job.error_message = f"Celery/Redis not configured: {str(celery_check_error)}"
            job.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "error": "Celery/Redis service not available",
                "details": str(celery_check_error),
                "message": "Please ensure Redis is running and CELERY_BROKER_URL is configured"
            }), 503
        
        # Start async Celery task
        try:
            task = scrape_profiles.delay(job_id, tenant_id, profile_ids=None)
            current_app.logger.info(f"Profile scrape: Started job_id={job_id}, task_id={task.id}, tenant_id={tenant_id}")
        except Exception as celery_error:
            # Handle Celery connection errors specifically
            error_msg = str(celery_error)
            if 'Redis' in error_msg or 'broker' in error_msg.lower() or 'connection' in error_msg.lower():
                current_app.logger.error(f"Profile scrape: Celery/Redis connection error: {error_msg}")
                job.status = 'failed'
                job.error_message = f"Celery/Redis connection failed: {error_msg}"
                job.completed_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    "error": "Celery/Redis connection failed",
                    "details": error_msg,
                    "message": "Please ensure Redis is running and accessible"
                }), 503
            else:
                # Re-raise other errors to be caught by outer exception handler
                raise
        
        return jsonify({
            "message": "Scraping job started",
            "job_id": job_id,
            "profiles_found": profile_count,
            "profiles_in_batch": batch_size,
            "status_url": f"/api/jobs/{job_id}"
        }), 202
        
    except Exception as e:
        current_app.logger.exception(f"Profile scrape: Error starting job for tenant_id={tenant_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            "error": "Failed to start scraping job",
            "details": str(e)
        }), 500


@bp.route('/<profile_id>/scrape', methods=['POST'])
@jwt_required()
def scrape_single_profile(profile_id):
    """
    Scrape a single profile by ID.
    
    Returns job_id immediately (async task).
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        current_app.logger.warning("Profile scrape: Missing tenant_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    current_app.logger.debug(f"Profile scrape: Starting single profile scrape profile_id={profile_id}, tenant_id={tenant_id}")
    
    # Verify profile exists and belongs to tenant
    profile = Profile.query.filter_by(profile_id=profile_id).first()
    if not profile:
        current_app.logger.warning(f"Profile scrape: Profile not found profile_id={profile_id}")
        return jsonify({"error": "Profile not found"}), 404
    
    if profile.tenant_id != tenant_id:
        current_app.logger.warning(f"Profile scrape: Forbidden - profile belongs to different tenant profile_id={profile_id}")
        return jsonify({"error": "Forbidden"}), 403
    
    if profile.status != 'url_only':
        current_app.logger.debug(f"Profile scrape: Profile already scraped profile_id={profile_id}, status={profile.status}")
        return jsonify({
            "message": "Profile already scraped",
            "profile_id": profile_id,
            "status": profile.status
        }), 200
    
    # Import here to avoid circular imports
    from app.tasks.scraper import scrape_profiles
    from app.models.job import Job
    import uuid
    
    try:
        # Create job record
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            tenant_id=tenant_id,
            job_type='profile_scrape',
            status='pending',
            total_items=1
        )
        db.session.add(job)
        db.session.commit()
        
        current_app.logger.debug(f"Profile scrape: Created job_id={job_id} for profile_id={profile_id}")
        
        # Check if Celery is properly configured before starting task
        try:
            from app.tasks.celery_app import celery_app
            # Check if broker is configured
            broker_url = celery_app.conf.broker_url
            if not broker_url or broker_url == 'memory://':
                raise ValueError("Celery broker is not properly configured. Please check Redis connection.")
        except Exception as celery_check_error:
            current_app.logger.error(f"Profile scrape: Celery configuration error: {str(celery_check_error)}")
            job.status = 'failed'
            job.error_message = f"Celery/Redis not configured: {str(celery_check_error)}"
            job.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "error": "Celery/Redis service not available",
                "details": str(celery_check_error),
                "message": "Please ensure Redis is running and CELERY_BROKER_URL is configured"
            }), 503
        
        # Start async Celery task
        try:
            task = scrape_profiles.delay(job_id, tenant_id, profile_ids=[profile_id])
            current_app.logger.info(f"Profile scrape: Started job_id={job_id}, task_id={task.id}, profile_id={profile_id}")
        except Exception as celery_error:
            # Handle Celery connection errors specifically
            error_msg = str(celery_error)
            if 'Redis' in error_msg or 'broker' in error_msg.lower() or 'connection' in error_msg.lower():
                current_app.logger.error(f"Profile scrape: Celery/Redis connection error: {error_msg}")
                job.status = 'failed'
                job.error_message = f"Celery/Redis connection failed: {error_msg}"
                job.completed_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    "error": "Celery/Redis connection failed",
                    "details": error_msg,
                    "message": "Please ensure Redis is running and accessible"
                }), 503
            else:
                # Re-raise other errors to be caught by outer exception handler
                raise
        
        return jsonify({
            "message": "Scraping job started",
            "job_id": job_id,
            "profile_id": profile_id,
            "status_url": f"/api/jobs/{job_id}"
        }), 202
        
    except Exception as e:
        current_app.logger.exception(f"Profile scrape: Error starting job for profile_id={profile_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            "error": "Failed to start scraping job",
            "details": str(e)
        }), 500