"""
Posts API Endpoints

Endpoints for managing and analyzing LinkedIn posts.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import Schema, fields, ValidationError
from app.extensions import db
from app.models.post import Post
from app.tasks.ai_analyzer import analyze_post
from app.tasks.celery_app import celery_app

bp = Blueprint('posts', __name__)
logger = logging.getLogger(__name__)


class BatchAnalyzeSchema(Schema):
    post_ids = fields.List(fields.Str(), required=True, error_messages={
        "required": "post_ids is required"
    })


batch_analyze_schema = BatchAnalyzeSchema()


@bp.route('/analyze-batch', methods=['POST'])
@jwt_required()
def analyze_batch_posts():
    """
    Batch analyze multiple posts using Claude AI.
    
    Request Body:
        {
            "post_ids": ["uuid1", "uuid2", ...]
        }
    
    Flow:
    1. Validate request body
    2. Verify all posts exist and belong to tenant
    3. Queue Celery tasks for each post
    4. Return job_ids
    
    Returns:
        202: Batch analysis jobs queued
        400: Validation error
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
    
    if not post_ids:
        return jsonify({"error": "post_ids cannot be empty"}), 400
    
    # Verify all posts exist and belong to tenant
    posts = Post.query.filter(
        Post.post_id.in_(post_ids),
        Post.tenant_id == tenant_id
    ).all()
    
    found_post_ids = {post.post_id for post in posts}
    missing_post_ids = set(post_ids) - found_post_ids
    
    if missing_post_ids:
        return jsonify({
            "error": "Some posts not found or access denied",
            "missing_post_ids": list(missing_post_ids)
        }), 404
    
    # Queue Celery tasks for each post
    job_ids = []
    for post_id in post_ids:
        try:
            task = analyze_post.delay(post_id)
            job_ids.append({
                "post_id": post_id,
                "job_id": task.id
            })
        except Exception as e:
            logger.error(f"Failed to queue analysis for post {post_id}: {str(e)}")
            job_ids.append({
                "post_id": post_id,
                "job_id": None,
                "error": str(e)
            })
    
    return jsonify({
        "message": "Batch analysis jobs queued",
        "total": len(post_ids),
        "queued": len([j for j in job_ids if j.get('job_id')]),
        "failed": len([j for j in job_ids if not j.get('job_id')]),
        "jobs": job_ids
    }), 202


@bp.route('/analyze-batch/status/<job_id>', methods=['GET'])
@jwt_required()
def get_batch_analyze_status(job_id: str):
    """
    Get status of batch analysis jobs.
    Note: This checks the status of individual jobs in the batch.
    For a complete batch status, you need to check each job_id from the batch response.
    
    Returns:
        200: Job status
        404: Job not found
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get task result
    try:
        task = celery_app.AsyncResult(job_id)
        
        if task.state == 'PENDING':
            response = {
                "job_id": job_id,
                "status": "pending",
                "message": "Job is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            response = {
                "job_id": job_id,
                "status": "processing",
                "message": "Job is being processed",
                "progress": task.info.get('progress', {}) if isinstance(task.info, dict) else {}
            }
        elif task.state == 'SUCCESS':
            result = task.result
            response = {
                "job_id": job_id,
                "status": "completed",
                "message": result.get('message', 'Analysis completed'),
                "result": result
            }
        elif task.state == 'FAILURE':
            response = {
                "job_id": job_id,
                "status": "failed",
                "message": str(task.info) if task.info else "Job failed",
                "error": str(task.info) if task.info else "Unknown error"
            }
        else:
            response = {
                "job_id": job_id,
                "status": task.state.lower(),
                "message": f"Job state: {task.state}"
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting batch job status: {str(e)}")
        return jsonify({
            "error": "Failed to get job status",
            "details": str(e)
        }), 500


@bp.route('/<post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id: str):
    """
    Get a single post with analysis results.
    
    Returns:
        200: Post data with analysis results
        404: Post not found
        403: Post belongs to different tenant
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get post
    post = Post.query.filter_by(post_id=post_id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post.tenant_id != tenant_id:
        return jsonify({"error": "Forbidden"}), 403
    
    # Return post data with analysis results
    return jsonify({
        "post": {
            "post_id": post.post_id,
            "company_id": post.company_id,
            "source_url": post.source_url,
            "post_text": post.post_text,
            "post_date": post.post_date.isoformat() if post.post_date else None,
            "score": post.score,
            "ai_judgement": post.ai_judgement,
            "analyzed_at": post.analyzed_at.isoformat() if post.analyzed_at else None,
            "created_at": post.created_at.isoformat() if post.created_at else None
        }
    }), 200


@bp.route('/<post_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_single_post(post_id: str):
    """
    Analyze a single post using Claude AI.
    
    Flow:
    1. Verify post exists and belongs to tenant
    2. Queue Celery task for analysis
    3. Return job_id (async)
    
    Returns:
        202: Analysis job queued with job_id
        404: Post not found
        403: Post belongs to different tenant
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Verify post exists and belongs to tenant
    post = Post.query.filter_by(post_id=post_id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post.tenant_id != tenant_id:
        return jsonify({"error": "Forbidden"}), 403
    
    # Queue Celery task for analysis
    try:
        task = analyze_post.delay(post_id)
        return jsonify({
            "message": "Analysis job queued",
            "job_id": task.id,
            "post_id": post_id,
            "status_url": f"/api/posts/{post_id}/analyze/status/{task.id}"
        }), 202
    except Exception as e:
        logger.error(f"Failed to queue analysis task: {str(e)}")
        return jsonify({
            "error": "Failed to queue analysis job",
            "details": str(e)
        }), 500


@bp.route('/<post_id>/analyze/status/<job_id>', methods=['GET'])
@jwt_required()
def get_analyze_status(post_id: str, job_id: str):
    """
    Get status of a single post analysis job.
    
    Returns:
        200: Job status with result if completed
        404: Job not found
        403: Post belongs to different tenant
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Verify post exists and belongs to tenant
    post = Post.query.filter_by(post_id=post_id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post.tenant_id != tenant_id:
        return jsonify({"error": "Forbidden"}), 403
    
    # Get task result
    try:
        task = celery_app.AsyncResult(job_id)
        
        if task.state == 'PENDING':
            response = {
                "job_id": job_id,
                "post_id": post_id,
                "status": "pending",
                "message": "Job is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            response = {
                "job_id": job_id,
                "post_id": post_id,
                "status": "processing",
                "message": "Job is being processed",
                "progress": task.info.get('progress', {}) if isinstance(task.info, dict) else {}
            }
        elif task.state == 'SUCCESS':
            result = task.result
            response = {
                "job_id": job_id,
                "post_id": post_id,
                "status": "completed",
                "message": result.get('message', 'Analysis completed'),
                "result": {
                    "score": result.get('score'),
                    "judgement": result.get('judgement')
                }
            }
        elif task.state == 'FAILURE':
            response = {
                "job_id": job_id,
                "post_id": post_id,
                "status": "failed",
                "message": str(task.info) if task.info else "Job failed",
                "error": str(task.info) if task.info else "Unknown error"
            }
        else:
            response = {
                "job_id": job_id,
                "post_id": post_id,
                "status": task.state.lower(),
                "message": f"Job state: {task.state}"
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({
            "error": "Failed to get job status",
            "details": str(e)
        }), 500

