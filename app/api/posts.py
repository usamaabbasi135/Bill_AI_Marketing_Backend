from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.post import Post
from app.models.company import Company
from datetime import datetime

bp = Blueprint('posts', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def list_posts():
    """List scraped LinkedIn posts for the current tenant with filtering and pagination.

    Query Params:
      - page: int (default 1)
      - limit: int (default 20, max 100)
      - company_id: str (optional) - filter by company
      - start_date: str (optional) - filter posts from this date (YYYY-MM-DD)
      - ai_judgement: str (optional) - filter by AI judgement (e.g., "product_launch")
    
    Returns:
      - post_id, company_name, post_text, post_date, score, ai_judgement
      - Sorted by post_date DESC (newest first)
    """

    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Pagination params
    try:
        page = int((request.args.get('page') or '1').strip())
    except Exception:
        page = 1
    if page < 1:
        page = 1

    try:
        limit = int((request.args.get('limit') or '20').strip())
    except Exception:
        limit = 20
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100

    # Build query with JOIN to companies table
    query = db.session.query(Post, Company.name).join(
        Company, Post.company_id == Company.company_id
    ).filter(
        Post.tenant_id == tenant_id,
        Company.tenant_id == tenant_id
    )

    # Filter by company_id
    company_id = request.args.get('company_id')
    if company_id:
        query = query.filter(Post.company_id == company_id.strip())

    # Filter by start_date
    start_date = request.args.get('start_date')
    if start_date:
        try:
            date_obj = datetime.strptime(start_date.strip(), '%Y-%m-%d').date()
            query = query.filter(Post.post_date >= date_obj)
        except ValueError:
            # Invalid date format, ignore filter
            pass

    # Filter by ai_judgement
    ai_judgement = request.args.get('ai_judgement')
    if ai_judgement:
        query = query.filter(Post.ai_judgement == ai_judgement.strip())

    # Get total count before pagination
    total = query.count()

    # Sort by post_date DESC (newest first) and apply pagination
    items = (
        query
        .order_by(Post.post_date.desc(), Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    # Format response
    posts = []
    for post, company_name in items:
        posts.append({
            "post_id": post.post_id,
            "company_name": company_name,
            "post_text": post.post_text,
            "post_date": post.post_date.isoformat() if post.post_date else None,
            "score": post.score,
            "ai_judgement": post.ai_judgement,
        })

    return jsonify({
        "posts": posts,
        "page": page,
        "limit": limit,
        "total": total
    }), 200

