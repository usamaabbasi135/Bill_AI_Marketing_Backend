from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.company import Company
from app.models.post import Post

bp = Blueprint('dashboard', __name__)


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """
    Dashboard Statistics Endpoint
    
    Returns aggregated statistics for the current tenant:
    - Total companies tracked
    - Total posts scraped
    - Product launches detected (ai_judgement='product_launch')
    - Recent activity (last 7 days)
    - Top scoring posts
    
    Requires JWT authentication and filters by tenant_id.
    """
    try:
        # Extract tenant_id from JWT token
        claims = get_jwt()
        tenant_id = claims.get('tenant_id')
        
        if not tenant_id:
            current_app.logger.warning(
                "Dashboard: Missing tenant_id in JWT token"
            )
            return jsonify({"error": "Unauthorized"}), 401
        
        current_app.logger.debug(
            "Dashboard: Fetching stats for tenant_id=%s",
            tenant_id
        )
        
        # Calculate date 7 days ago for recent activity
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # 1. Total companies tracked (only active companies)
        total_companies = Company.query.filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).count()
        
        current_app.logger.debug(
            "Dashboard: Total companies for tenant_id=%s: %d",
            tenant_id,
            total_companies
        )
        
        # 2. Total posts scraped
        total_posts = Post.query.filter_by(tenant_id=tenant_id).count()
        
        current_app.logger.debug(
            "Dashboard: Total posts for tenant_id=%s: %d",
            tenant_id,
            total_posts
        )
        
        # 3. Product launches detected (ai_judgement='product_launch')
        product_launches = Post.query.filter_by(
            tenant_id=tenant_id,
            ai_judgement='product_launch'
        ).count()
        
        current_app.logger.debug(
            "Dashboard: Product launches for tenant_id=%s: %d",
            tenant_id,
            product_launches
        )
        
        # 4. Recent activity (posts created in last 7 days)
        recent_activity = Post.query.filter(
            Post.tenant_id == tenant_id,
            Post.created_at >= seven_days_ago
        ).count()
        
        current_app.logger.debug(
            "Dashboard: Recent activity (7 days) for tenant_id=%s: %d",
            tenant_id,
            recent_activity
        )
        
        # 5. Top scoring posts (top 5 posts ordered by score DESC)
        top_posts = (
            Post.query
            .filter_by(tenant_id=tenant_id)
            .order_by(Post.score.desc())
            .limit(5)
            .all()
        )
        
        top_posts_data = []
        for post in top_posts:
            top_posts_data.append({
                "post_id": post.post_id,
                "company_id": post.company_id,
                "source_url": post.source_url,
                "score": post.score,
                "ai_judgement": post.ai_judgement,
                "post_date": post.post_date.isoformat() if post.post_date else None,
                "created_at": post.created_at.isoformat() if post.created_at else None,
            })
        
        current_app.logger.debug(
            "Dashboard: Top posts retrieved for tenant_id=%s: %d posts",
            tenant_id,
            len(top_posts_data)
        )
        
        # Compile response
        stats = {
            "total_companies": total_companies,
            "total_posts": total_posts,
            "product_launches": product_launches,
            "recent_activity": recent_activity,
            "top_scoring_posts": top_posts_data
        }
        
        current_app.logger.info(
            "Dashboard: Stats successfully retrieved for tenant_id=%s",
            tenant_id
        )
        
        return jsonify({"stats": stats}), 200
        
    except Exception as exc:
        current_app.logger.exception(
            "Dashboard: Error fetching stats for tenant_id=%s: %s",
            tenant_id if 'tenant_id' in locals() else 'unknown',
            exc
        )
        return jsonify({"error": "Unable to fetch dashboard statistics"}), 500

