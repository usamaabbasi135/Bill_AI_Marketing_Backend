from datetime import datetime

from celery import Celery
from celery.result import AsyncResult
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.job import Job

bp = Blueprint('jobs', __name__)

_celery_client = None


def _get_celery_client():
    global _celery_client

    if _celery_client is not None:
        return _celery_client

    broker_url = current_app.config.get('CELERY_BROKER_URL')
    backend_url = current_app.config.get('CELERY_RESULT_BACKEND')

    if not broker_url or not backend_url:
        current_app.logger.error(
            "Jobs: Celery configuration missing (broker=%s, backend=%s)",
            broker_url,
            backend_url,
        )
        raise RuntimeError("Celery configuration missing")

    _celery_client = Celery('job_status_client', broker=broker_url, backend=backend_url)
    current_app.logger.debug(
        "Jobs: Initialized Celery client with broker=%s backend=%s",
        broker_url,
        backend_url,
    )
    return _celery_client


def _normalize_state(state: str) -> str:
    if not state:
        return 'pending'

    normalized = state.lower()
    if normalized == 'success':
        return 'completed'
    if normalized in {'failure', 'failed', 'revoked'}:
        return 'failed'
    if normalized in {'started', 'running', 'progress'}:
        return 'processing'
    return 'pending'


def _safe_result_payload(result):
    if result is None:
        return None

    try:
        # Attempt JSON-serializable structures first
        from flask import json

        json.dumps(result)
        return result
    except Exception:
        return str(result)


@bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_job_status(job_id):
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')

    if not tenant_id:
        current_app.logger.warning(
            "Jobs: Missing tenant_id in JWT for job_id=%s",
            job_id,
        )
        return jsonify({"error": "Unauthorized"}), 401

    job = Job.query.filter_by(job_id=job_id).first()
    if not job:
        current_app.logger.debug(
            "Jobs: Job not found job_id=%s tenant_id=%s",
            job_id,
            tenant_id,
        )
        return jsonify({"error": "Job not found"}), 404

    if job.tenant_id != tenant_id:
        current_app.logger.warning(
            "Jobs: Forbidden access job_id=%s tenant_id=%s owner_id=%s",
            job_id,
            tenant_id,
            job.tenant_id,
        )
        return jsonify({"error": "Forbidden"}), 403

    try:
        celery_client = _get_celery_client()
        async_result = AsyncResult(job_id, app=celery_client)
        celery_state = async_result.state or 'PENDING'
        status = _normalize_state(celery_state)

        result_payload = None
        error_payload = None

        if status == 'completed':
            result_payload = _safe_result_payload(async_result.result)
        elif status == 'failed':
            error_payload = _safe_result_payload(async_result.result) or "Task failed"

        # Fall back to stored values when Celery backend has no data
        if result_payload is None:
            result_payload = job.result
        if error_payload is None:
            error_payload = job.error

        job.status = status
        job.result = result_payload
        job.error = error_payload
        job.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.debug(
            "Jobs: Status fetched job_id=%s status=%s",
            job_id,
            status,
        )

        response = {
            "job_id": job.job_id,
            "task_name": job.task_name,
            "status": status,
            "result": result_payload,
            "error": error_payload,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
        return jsonify({"job": response}), 200
    except RuntimeError as config_error:
        current_app.logger.exception(
            "Jobs: Celery misconfiguration job_id=%s error=%s",
            job_id,
            config_error,
        )
        return jsonify({"error": "Celery is not configured"}), 500
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception(
            "Jobs: Failed to fetch status job_id=%s error=%s",
            job_id,
            exc,
        )
        return jsonify({"error": "Unable to fetch job status"}), 500

