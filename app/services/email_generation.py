"""
Email Generation Service - Uses Claude API to generate personalized emails
"""
import logging
import time
from typing import Optional, Dict
from anthropic import Anthropic
from app.extensions import db
from app.models.email import Email
from app.models.email_template import EmailTemplate
from app.models.post import Post
from app.models.profile import Profile
from app.models.company import Company
from app.models.campaign import CampaignProfile

logger = logging.getLogger(__name__)


def extract_first_name(full_name: Optional[str]) -> str:
    """Extract first name from full name."""
    if not full_name:
        return "there"
    return full_name.split()[0] if full_name.split() else "there"


def build_claude_prompt(post: Post, profile: Profile, template: EmailTemplate, sender_name: str) -> str:
    """
    Build the prompt for Claude API to generate personalized email.
    """
    company_name = post.company.name if post.company else "the company"
    post_text = post.post_text or ""
    recipient_name = extract_first_name(profile.person_name)
    headline = profile.headline or ""
    
    prompt = f"""You are an AI assistant helping to generate personalized outreach emails for B2B sales.

Given:
- LinkedIn Post: {post_text}
- Recipient: {profile.person_name or 'Recipient'} ({headline})
- Company: {company_name}
- Template Structure:
  Subject: {template.subject}
  Body: {template.body}

Your tasks:
1. Extract the product name from the post text
2. Generate a 2-3 sentence summary of the post that highlights the key product/launch
3. Personalize the message based on the recipient's role/headline if relevant
4. Fill in all template placeholders with appropriate values

Template placeholders to fill:
- {{recipient_name}} → Use first name only: {recipient_name}
- {{company_name}} → {company_name}
- {{product_name}} → Extract from post
- {{sender_name}} → {sender_name}
- {{post_summary}} → Generate 2-3 sentences about the launch/product

Output format (JSON):
{{
  "product_name": "extracted product name",
  "post_summary": "2-3 sentence personalized summary",
  "subject": "final subject with all placeholders replaced",
  "body": "final body with all placeholders replaced"
}}

Make the email:
- Professional but friendly
- Personalized to the recipient's role when possible
- Focused on the product launch/announcement
- Natural and conversational
- 2-3 sentences for post_summary

Generate the email now:"""

    return prompt


def call_claude_api(prompt: str, max_retries: int = 3) -> Dict:
    """
    Call Claude API with retry logic for timeouts and rate limits.
    """
    from app.config import Config
    import os
    import json
    
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not set in environment")
    
    client = Anthropic(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract text from response
            content = response.content[0].text if response.content else ""
            
            # Parse JSON from Claude's response
            # Claude might wrap JSON in markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            result = json.loads(content)
            
            # Log token usage
            logger.info("Claude API call successful", extra={
                "input_tokens": getattr(response, 'usage', {}).get('input_tokens', 0),
                "output_tokens": getattr(response, 'usage', {}).get('output_tokens', 0),
                "attempt": attempt + 1
            })
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Claude API call failed (attempt {attempt + 1}/{max_retries})", extra={
                "error": error_msg,
                "attempt": attempt + 1
            })
            
            # Check for rate limit
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.info(f"Rate limit hit, waiting {wait_time} seconds")
                time.sleep(wait_time)
                continue
            
            # Check for timeout
            if "timeout" in error_msg.lower() or attempt < max_retries - 1:
                wait_time = (attempt + 1) * 1
                time.sleep(wait_time)
                continue
            
            # Last attempt failed
            raise


def generate_email_record(
    tenant_id: str,
    post: Post,
    profile: Profile,
    template: EmailTemplate,
    sender_name: str,
    campaign_id: Optional[str] = None
) -> Email:
    """
    Generate a personalized email using Claude API and save to database.
    
    Returns:
        Email: The created email record
    """
    try:
        # Build Claude prompt
        prompt = build_claude_prompt(post, profile, template, sender_name)
        
        # Call Claude API
        claude_response = call_claude_api(prompt)
        
        # Extract values from Claude response
        product_name = claude_response.get('product_name', '')
        post_summary = claude_response.get('post_summary', '')
        subject = claude_response.get('subject', template.subject)
        body = claude_response.get('body', template.body)
        
        # Fallback: if Claude didn't provide subject/body, do manual replacement
        if subject == template.subject or body == template.body:
            # Manual placeholder replacement as fallback
            company_name = post.company.name if post.company else "the company"
            recipient_name = extract_first_name(profile.person_name)
            
            replacements = {
                'recipient_name': recipient_name,
                'company_name': company_name,
                'product_name': product_name or 'the product',
                'sender_name': sender_name,
                'post_summary': post_summary
            }
            
            # Replace in subject
            for key, value in replacements.items():
                subject = subject.replace(f'{{{{{key}}}}}', str(value))
            
            # Replace in body
            for key, value in replacements.items():
                body = body.replace(f'{{{{{key}}}}}', str(value))
        
        # Create email record
        email = Email(
            tenant_id=tenant_id,
            post_id=post.post_id,
            profile_id=profile.profile_id,
            template_id=template.template_id,
            subject=subject,
            body=body,
            status='draft'
        )
        
        db.session.add(email)
        db.session.flush()  # Get email_id
        
        # If profile is in a campaign, update campaign_profiles
        if campaign_id:
            campaign_profile = CampaignProfile.query.filter_by(
                campaign_id=campaign_id,
                profile_id=profile.profile_id
            ).first()
            
            if campaign_profile:
                campaign_profile.email_id = email.email_id
                campaign_profile.status = 'email_generated'
        
        db.session.commit()
        
        logger.info("Email generated successfully", extra={
            "email_id": email.email_id,
            "post_id": post.post_id,
            "profile_id": profile.profile_id,
            "campaign_id": campaign_id
        })
        
        return email
        
    except Exception as e:
        logger.exception("Failed to generate email", extra={
            "post_id": post.post_id,
            "profile_id": profile.profile_id,
            "error": str(e)
        })
        db.session.rollback()
        raise

