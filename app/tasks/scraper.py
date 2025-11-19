from datetime import datetime
from apify_client import ApifyClient
from app.tasks.celery_app import celery_app
from app import create_app
from app.extensions import db
from app.models.company import Company
from app.models.post import Post
from app.config import Config
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='scrape_company_posts')
def scrape_company_posts(self, company_id, max_posts=100):
    """
    Scrape LinkedIn company posts using Apify API.
    
    Args:
        company_id: UUID of the company to scrape
        max_posts: Maximum number of posts to scrape (default: 100)
    
    Returns:
        dict: Result with status and message
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Get company from database
            company = Company.query.filter_by(company_id=company_id).first()
            if not company:
                logger.error(f"Company not found: {company_id}")
                return {"status": "error", "message": "Company not found"}
            
            if not company.is_active:
                logger.warning(f"Company is inactive: {company_id}")
                return {"status": "error", "message": "Company is inactive"}
            
            # Step 2: Check Apify API token
            apify_token = Config.APIFY_API_TOKEN
            if not apify_token:
                logger.error("APIFY_API_TOKEN not configured")
                return {"status": "error", "message": "Apify API token not configured"}
            
            # Step 3: Initialize Apify client
            client = ApifyClient(apify_token)
            
            # Step 4: Extract company identifier from LinkedIn URL
            # Apify accepts company name or full URL
            # Example: "google" or "https://www.linkedin.com/company/google/"
            linkedin_url = company.linkedin_url.strip()
            
            # Extract company slug from URL if full URL provided
            if 'linkedin.com/company/' in linkedin_url:
                # Extract company identifier (slug)
                parts = linkedin_url.split('linkedin.com/company/')
                if len(parts) > 1:
                    company_identifier = parts[1].rstrip('/').split('/')[0]
                else:
                    company_identifier = linkedin_url
            else:
                company_identifier = linkedin_url
            
            logger.info(f"Starting scrape for company: {company.name} ({company_identifier})")
            
            # Step 5: Calculate pages needed based on max_posts
            # Apify returns up to 100 posts per page
            posts_per_page = 100
            pages_needed = (max_posts + posts_per_page - 1) // posts_per_page  # Ceiling division
            
            all_posts = []
            
            # Step 6: Call Apify Actor for each page
            for page_num in range(1, pages_needed + 1):
                try:
                    # Prepare input for Apify Actor
                    run_input = {
                        "companyIdentifier": company_identifier,
                        "pageNumber": page_num
                    }
                    
                    logger.info(f"Calling Apify Actor (page {page_num}/{pages_needed})")
                    
                    # Run the Actor
                    run = client.actor(Config.APIFY_ACTOR_ID).call(run_input=run_input)
                    
                    # Get results
                    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                    
                    logger.info(f"Received {len(dataset_items)} posts from page {page_num}")
                    
                    # Add posts to collection
                    all_posts.extend(dataset_items)
                    
                    # Stop if we have enough posts
                    if len(all_posts) >= max_posts:
                        all_posts = all_posts[:max_posts]
                        break
                        
                except Exception as e:
                    logger.error(f"Error calling Apify API (page {page_num}): {str(e)}")
                    # Continue with next page or break if first page fails
                    if page_num == 1:
                        raise
                    break
            
            if not all_posts:
                logger.warning(f"No posts found for company: {company.name}")
                company.last_scraped_at = datetime.utcnow()
                db.session.commit()
                return {
                    "status": "success",
                    "message": "No posts found",
                    "posts_scraped": 0
                }
            
            # Step 7: Parse and save posts to database
            posts_saved = 0
            posts_skipped = 0
            
            for post_data in all_posts:
                try:
                    # Extract post URL (required field) - Apify uses 'post_url' (underscore)
                    post_url = post_data.get('post_url') or post_data.get('postUrl') or post_data.get('url')
                    if not post_url:
                        logger.warning(f"Post missing URL, skipping. Keys: {list(post_data.keys())}")
                        posts_skipped += 1
                        continue
                    
                    # Check if post already exists (by source_url)
                    existing_post = Post.query.filter_by(
                        tenant_id=company.tenant_id,
                        company_id=company.company_id,
                        source_url=post_url
                    ).first()
                    
                    if existing_post:
                        # Update existing post
                        existing_post.post_text = post_data.get('text') or post_data.get('content') or existing_post.post_text
                        # Parse date from posted_at dict structure
                        posted_at = post_data.get('posted_at') or post_data.get('postedAt')
                        if posted_at:
                            try:
                                if isinstance(posted_at, dict) and 'date' in posted_at:
                                    # Apify returns: {'date': '2025-11-13 18:58:46', ...}
                                    date_str = posted_at['date']
                                    existing_post.post_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
                                elif isinstance(posted_at, str):
                                    existing_post.post_date = datetime.fromisoformat(
                                        posted_at.replace('Z', '+00:00')
                                    ).date()
                            except Exception as e:
                                logger.debug(f"Could not parse date: {e}")
                        posts_saved += 1
                        continue
                    
                    # Parse post date - handle Apify's posted_at dict structure
                    post_date = None
                    posted_at = post_data.get('posted_at') or post_data.get('postedAt')
                    if posted_at:
                        try:
                            if isinstance(posted_at, dict) and 'date' in posted_at:
                                # Apify returns: {'date': '2025-11-13 18:58:46', 'timestamp': ..., ...}
                                date_str = posted_at['date']
                                post_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
                            elif isinstance(posted_at, str):
                                post_date = datetime.fromisoformat(
                                    posted_at.replace('Z', '+00:00')
                                ).date()
                        except Exception as e:
                            logger.debug(f"Could not parse date: {e}")
                    
                    # Extract post text/content
                    post_text = post_data.get('text') or post_data.get('content') or ''
                    
                    # Create new post
                    new_post = Post(
                        tenant_id=company.tenant_id,
                        company_id=company.company_id,
                        source_url=post_url,
                        post_text=post_text,
                        post_date=post_date,
                        score=0,  # Will be scored later by AI
                        ai_judgement=None
                    )
                    
                    db.session.add(new_post)
                    db.session.flush()  # Flush to get any immediate errors
                    posts_saved += 1
                    logger.debug(f"Added post: {post_url[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error saving post: {str(e)}", exc_info=True)
                    db.session.rollback()
                    posts_skipped += 1
                    continue
            
            # Step 8: Update company last_scraped_at
            company.last_scraped_at = datetime.utcnow()
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Successfully scraped {posts_saved} posts for company: {company.name}")
            
            return {
                "status": "success",
                "message": f"Scraped {posts_saved} posts",
                "posts_scraped": posts_saved,
                "posts_skipped": posts_skipped,
                "company_id": company_id
            }
            
        except Exception as e:
            logger.error(f"Error scraping company posts: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                "status": "error",
                "message": f"Scraping failed: {str(e)}",
                "company_id": company_id
            }

