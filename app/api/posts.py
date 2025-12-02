"""
API endpoints for LinkedIn posts analysis
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import Schema, fields, validates, ValidationError
from app.extensions import db
from app.models.post import Post
from app.models.company import Company
from app.tasks.ai_analyzer import analyze_post
from datetime import datetime
from sqlalchemy import and_, or_

bp = Blueprint('posts', __name__)


class BatchAnalyzeSchema(Schema):
    post_ids = fields.List(fields.Str(), required=True, error_messages={
        "required": "post_ids is required"
    })
    
    @validates('post_ids')
    def validate_post_ids(self, value):
        if not value or len(value) == 0:
            raise ValidationError("post_ids cannot be empty")
        if len(value) > 100:
            raise ValidationError("Cannot analyze more than 100 posts at once")


batch_analyze_schema = BatchAnalyzeSchema()


@bp.route('', methods=['GET'])
@jwt_required()
def list_posts():
    """
    List scraped LinkedIn posts with filtering, pagination, and sorting.
    
    Query Parameters:
        - company_id (str, optional): Filter by company ID
        - start_date (str, optional): Filter posts from this date (YYYY-MM-DD)
        - end_date (str, optional): Filter posts until this date (YYYY-MM-DD)
        - ai_judgement (str, optional): Filter by AI judgement (e.g., 'product_launch', 'other')
        - page (int, optional): Page number (default: 1)
        - limit (int, optional): Items per page (default: 20, max: 100)
    
    Returns:
        200 OK with posts array containing:
        - post_id: Post unique identifier
        - company_id: Company ID
        - company_name: Company name (from JOIN)
        - post_text: Post content
        - post_date: Post date (YYYY-MM-DD)
        - score: AI score (0-100)
        - ai_judgement: AI judgement category
        - source_url: Original LinkedIn post URL
        - created_at: When post was scraped
        - analyzed_at: When post was analyzed (if analyzed)
    
    Example:
        GET /api/posts?company_id=xxx&page=1&limit=20&ai_judgement=product_launch
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get query parameters
    company_id = request.args.get('company_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    ai_judgement = request.args.get('ai_judgement')
    
    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400
    
    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    
    # Build query with JOIN to companies table
    query = db.session.query(Post, Company.name.label('company_name')).join(
        Company, Post.company_id == Company.company_id
    ).filter(
        Post.tenant_id == tenant_id,
        Company.tenant_id == tenant_id  # Ensure company belongs to tenant
    )
    
    # Apply filters
    if company_id:
        query = query.filter(Post.company_id == company_id)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Post.post_date >= start_dt)
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format"}), 400
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Post.post_date <= end_dt)
        except ValueError:
            return jsonify({"error": "end_date must be in YYYY-MM-DD format"}), 400
    
    if ai_judgement:
        query = query.filter(Post.ai_judgement == ai_judgement)
    
    # Sort by date (newest first)
    query = query.order_by(Post.post_date.desc().nullslast(), Post.created_at.desc())
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Format response
    posts = []
    for post, company_name in results:
        posts.append({
            "post_id": post.post_id,
            "company_id": post.company_id,
            "company_name": company_name,
            "post_text": post.post_text,
            "post_date": post.post_date.isoformat() if post.post_date else None,
            "score": post.score,
            "ai_judgement": post.ai_judgement,
            "source_url": post.source_url,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "analyzed_at": post.analyzed_at.isoformat() if post.analyzed_at else None
        })
    
    # Calculate pagination metadata
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    
    return jsonify({
        "posts": posts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }), 200


