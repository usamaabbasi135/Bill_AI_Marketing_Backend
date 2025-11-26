"""
Celery tasks for sending emails via AWS SES.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any

from app.tasks.celery_app import celery_app
from app.extensions import db
from app.models.email import Email
from app.models.profile import Profile
from app.models.campaign import Campaign, CampaignProfile
from app.services.email_sender import send_email_via_ses, is_transient_error

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_single_email_task(self, email_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Send a single email via AWS SES.
    
    Args:
        email_id: Email record ID
        tenant_id: Tenant ID for validation
    
    Returns:
        Dict with success status and message_id or error details
    """
    email = Email.query.filter_by(email_id=email_id, tenant_id=tenant_id).first()
    
    if not email:
        logger.error("Email not found for sending", extra={"email_id": email_id, "tenant_id": tenant_id})
        return {"success": False, "error": "Email not found"}
    
    # Validate email status
    if email.status != 'draft':
        error_msg = f"Cannot send email with status '{email.status}'. Only 'draft' emails can be sent."
        logger.warning("Attempted to send non-draft email", extra={"email_id": email_id, "status": email.status})
        email.status = 'failed'
        email.error_message = error_msg
        db.session.commit()
        return {"success": False, "error": error_msg}
    
    # Get recipient email from profile
    if not email.profile_id:
        error_msg = "Email has no associated profile"
        logger.error("Email missing profile", extra={"email_id": email_id})
        email.status = 'failed'
        email.error_message = error_msg
        db.session.commit()
        return {"success": False, "error": error_msg}
    
    profile = Profile.query.filter_by(profile_id=email.profile_id, tenant_id=tenant_id).first()
    if not profile:
        error_msg = "Profile not found"
        logger.error("Profile not found for email", extra={"email_id": email_id, "profile_id": email.profile_id})
        email.status = 'failed'
        email.error_message = error_msg
        db.session.commit()
        return {"success": False, "error": error_msg}
    
    if not profile.email or not profile.email.strip():
        error_msg = "Recipient email not found"
        logger.warning("Profile has no email address", extra={"email_id": email_id, "profile_id": email.profile_id})
        email.status = 'failed'
        email.error_message = error_msg
        db.session.commit()
        return {"success": False, "error": error_msg}
    
    # Send email via SES
    try:
        result = send_email_via_ses(
            recipient_email=profile.email,
            subject=email.subject,
            body=email.body
        )
        
        # Update email record
        email.status = 'sent'
        email.message_id = result['message_id']
        email.sent_at = datetime.utcnow()
        email.error_message = None
        db.session.commit()
        
        logger.info("Email sent successfully", extra={
            "email_id": email_id,
            "message_id": result['message_id'],
            "recipient": profile.email
        })
        
        # Update campaign profile if linked
        campaign_profile = CampaignProfile.query.filter_by(email_id=email_id).first()
        if campaign_profile:
            campaign_profile.status = 'email_sent'
            db.session.commit()
        
        return {
            "success": True,
            "message_id": result['message_id'],
            "sent_at": email.sent_at.isoformat()
        }
        
    except ValueError as e:
        # Validation errors - don't retry
        error_msg = str(e)
        logger.error("Email sending validation error", extra={"email_id": email_id, "error": error_msg})
        email.status = 'failed'
        email.error_message = error_msg
        email.sent_at = datetime.utcnow()
        db.session.commit()
        
        # Update campaign profile
        campaign_profile = CampaignProfile.query.filter_by(email_id=email_id).first()
        if campaign_profile:
            campaign_profile.status = 'email_failed'
            db.session.commit()
        
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        # Check if this is a transient error that should be retried
        if is_transient_error(e) and self.request.retries < self.max_retries:
            logger.warning("Transient error sending email, will retry", extra={
                "email_id": email_id,
                "retry": self.request.retries + 1,
                "error": str(e)
            })
            raise  # Let Celery retry
        
        # Permanent error - mark as failed
        error_msg = str(e)
        logger.error("Failed to send email", extra={"email_id": email_id, "error": error_msg})
        email.status = 'failed'
        email.error_message = error_msg
        email.sent_at = datetime.utcnow()
        db.session.commit()
        
        # Update campaign profile
        campaign_profile = CampaignProfile.query.filter_by(email_id=email_id).first()
        if campaign_profile:
            campaign_profile.status = 'email_failed'
            db.session.commit()
        
        return {"success": False, "error": error_msg}


