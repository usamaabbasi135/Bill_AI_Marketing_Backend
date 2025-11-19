"""
API endpoints for LinkedIn posts analysis
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import Schema, fields, validates, ValidationError
from app.extensions import db
from app.models.post import Post
from app.tasks.ai_analyzer import analyze_post

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
    
    # Queue Celery task
    task = analyze_post.delay(post_id)
    
    return jsonify({
        "job_id": task.id,
        "post_id": post_id,
        "status": "queued"
    }), 202


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
    
    # Queue tasks for all posts
    job_results = []
    for post_id in post_ids:
        task = analyze_post.delay(post_id)
        job_results.append({
            "post_id": post_id,
            "job_id": task.id
        })
    
    return jsonify({
        "job_ids": [j["job_id"] for j in job_results],
        "posts": job_results,
        "count": len(job_results),
        "status": "queued"
    }), 202

