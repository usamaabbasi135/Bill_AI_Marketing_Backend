from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import Schema, fields, validates, ValidationError
from app.extensions import db
from app.models.email import Email
from app.models.email_template import EmailTemplate
from app.models.post import Post
from app.models.profile import Profile
from app.models.user import User
from app.models.campaign import Campaign, CampaignProfile
from app.services.email_generation import generate_email_record
import uuid

bp = Blueprint('emails', __name__)


class GenerateEmailSchema(Schema):
    post_id = fields.Str(required=True, error_messages={"required": "post_id is required"})
    profile_id = fields.Str(required=True, error_messages={"required": "profile_id is required"})
    template_id = fields.Str(required=True, error_messages={"required": "template_id is required"})


generate_email_schema = GenerateEmailSchema()


def email_to_dict(email):
    """Convert Email model to dictionary."""
    return {
        "email_id": email.email_id,
        "post_id": email.post_id,
        "profile_id": email.profile_id,
        "subject": email.subject,
        "body": email.body,
        "status": email.status,
        "created_at": email.created_at.isoformat() if email.created_at else None
    }


@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_email():
    """
    Generate a single personalized email using Claude API.
    
    Request Body:
        {
            "post_id": "post-uuid",
            "profile_id": "profile-uuid",
            "template_id": "template-uuid"
        }
    """
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    if not tenant_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user_id).first()
    sender_name = user.first_name or "Team" if user else "Team"
    
    data = request.get_json() or {}
    
    try:
        validated = generate_email_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400
    
    post_id = validated['post_id']
    profile_id = validated['profile_id']
    template_id = validated['template_id']
    
    # Validate post exists and belongs to tenant
    post = Post.query.filter_by(post_id=post_id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post.tenant_id != tenant_id:
        return jsonify({"error": "Post does not belong to your tenant"}), 403
    
    # Validate profile exists and belongs to tenant
    profile = Profile.query.filter_by(profile_id=profile_id).first()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    if profile.tenant_id != tenant_id:
        return jsonify({"error": "Profile does not belong to your tenant"}), 403
    
    # Validate template exists and belongs to tenant (or is default)
    template = EmailTemplate.query.filter(
        EmailTemplate.template_id == template_id,
        (EmailTemplate.tenant_id == tenant_id) | (EmailTemplate.is_default == True)
    ).first()
    
    if not template:
        return jsonify({"error": "Template not found"}), 404
    
    # Check if profile is in a campaign
    campaign_profile = CampaignProfile.query.filter_by(profile_id=profile_id).first()
    campaign_id = campaign_profile.campaign_id if campaign_profile else None
    
    try:
        # Generate email using Claude
        email = generate_email_record(
            tenant_id=tenant_id,
            post=post,
            profile=profile,
            template=template,
            sender_name=sender_name,
            campaign_id=campaign_id
        )
        
        return jsonify({"email": email_to_dict(email)}), 201
        
    except Exception as e:
        return jsonify({"error": "Failed to generate email", "details": str(e)}), 500