@bp.route('/<post_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_single_post(post_id):
    """
    Analyze a single post using Claude AI.
    
    Returns:
        - job_id: Celery task ID for tracking
        - post_id: The post ID being analyzed
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Verify post exists and belongs to tenant
    post = Post.query.filter_by(post_id=post_id, tenant_id=tenant_id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    # Import here to avoid circular imports
    from app.tasks.ai_analyzer import analyze_post
    from app.tasks.celery_app import celery_app
    
    # Check if Celery is properly configured before starting task
    try:
        # Check if broker is configured
        broker_url = celery_app.conf.broker_url
        if not broker_url or broker_url == 'memory://':
            raise ValueError("Celery broker is not properly configured. Please check Redis connection.")
    except Exception as celery_check_error:
        current_app.logger.error(f"Post analyze: Celery configuration error: {str(celery_check_error)}")
        return jsonify({
            "error": "Celery/Redis service not available",
            "details": str(celery_check_error),
            "message": "Please ensure Redis is running and CELERY_BROKER_URL is configured"
        }), 503
    
    # Start async Celery task
    try:
        task = analyze_post.delay(post_id)
        current_app.logger.info(f"Post analyze: Started task_id={task.id}, post_id={post_id}")
        return jsonify({
            "job_id": task.id,
            "post_id": post_id,
            "status": "queued"
        }), 202
    except Exception as celery_error:
        # Handle Celery connection errors specifically
        error_msg = str(celery_error)
        if 'Redis' in error_msg or 'broker' in error_msg.lower() or 'connection' in error_msg.lower():
            current_app.logger.error(f"Post analyze: Celery/Redis connection error: {error_msg}")
            return jsonify({
                "error": "Celery/Redis connection failed",
                "details": error_msg,
                "message": "Please ensure Redis is running and accessible. Check that the Celery worker is also running."
            }), 503
        else:
            # Re-raise other errors
            current_app.logger.exception(f"Post analyze: Unexpected error: {error_msg}")
            return jsonify({
                "error": "Failed to start analysis job",
                "details": error_msg
            }), 500


@bp.route('/analyze-batch', methods=['POST'])
@jwt_required()
def analyze_batch_posts():
    """
    Analyze multiple posts in batch.
    
    Request body:
        {
            "post_ids": ["uuid1", "uuid2", ...]
        }
    
    Returns:
        - job_ids: List of Celery task IDs
        - posts: List of post info with job_id mapping
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    
    try:
        validated = batch_analyze_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400
    
    post_ids = validated['post_ids']
    
    # Verify all posts exist and belong to tenant
    posts = Post.query.filter(
        Post.post_id.in_(post_ids),
        Post.tenant_id == tenant_id
    ).all()
    
    found_post_ids = {post.post_id for post in posts}
    missing_ids = set(post_ids) - found_post_ids
    
    if missing_ids:
        return jsonify({
            "error": "Some posts not found or access denied",
            "missing_post_ids": list(missing_ids)
        }), 404
    
    # Import here to avoid circular imports
    from app.tasks.ai_analyzer import analyze_post
    from app.tasks.celery_app import celery_app
    
    # Check if Celery is properly configured before starting tasks
    try:
        # Check if broker is configured
        broker_url = celery_app.conf.broker_url
        if not broker_url or broker_url == 'memory://':
            raise ValueError("Celery broker is not properly configured. Please check Redis connection.")
    except Exception as celery_check_error:
        current_app.logger.error(f"Post analyze batch: Celery configuration error: {str(celery_check_error)}")
        return jsonify({
            "error": "Celery/Redis service not available",
            "details": str(celery_check_error),
            "message": "Please ensure Redis is running and CELERY_BROKER_URL is configured"
        }), 503
    
    # Queue tasks for all posts
    try:
        job_results = []
        for post_id in post_ids:
            task = analyze_post.delay(post_id)
            job_results.append({
                "post_id": post_id,
                "job_id": task.id
            })
        
        current_app.logger.info(f"Post analyze batch: Started {len(job_results)} tasks")
        return jsonify({
            "job_ids": [j["job_id"] for j in job_results],
            "posts": job_results,
            "count": len(job_results),
            "status": "queued"
        }), 202
    except Exception as celery_error:
        # Handle Celery connection errors specifically
        error_msg = str(celery_error)
        if 'Redis' in error_msg or 'broker' in error_msg.lower() or 'connection' in error_msg.lower():
            current_app.logger.error(f"Post analyze batch: Celery/Redis connection error: {error_msg}")
            return jsonify({
                "error": "Celery/Redis connection failed",
                "details": error_msg,
                "message": "Please ensure Redis is running and accessible. Check that the Celery worker is also running."
            }), 503
        else:
            # Re-raise other errors
            current_app.logger.exception(f"Post analyze batch: Unexpected error: {error_msg}")
            return jsonify({
                "error": "Failed to start analysis jobs",
                "details": error_msg
            }), 500

