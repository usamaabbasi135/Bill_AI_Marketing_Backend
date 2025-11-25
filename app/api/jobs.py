from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.job import Job

bp = Blueprint('jobs', __name__)


@bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_job_status(job_id):
    """
    Get job status by job_id.
    
    Returns job status, progress, and results.
    Supports both old Job model (task_name, result, error) and new Job model (job_type, progress, etc.)
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    
    if not tenant_id:
        current_app.logger.warning("Job status: Missing tenant_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    current_app.logger.debug(f"Job status: Fetching job_id={job_id} for tenant_id={tenant_id}")
    
    # Get job from database with tenant filter for security (optimized query)
    job = Job.query.filter_by(job_id=job_id, tenant_id=tenant_id).first()
    
    if not job:
        current_app.logger.warning(f"Job status: Job not found or access denied job_id={job_id}")
        return jsonify({"error": "Job not found"}), 404
    
    current_app.logger.debug(f"Job status: Found job_id={job_id}, status={job.status}")
    
    # Check if it's the new Job model (has to_dict method) or old model
    if hasattr(job, 'to_dict'):
        # New Job model with progress tracking
        return jsonify({"job": job.to_dict()}), 200
    else:
        # Old Job model - return basic structure
        response = {
            "job_id": job.job_id,
            "task_name": getattr(job, 'task_name', None),
            "status": job.status,
            "result": getattr(job, 'result', None),
            "error": getattr(job, 'error', None),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
        return jsonify({"job": response}), 200
