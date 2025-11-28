"""
AWS SES Email Sender Service

Handles sending emails via AWS Simple Email Service (SES).
"""
import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import Config

logger = logging.getLogger(__name__)

# Global SES client (initialized on first use)
_ses_client = None


def get_ses_client():
    """Get or create AWS SES client."""
    global _ses_client
    
    if _ses_client is not None:
        return _ses_client
    
    # Validate AWS credentials
    if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in environment.")
    
    if not Config.SES_SENDER_EMAIL:
        raise ValueError("SES sender email not configured. Set SES_SENDER_EMAIL in environment.")
    
    try:
        _ses_client = boto3.client(
            'ses',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        
        # Verify SES client can connect
        _ses_client.get_send_quota()
        logger.info("AWS SES client initialized successfully", extra={"region": Config.AWS_REGION, "sender": Config.SES_SENDER_EMAIL})
        
        return _ses_client
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to initialize AWS SES client", extra={"error": str(e)})
        raise ValueError(f"AWS SES configuration error: {str(e)}")


def send_email_via_ses(
    recipient_email: str,
    subject: str,
    body: str,
    sender_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email via AWS SES.
    
    Args:
        recipient_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        sender_email: Sender email (defaults to SES_SENDER_EMAIL from config)
    
    Returns:
        Dict with 'message_id' and 'success' keys
    
    Raises:
        ValueError: If recipient email is invalid or SES is misconfigured
        ClientError: If SES API call fails
    """
    if not recipient_email or not recipient_email.strip():
        raise ValueError("Recipient email is required")
    
    if not subject or not subject.strip():
        raise ValueError("Email subject is required")
    
    if not body or not body.strip():
        raise ValueError("Email body is required")
    
    sender = sender_email or Config.SES_SENDER_EMAIL
    if not sender:
        raise ValueError("Sender email not configured")
    
    try:
        ses_client = get_ses_client()
        
        # Send email via SES
        response = ses_client.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [recipient_email.strip()]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        message_id = response.get('MessageId')
        logger.info("Email sent successfully via SES", extra={
            "message_id": message_id,
            "recipient": recipient_email,
            "sender": sender
        })
        
        return {
            'success': True,
            'message_id': message_id,
            'response': response
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        # Handle specific SES errors
        if error_code == 'MessageRejected':
            logger.warning("Email rejected by SES", extra={
                "recipient": recipient_email,
                "error": error_message
            })
            raise ValueError(f"Email rejected: {error_message}")
        elif error_code == 'MailFromDomainNotVerified':
            raise ValueError("Sender domain not verified in SES")
        elif error_code == 'ConfigurationSetDoesNotExist':
            raise ValueError("SES configuration set does not exist")
        else:
            logger.error("SES API error", extra={
                "error_code": error_code,
                "error_message": error_message,
                "recipient": recipient_email
            })
            raise ValueError(f"AWS SES error ({error_code}): {error_message}")
    
    except BotoCoreError as e:
        logger.error("Boto3 core error", extra={"error": str(e), "recipient": recipient_email})
        raise ValueError(f"AWS connection error: {str(e)}")
    
    except Exception as e:
        logger.exception("Unexpected error sending email", extra={"recipient": recipient_email, "error": str(e)})
        raise ValueError(f"Failed to send email: {str(e)}")


def is_rate_limit_error(error: Exception) -> bool:
    """Check if error is a rate limit error that should be retried."""
    if isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', '')
        return error_code in ['Throttling', 'ServiceUnavailable', 'TooManyRequests']
    return False


def is_transient_error(error: Exception) -> bool:
    """Check if error is transient and should be retried."""
    if isinstance(error, (BotoCoreError, ClientError)):
        error_code = getattr(error, 'response', {}).get('Error', {}).get('Code', '') if hasattr(error, 'response') else ''
        return error_code in ['Throttling', 'ServiceUnavailable', 'TooManyRequests', 'RequestTimeout']
    return False

