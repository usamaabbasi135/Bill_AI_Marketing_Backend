"""
Celery task for analyzing LinkedIn posts using Claude AI
"""
import os
import logging
from datetime import datetime
from anthropic import Anthropic
from app.tasks.celery_app import celery_app
from app.extensions import db
from app.models.post import Post
from app.models.job import Job
from app import create_app

logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = None


def get_anthropic_client():
    """Get or create Anthropic client"""
    global anthropic_client
    if anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        anthropic_client = Anthropic(api_key=api_key)
    return anthropic_client


@celery_app.task(bind=True, max_retries=3)
def analyze_post(self, job_id, tenant_id, post_id):
    """
    Analyze a LinkedIn post using Claude AI to detect product launches.
    
    Args:
        job_id: UUID of the job tracking this task
        tenant_id: UUID of the tenant
        post_id: UUID of the post to analyze
        
    Returns:
        dict: Analysis result with score and judgement
    """
    app = create_app()
    
    with app.app_context():
        job = None
        try:
            # Get job record
            job = Job.query.filter_by(job_id=job_id).first()
            if not job:
                logger.error(f"Job not found: {job_id}")
                return {"status": "error", "message": "Job not found"}
            
            # Update job status to processing
            job.status = 'processing'
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Post analysis job started: job_id={job_id}, post_id={post_id}")
            
            # Get post from database
            post = Post.query.filter_by(post_id=post_id, tenant_id=tenant_id).first()
            if not post:
                logger.error(f"Post {post_id} not found")
                job.status = 'failed'
                job.error_message = f"Post not found: {post_id}"
                job.completed_at = datetime.utcnow()
                job.completed_items = 1
                job.failed_count = 1
                db.session.commit()
                return {"error": "Post not found", "post_id": post_id}
            
            if not post.post_text:
                logger.warning(f"Post {post_id} has no text to analyze")
                # Update with default values
                post.score = 0
                post.ai_judgement = 'other'
                post.analyzed_at = datetime.utcnow()
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.completed_items = 1
                job.success_count = 1
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {"error": "Post has no text", "post_id": post_id}
            
            # Prepare prompt for Claude
            prompt = f"""Is this LinkedIn post announcing a product launch? Score 0-100. Return: {{"score": X, "judgement": "product_launch"|"other"}}

Post text:
{post.post_text}

Analyze and return JSON only:"""
            
            # Call Claude API
            client = get_anthropic_client()
            
            try:
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract response text
                response_text = message.content[0].text.strip()
                
                # Parse JSON response
                import json
                # Try to extract JSON from response (handle markdown code blocks)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(response_text)
                
                # Validate response structure
                score = int(analysis.get('score', 0))
                judgement = analysis.get('judgement', 'other')
                
                if judgement not in ['product_launch', 'other']:
                    judgement = 'other'
                
                # Clamp score to 0-100
                score = max(0, min(100, score))
                
                # Update post
                post.score = score
                post.ai_judgement = judgement
                post.analyzed_at = datetime.utcnow()
                
                # Update job status to completed
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.completed_items = 1
                job.success_count = 1
                job.updated_at = datetime.utcnow()
                
                # Store result data
                result_data = {
                    "post_id": post_id,
                    "score": score,
                    "judgement": judgement,
                    "analyzed_at": post.analyzed_at.isoformat() if post.analyzed_at else None
                }
                job.result_data = json.dumps(result_data)
                
                db.session.commit()
                
                logger.info(f"Successfully analyzed post {post_id}: score={score}, judgement={judgement}")
                
                return {
                    "status": "success",
                    "post_id": post_id,
                    "score": score,
                    "judgement": judgement,
                    "analyzed_at": post.analyzed_at.isoformat() if post.analyzed_at else None
                }
                
            except Exception as api_error:
                logger.error(f"Claude API error for post {post_id}: {str(api_error)}")
                
                # Handle rate limits with exponential backoff
                if "rate limit" in str(api_error).lower() or "429" in str(api_error):
                    logger.warning(f"Rate limit hit for post {post_id}, retrying...")
                    raise self.retry(exc=api_error, countdown=60 * (2 ** self.request.retries))
                
                # For other API errors, retry with backoff
                raise self.retry(exc=api_error, countdown=30 * (2 ** self.request.retries))
            
        except Exception as e:
            logger.error(f"Error analyzing post {post_id}: {str(e)}")
            
            # If max retries reached, mark as failed
            if self.request.retries >= self.max_retries:
                try:
                    if job:
                        job.status = 'failed'
                        job.error_message = f"Analysis failed after retries: {str(e)}"
                        job.completed_at = datetime.utcnow()
                        job.completed_items = 1
                        job.failed_count = 1
                        job.updated_at = datetime.utcnow()
                        db.session.commit()
                    
                    post = Post.query.filter_by(post_id=post_id, tenant_id=tenant_id).first()
                    if post:
                        post.score = 0
                        post.ai_judgement = 'other'
                        post.analyzed_at = datetime.utcnow()
                        db.session.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update post {post_id} after max retries: {str(db_error)}")
                
                return {
                    "status": "error",
                    "error": "Analysis failed after retries",
                    "post_id": post_id,
                    "details": str(e)
                }
            
            raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))