@celery_app.task(bind=True)
def send_campaign_emails_task(self, campaign_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Send all draft emails in a campaign via AWS SES.
    
    Args:
        campaign_id: Campaign ID
        tenant_id: Tenant ID for validation
    
    Returns:
        Dict with total, sent, failed counts and failed email details
    """
    campaign = Campaign.query.filter_by(campaign_id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        logger.error("Campaign not found for sending", extra={"campaign_id": campaign_id, "tenant_id": tenant_id})
        return {"total": 0, "sent": 0, "failed": 0, "failed_emails": []}
    
    # Find all emails in campaign with status='draft'
    campaign_profiles = CampaignProfile.query.filter_by(
        campaign_id=campaign_id
    ).filter(
        CampaignProfile.email_id.isnot(None)
    ).all()
    
    email_ids = [cp.email_id for cp in campaign_profiles if cp.email_id]
    
    if not email_ids:
        logger.info("No emails found in campaign", extra={"campaign_id": campaign_id})
        return {"total": 0, "sent": 0, "failed": 0, "failed_emails": []}
    
    # Get draft emails
    emails = Email.query.filter(
        Email.email_id.in_(email_ids),
        Email.tenant_id == tenant_id,
        Email.status == 'draft'
    ).all()
    
    total = len(emails)
    sent = 0
    failed = 0
    failed_emails: List[Dict[str, Any]] = []
    
    logger.info("Starting campaign email sending", extra={
        "campaign_id": campaign_id,
        "total_emails": total
    })
    
    for email in emails:
        try:
            # Get recipient email
            if not email.profile_id:
                failed += 1
                failed_emails.append({
                    "email_id": email.email_id,
                    "recipient": None,
                    "error": "Email has no associated profile"
                })
                email.status = 'failed'
                email.error_message = "Email has no associated profile"
                db.session.commit()
                continue
            
            profile = Profile.query.filter_by(profile_id=email.profile_id).first()
            if not profile or not profile.email or not profile.email.strip():
                failed += 1
                failed_emails.append({
                    "email_id": email.email_id,
                    "recipient": profile.email if profile else None,
                    "error": "Recipient email not found"
                })
                email.status = 'failed'
                email.error_message = "Recipient email not found"
                db.session.commit()
                
                # Update campaign profile
                campaign_profile = CampaignProfile.query.filter_by(
                    campaign_id=campaign_id,
                    email_id=email.email_id
                ).first()
                if campaign_profile:
                    campaign_profile.status = 'email_failed'
                    db.session.commit()
                continue
            
            # Send email
            result = send_email_via_ses(
                recipient_email=profile.email,
                subject=email.subject,
                body=email.body
            )
            
            # Update email record
            email.status = 'sent'
            email.message_id = result['message_id']
            email.sent_at = datetime.utcnow()
            email.error_message = None
            db.session.commit()
            
            # Update campaign profile
            campaign_profile = CampaignProfile.query.filter_by(
                campaign_id=campaign_id,
                email_id=email.email_id
            ).first()
            if campaign_profile:
                campaign_profile.status = 'email_sent'
                db.session.commit()
            
            sent += 1
            logger.info("Campaign email sent", extra={
                "campaign_id": campaign_id,
                "email_id": email.email_id,
                "message_id": result['message_id']
            })
            
        except ValueError as e:
            # Validation errors
            failed += 1
            error_msg = str(e)
            failed_emails.append({
                "email_id": email.email_id,
                "recipient": profile.email if profile else None,
                "error": error_msg
            })
            email.status = 'failed'
            email.error_message = error_msg
            email.sent_at = datetime.utcnow()
            db.session.commit()
            
            # Update campaign profile
            campaign_profile = CampaignProfile.query.filter_by(
                campaign_id=campaign_id,
                email_id=email.email_id
            ).first()
            if campaign_profile:
                campaign_profile.status = 'email_failed'
                db.session.commit()
            
            logger.warning("Campaign email failed (validation)", extra={
                "campaign_id": campaign_id,
                "email_id": email.email_id,
                "error": error_msg
            })
            
        except Exception as e:
            # Other errors
            failed += 1
            error_msg = str(e)
            failed_emails.append({
                "email_id": email.email_id,
                "recipient": profile.email if profile else None,
                "error": error_msg
            })
            email.status = 'failed'
            email.error_message = error_msg
            email.sent_at = datetime.utcnow()
            db.session.commit()
            
            # Update campaign profile
            campaign_profile = CampaignProfile.query.filter_by(
                campaign_id=campaign_id,
                email_id=email.email_id
            ).first()
            if campaign_profile:
                campaign_profile.status = 'email_failed'
                db.session.commit()
            
            logger.error("Campaign email failed", extra={
                "campaign_id": campaign_id,
                "email_id": email.email_id,
                "error": error_msg
            })
    
    logger.info("Campaign email sending completed", extra={
        "campaign_id": campaign_id,
        "total": total,
        "sent": sent,
        "failed": failed
    })
    
    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "failed_emails": failed_emails
    }

