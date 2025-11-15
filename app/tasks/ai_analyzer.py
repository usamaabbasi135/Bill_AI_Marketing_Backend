"""
AI Analyzer Task

Celery task to analyze LinkedIn posts using Claude API for product launch detection.
"""
from datetime import datetime
import logging
import os
import json
import re
import time
from app.tasks.celery_app import celery_app
from app import create_app
from app.extensions import db
from app.models.post import Post

logger = logging.getLogger(__name__)

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")


def get_claude_client():
    """Get Claude API client instance."""
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not configured in environment variables")
    return Anthropic(api_key=api_key)


def analyze_post_with_claude(post_text: str, max_retries: int = 3, retry_delay: int = 2) -> dict:
    """
    Analyze a LinkedIn post using Claude API to detect product launches.
    Includes retry logic for rate limits and transient errors.
    
    Args:
        post_text: The text content of the LinkedIn post
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 2)
    
    Returns:
        dict: Analysis result with score and judgement
        Format: {"score": int(0-100), "judgement": "product_launch"|"other"}
    """
    if not CLAUDE_AVAILABLE:
        raise ImportError("Anthropic SDK not available. Install with: pip install anthropic")
    
    client = get_claude_client()
    
    # Prompt as specified
    prompt = """Is this LinkedIn post announcing a product launch? Score 0-100. Return: {"score": X, "judgement": "product_launch"|"other"}

Post content:
""" + post_text

    last_exception = None
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response text
            response_text = message.content[0].text.strip()
            
            # Parse JSON from response (handle cases where there's extra text)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            result = json.loads(response_text)
            
            # Validate and normalize
            score = max(0, min(100, int(result.get('score', 0))))
            judgement = result.get('judgement', 'other')
            
            # Ensure judgement is either 'product_launch' or 'other'
            if judgement not in ['product_launch', 'other']:
                judgement = 'other'
            
            return {
                'score': score,
                'judgement': judgement
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude API response as JSON (attempt {attempt + 1}/{max_retries}): {response_text[:200]}")
            last_exception = ValueError(f"Invalid JSON response from Claude API: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                raise last_exception
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit or retryable error
            is_retryable = any(keyword in error_str for keyword in [
                'rate limit', 'rate_limit', '429', 'too many requests',
                'timeout', 'connection', '503', '502', '500'
            ])
            
            if is_retryable and attempt < max_retries - 1:
                retry_after = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Claude API error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_after}s...")
                time.sleep(retry_after)
                last_exception = e
            else:
                logger.error(f"Error calling Claude API (attempt {attempt + 1}/{max_retries}): {str(e)}")
                raise


@celery_app.task(bind=True, name='analyze_post', autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60}, retry_backoff=True)
def analyze_post(self, post_id: str):
    """
    Analyze a single post using Claude AI to detect product launches.
    
    Flow:
    1. Get post text from database
    2. Send to Claude API with prompt
    3. Parse response
    4. Update post: score, ai_judgement, analyzed_at
    5. Log results
    
    Args:
        post_id: UUID of the post to analyze
    
    Returns:
        dict: Result with status and analysis details
    """
    # Create Flask app context for database access
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Get post text from database
            post = Post.query.filter_by(post_id=post_id).first()
            if not post:
                logger.error(f"Post not found: {post_id}")
                return {
                    "status": "error",
                    "message": "Post not found",
                    "post_id": post_id
                }
            
            # Check if post has text to analyze
            if not post.post_text or len(post.post_text.strip()) < 10:
                logger.warning(f"Post {post_id} has insufficient text for analysis")
                post.score = 0
                post.ai_judgement = 'other'
                post.analyzed_at = datetime.utcnow()
                db.session.commit()
                return {
                    "status": "success",
                    "message": "Post has insufficient text",
                    "post_id": post_id,
                    "score": 0,
                    "judgement": "other"
                }
            
            # Step 2: Send to Claude API with prompt
            logger.info(f"Analyzing post {post_id} with Claude API...")
            analysis = analyze_post_with_claude(post.post_text)
            
            # Step 3: Parse response (already done in analyze_post_with_claude)
            score = analysis['score']
            judgement = analysis['judgement']
            
            # Step 4: Update post: score, ai_judgement, analyzed_at
            post.score = score
            post.ai_judgement = judgement
            post.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            # Step 5: Log AI analysis results
            logger.info(
                f"Post {post_id} analyzed: score={score}, judgement={judgement}"
            )
            
            return {
                "status": "success",
                "message": "Post analyzed successfully",
                "post_id": post_id,
                "score": score,
                "judgement": judgement
            }
            
        except ValueError as e:
            # Handle API errors (rate limits, invalid responses, etc.)
            logger.error(f"API error analyzing post {post_id}: {str(e)}")
            db.session.rollback()
            return {
                "status": "error",
                "message": f"API error: {str(e)}",
                "post_id": post_id
            }
        except Exception as e:
            # Handle other errors
            logger.error(f"Error analyzing post {post_id}: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "post_id": post_id
            }

