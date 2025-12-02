from datetime import datetime
from apify_client import ApifyClient
from app.tasks.celery_app import celery_app
from app import create_app
from app.extensions import db
from app.models.company import Company
from app.models.post import Post
from app.models.profile import Profile
from app.models.job import Job
from app.config import Config
import logging
import json
import time
try:
    from requests.exceptions import Timeout, ConnectionError, HTTPError
except ImportError:
    # Fallback if requests is not available
    Timeout = Exception
    ConnectionError = Exception
    HTTPError = Exception

try:
    from apify_client._errors import ApifyApiError  # type: ignore
except ImportError:
    # Fallback if ApifyApiError is not available
    ApifyApiError = Exception

logger = logging.getLogger(__name__)

# Configuration constants
BATCH_COMMIT_SIZE = 5  # Commit database changes every N profiles
PROGRESS_UPDATE_INTERVAL = 5  # Update job progress every N profiles
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2  # seconds
API_TIMEOUT = 60  # seconds for Apify API calls

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


@celery_app.task(bind=True, name='scrape_profiles')
def scrape_profiles(self, job_id, tenant_id, profile_ids=None):
    """
    Scrape LinkedIn profile details using Apify unlimited-leads-linkedin API.
    
    Args:
        job_id: UUID of the job tracking this task
        tenant_id: UUID of the tenant
        profile_ids: List of profile IDs to scrape (None = scrape all url_only profiles for tenant)
    
    Returns:
        dict: Result with status and message
    """
    app = create_app()
    
    with app.app_context():
        job = None
        try:
            # Get or create job record
            job = Job.query.filter_by(job_id=job_id).first()
            if not job:
                logger.error(f"Job not found: {job_id}")
                return {"status": "error", "message": "Job not found"}
            
            # Update job status to processing
            job.status = 'processing'
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Profile scraping job started: job_id={job_id}, tenant_id={tenant_id}")
            
            # Step 1: Get profiles to scrape
            if profile_ids:
                profiles = Profile.query.filter(
                    Profile.profile_id.in_(profile_ids),
                    Profile.tenant_id == tenant_id,
                    Profile.status == 'url_only'
                ).all()
            else:
                profiles = Profile.query.filter_by(
                    tenant_id=tenant_id,
                    status='url_only'
                ).limit(50).all()  # Batch limit: 50 profiles per job
            
            if not profiles:
                logger.warning(f"No profiles to scrape for tenant_id={tenant_id}")
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {
                    "status": "success",
                    "message": "No profiles to scrape",
                    "profiles_scraped": 0
                }
            
            # Update job with total items
            job.total_items = len(profiles)
            db.session.commit()
            
            logger.debug(f"Scraping {len(profiles)} profiles for tenant_id={tenant_id}")
            
            # Step 2: Check Apify API token
            apify_token = Config.APIFY_API_TOKEN
            if not apify_token:
                logger.error("APIFY_API_TOKEN not configured")
                job.status = 'failed'
                job.error_message = "Apify API token not configured"
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {"status": "error", "message": "Apify API token not configured"}
            
            # Step 3: Initialize Apify client
            client = ApifyClient(apify_token)
            
            # Step 3.5: Validate actor ID
            actor_id = Config.APIFY_PROFILE_ACTOR_ID
            if not actor_id or not isinstance(actor_id, str) or actor_id.strip() == '':
                logger.error("APIFY_PROFILE_ACTOR_ID is not configured or is empty")
                job.status = 'failed'
                job.error_message = "Apify profile actor ID not configured. Please set APIFY_PROFILE_ACTOR_ID environment variable."
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {"status": "error", "message": "Apify profile actor ID not configured"}
            
            # Check if actor ID looks like a URL (common mistake)
            if actor_id.startswith('http://') or actor_id.startswith('https://'):
                logger.error(f"APIFY_PROFILE_ACTOR_ID appears to be a URL, not an actor ID: {actor_id}")
                logger.error("Actor ID should be in format: 'username/actor-name' (e.g., 'apify/linkedin-profile-scraper')")
                job.status = 'failed'
                job.error_message = f"Invalid actor ID format (looks like a URL): {actor_id}. Should be 'username/actor-name'"
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {"status": "error", "message": f"Invalid actor ID format: {actor_id}"}
            
            # Validate actor ID format
            if '/' not in actor_id or actor_id.count('/') != 1:
                logger.error(f"APIFY_PROFILE_ACTOR_ID has invalid format: {actor_id}")
                logger.error("Actor ID should be in format: 'username/actor-name'")
                job.status = 'failed'
                job.error_message = f"Invalid actor ID format: {actor_id}. Should be 'username/actor-name'"
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
                return {"status": "error", "message": f"Invalid actor ID format: {actor_id}"}
            
            # Step 4: Process profiles with optimized batching
            success_count = 0
            failed_count = 0
            failed_profiles = []
            profiles_to_commit = []
            last_progress_update = 0
            
            for idx, profile in enumerate(profiles, 1):
                try:
                    logger.debug(f"Scraping profile {idx}/{len(profiles)}: {profile.linkedin_url}")
                    
                    # Call Apify API with optimized retry logic
                    apify_result = _call_apify_with_retry(
                        client, 
                        profile.linkedin_url, 
                        profile.profile_id,
                        logger
                    )
                    
                    if not apify_result:
                        raise Exception("No data returned from Apify")
                    
                    # Parse and update profile
                    _update_profile_from_apify_result(profile, apify_result)
                    profiles_to_commit.append(profile)
                    success_count += 1
                    
                    logger.debug(f"Successfully scraped profile {profile.profile_id}: {profile.person_name}")
                    
                except ValueError as e:
                    # Handle actor not found errors specifically
                    error_msg = str(e)
                    if "Actor" in error_msg and "not found" in error_msg:
                        error_type = 'actor_not_found'
                        logger.error(
                            f"Error scraping profile {profile.profile_id} ({error_type}): {error_msg}", 
                            exc_info=True
                        )
                        profile.status = 'scraping_failed'
                        profiles_to_commit.append(profile)
                        failed_count += 1
                        failed_profiles.append({
                            "profile_id": profile.profile_id,
                            "linkedin_url": profile.linkedin_url,
                            "error": error_msg,
                            "error_type": error_type
                        })
                    else:
                        # Re-raise other ValueError exceptions
                        raise
                except Exception as e:
                    error_type = _categorize_error(e)
                    logger.error(
                        f"Error scraping profile {profile.profile_id} ({error_type}): {str(e)}", 
                        exc_info=True
                    )
                    profile.status = 'scraping_failed'
                    profiles_to_commit.append(profile)
                    failed_count += 1
                    failed_profiles.append({
                        "profile_id": profile.profile_id,
                        "linkedin_url": profile.linkedin_url,
                        "error": str(e),
                        "error_type": error_type
                    })
                
                # Batch commit database changes
                if len(profiles_to_commit) >= BATCH_COMMIT_SIZE or idx == len(profiles):
                    try:
                        db.session.commit()
                        profiles_to_commit.clear()
                        logger.debug(f"Committed batch: {idx}/{len(profiles)} profiles processed")
                    except Exception as e:
                        logger.error(f"Error committing batch: {str(e)}", exc_info=True)
                        db.session.rollback()
                        # Mark failed profiles in this batch
                        for p in profiles_to_commit:
                            if p.status != 'scraping_failed':
                                p.status = 'scraping_failed'
                                failed_count += 1
                                success_count -= 1
                        profiles_to_commit.clear()
                
                # Update job progress periodically (not every profile)
                if idx - last_progress_update >= PROGRESS_UPDATE_INTERVAL or idx == len(profiles):
                    try:
                        job.completed_items = idx
                        job.success_count = success_count
                        job.failed_count = failed_count
                        job.updated_at = datetime.utcnow()
                        db.session.commit()
                        last_progress_update = idx
                        logger.debug(f"Progress updated: {idx}/{len(profiles)} ({success_count} success, {failed_count} failed)")
                    except Exception as e:
                        logger.warning(f"Error updating job progress: {str(e)}")
                        db.session.rollback()
            
            # Step 6: Finalize job
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            
            # Store failed profiles in result_data
            if failed_profiles:
                result_data = {
                    "failed_profiles": failed_profiles
                }
                job.result_data = json.dumps(result_data)
            
            db.session.commit()
            
            logger.info(f"Profile scraping completed: job_id={job_id}, success={success_count}, failed={failed_count}")
            
            return {
                "status": "success",
                "message": f"Scraped {success_count} profiles, {failed_count} failed",
                "profiles_scraped": success_count,
                "profiles_failed": failed_count,
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error in profile scraping task: {str(e)}", exc_info=True)
            if job:
                job.status = 'failed'
                error_msg = str(e)
                # Provide helpful message for actor not found errors
                if 'actor' in error_msg.lower() and 'not found' in error_msg.lower():
                    actor_id = Config.APIFY_PROFILE_ACTOR_ID
                    error_msg = f"Apify Actor '{actor_id}' not found. Please set a valid APIFY_PROFILE_ACTOR_ID environment variable. Common options: apify/linkedin-profile-scraper, apify/linkedin-scraper, apify/unlimited-leads-linkedin"
                job.error_message = error_msg
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.session.commit()
            else:
                db.session.rollback()
            return {
                "status": "error",
                "message": f"Scraping failed: {str(e)}",
                "job_id": job_id
            }


def _call_apify_with_retry(client, linkedin_url, profile_id, logger):
    """
    Call Apify API with optimized retry logic and error handling.
    
    Returns:
        dict: Apify result or None if all retries failed
    """
    apify_result = None
    last_exception = None
    actor_id = Config.APIFY_PROFILE_ACTOR_ID  # Get actor ID once, outside retry loop
    
    # Validate actor ID
    if not actor_id or not isinstance(actor_id, str) or actor_id.strip() == '':
        raise ValueError("APIFY_PROFILE_ACTOR_ID is not configured or is empty")
    if actor_id.startswith('http://') or actor_id.startswith('https://'):
        raise ValueError(f"APIFY_PROFILE_ACTOR_ID appears to be a URL, not an actor ID: {actor_id}. "
                        f"Actor ID should be in format: 'username/actor-name' (e.g., 'apify/linkedin-profile-scraper')")
    
    # Different Apify actors use different input field names
    # apify/linkedin-profile-scraper uses profileUrls (array of strings)
    # Other actors may use startUrls (array of objects with url property)
    if 'linkedin-profile-scraper' in actor_id.lower():
        run_input = {
            "profileUrls": [linkedin_url]  # Array of strings
        }
        logger.debug(f"Using profileUrls format for actor: {actor_id}")
    else:
        # Default to startUrls format (for other actors)
        run_input = {
            "startUrls": [{"url": linkedin_url}]  # Array of objects
        }
        logger.debug(f"Using startUrls format for actor: {actor_id}")
    
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = INITIAL_RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.debug(f"Retrying Apify call (attempt {attempt + 1}/{MAX_RETRIES}) after {delay}s")
                time.sleep(delay)
            
            logger.debug(f"Calling Apify Actor '{actor_id}' (attempt {attempt + 1}/{MAX_RETRIES}) for profile {profile_id}")
            
            # Call Apify with timeout handling
            run = client.actor(actor_id).call(
                run_input=run_input,
                timeout_secs=API_TIMEOUT
            )
            
            # Get results with timeout protection
            dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if dataset_items:
                apify_result = dataset_items[0]  # First result
                logger.info(f"Successfully retrieved data from Apify for profile {profile_id}")
                logger.info(f"Dataset contains {len(dataset_items)} item(s)")
                
                # Log the structure for debugging
                if isinstance(apify_result, dict):
                    logger.info(f"Apify result keys: {list(apify_result.keys())}")
                    # Log a sample of the data (first 1000 chars to avoid log spam)
                    result_sample = json.dumps(apify_result, indent=2, default=str)[:1000]
                    logger.debug(f"Apify result sample: {result_sample}")
                else:
                    logger.warning(f"Apify result is not a dict, type: {type(apify_result)}")
                
                break
            else:
                logger.warning(f"No data returned from Apify dataset for profile {profile_id}")
                logger.warning(f"Run status: {run.get('status')}, Run ID: {run.get('id')}")
                # Check if run has any error messages
                if run.get('status') == 'SUCCEEDED' and not dataset_items:
                    logger.warning("Run succeeded but dataset is empty - actor may have returned no data")
                last_exception = Exception("No data returned from Apify dataset")
                
        except (Timeout, ConnectionError) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Network error (attempt {attempt + 1}): {str(e)}, will retry...")
            else:
                logger.error(f"Network error after {MAX_RETRIES} attempts: {str(e)}")
                
        except HTTPError as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'response') and e.response is not None:
                status_code = getattr(e.response, 'status_code', None)
                if status_code == 429:
                    # Rate limited - use longer backoff
                    if attempt < MAX_RETRIES - 1:
                        delay = INITIAL_RETRY_DELAY * (2 ** attempt) * 2  # Double the backoff for rate limits
                        logger.warning(f"Rate limited (429), waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"HTTP error (attempt {attempt + 1}): {str(e)}, will retry...")
            else:
                logger.error(f"HTTP error after {MAX_RETRIES} attempts: {str(e)}")
                
        except ApifyApiError as e:
            # Apify-specific errors (e.g., actor not found)
            last_exception = e
            error_msg = str(e)
            error_lower = error_msg.lower()
            
            # Check for actor not found errors - don't retry these
            if "actor" in error_lower and ("not found" in error_lower or "was not found" in error_lower):
                logger.error(f"Apify Actor '{actor_id}' not found or unavailable. Error: {error_msg}")
                logger.error(f"Please check the actor ID in your configuration. Current: {actor_id}")
                logger.error("Common alternatives:")
                logger.error("  - apify/linkedin-profile-scraper")
                logger.error("  - apify/linkedin-scraper")
                logger.error("  - apify/unlimited-leads-linkedin")
                logger.error("  - apify/linkedin-profile-enrichment")
                # Don't retry - actor doesn't exist, retrying won't help
                raise ValueError(f"Apify Actor '{actor_id}' not found. Please set a valid APIFY_PROFILE_ACTOR_ID in your environment variables. Error: {error_msg}")
            
            # For other Apify errors, retry if appropriate
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Apify API error (attempt {attempt + 1}): {error_msg}, will retry...")
            else:
                logger.error(f"Apify API error after {MAX_RETRIES} attempts: {error_msg}")
                
        except Exception as e:
            # Other unexpected errors
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Unexpected error (attempt {attempt + 1}): {str(e)}, will retry...")
            else:
                logger.error(f"Unexpected error after {MAX_RETRIES} attempts: {str(e)}")
    
    if not apify_result and last_exception:
        raise last_exception
    
    return apify_result


def _update_profile_from_apify_result(profile, apify_result):
    """
    Update profile fields from Apify result data.
    Handles different Apify actor response formats, including nested structures.
    """
    now = datetime.utcnow()
    
    # Log what we received for debugging
    if isinstance(apify_result, dict):
        logger.info(f"Updating profile from Apify result - Keys: {list(apify_result.keys())}")
        logger.debug(f"Apify result sample: {json.dumps(apify_result, indent=2, default=str)[:1000]}")
    else:
        logger.warning(f"Apify result is not a dict, type: {type(apify_result)}")
        # If it's not a dict, try to extract data from it
        if hasattr(apify_result, '__dict__'):
            apify_result = apify_result.__dict__
        else:
            logger.error(f"Cannot process Apify result of type {type(apify_result)}")
            profile.status = 'scraped'
            profile.scraped_at = now
            return
    
    # Helper function to get nested values
    def get_nested_value(data, *keys):
        """Get value from nested dict/list using multiple keys."""
        if not isinstance(data, (dict, list)):
            return None
        current = data
        for key in keys:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                current = current[key]
            else:
                return None
        return current
    
    # Different Apify actors return data in different formats
    # Try multiple possible field names for each attribute, including nested structures
    
    # Person Name - try: name, fullName, full_name, personName, title, profile.name, data.name
    person_name = (
        get_nested_value(apify_result, 'name') or
        get_nested_value(apify_result, 'fullName') or
        get_nested_value(apify_result, 'full_name') or
        get_nested_value(apify_result, 'personName') or
        get_nested_value(apify_result, 'title') or
        get_nested_value(apify_result, 'profile', 'name') or
        get_nested_value(apify_result, 'data', 'name') or
        apify_result.get('name') or 
        apify_result.get('fullName') or 
        apify_result.get('full_name') or 
        apify_result.get('personName') or
        apify_result.get('title') or
        None
    )
    if person_name:
        profile.person_name = str(person_name).strip() if person_name else None
    
    # Email - try: email, emailAddress, email_address, contactEmail, profile.email, data.email
    email = (
        get_nested_value(apify_result, 'email') or
        get_nested_value(apify_result, 'emailAddress') or
        get_nested_value(apify_result, 'email_address') or
        get_nested_value(apify_result, 'contactEmail') or
        get_nested_value(apify_result, 'profile', 'email') or
        get_nested_value(apify_result, 'data', 'email') or
        apify_result.get('email') or 
        apify_result.get('emailAddress') or 
        apify_result.get('email_address') or 
        apify_result.get('contactEmail') or
        None
    )
    if email:
        profile.email = str(email).strip() if email else None
    
    # Phone - try: phone, phoneNumber, phone_number, contactPhone
    phone = (
        apify_result.get('phone') or 
        apify_result.get('phoneNumber') or 
        apify_result.get('phone_number') or 
        apify_result.get('contactPhone') or
        None
    )
    if phone:
        profile.phone = phone
    
    # Company - try: company, companyName, company_name, currentCompany, organization, experience.company
    company = (
        get_nested_value(apify_result, 'company') or
        get_nested_value(apify_result, 'companyName') or
        get_nested_value(apify_result, 'company_name') or
        get_nested_value(apify_result, 'currentCompany') or
        get_nested_value(apify_result, 'organization') or
        get_nested_value(apify_result, 'experience', 0, 'company') if isinstance(apify_result.get('experience'), list) and len(apify_result.get('experience', [])) > 0 else None or
        apify_result.get('company') or 
        apify_result.get('companyName') or 
        apify_result.get('company_name') or 
        apify_result.get('currentCompany') or
        apify_result.get('organization') or
        None
    )
    if company:
        profile.company = str(company).strip() if company else None
    
    # Job Title - try: jobTitle, job_title, position, title, currentPosition, experience.position
    job_title = (
        get_nested_value(apify_result, 'jobTitle') or
        get_nested_value(apify_result, 'job_title') or
        get_nested_value(apify_result, 'position') or
        get_nested_value(apify_result, 'currentPosition') or
        get_nested_value(apify_result, 'experience', 0, 'position') if isinstance(apify_result.get('experience'), list) and len(apify_result.get('experience', [])) > 0 else None or
        apify_result.get('jobTitle') or 
        apify_result.get('job_title') or 
        apify_result.get('position') or 
        apify_result.get('currentPosition') or
        None
    )
    if job_title:
        profile.job_title = str(job_title).strip() if job_title else None
    
    # Headline - try: headline, summary, bio, description
    headline = (
        apify_result.get('headline') or 
        apify_result.get('summary') or 
        apify_result.get('bio') or 
        apify_result.get('description') or
        None
    )
    if headline:
        profile.headline = headline
    
    # Location - try: location, city, address, locationName
    location = (
        apify_result.get('location') or 
        apify_result.get('city') or 
        apify_result.get('address') or 
        apify_result.get('locationName') or
        None
    )
    if location:
        profile.location = location
    
    # Industry - try: industry, sector, industryType
    industry = (
        apify_result.get('industry') or 
        apify_result.get('sector') or 
        apify_result.get('industryType') or
        None
    )
    if industry:
        profile.industry = industry
    
    # Always update status and timestamp on success (even if no data was extracted)
    profile.status = 'scraped'
    profile.scraped_at = now
    
    # Log if no data was extracted (for debugging)
    if not any([person_name, email, phone, company, job_title, headline, location, industry]):
        logger.warning(f"Profile {profile.profile_id} marked as scraped but no data fields were populated. Apify result keys: {list(apify_result.keys()) if isinstance(apify_result, dict) else type(apify_result)}")


def _categorize_error(error):
    """
    Categorize errors for better tracking and handling.
    
    Returns:
        str: Error category (network, rate_limit, api_error, actor_not_found, not_found, other)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Check for actor not found errors first
    if 'actor' in error_str and ('not found' in error_str or 'was not found' in error_str):
        return 'actor_not_found'
    
    if isinstance(error, (Timeout, ConnectionError)):
        return 'network'
    elif isinstance(error, HTTPError):
        if hasattr(error, 'response') and error.response is not None:
            status_code = getattr(error.response, 'status_code', None)
            if status_code == 429:
                return 'rate_limit'
            elif status_code == 404:
                return 'not_found'
        return 'api_error'
    elif isinstance(error, ApifyApiError):
        # Check error message for actor not found
        if 'actor' in error_str and 'not found' in error_str:
            return 'actor_not_found'
        return 'api_error'
    elif 'not found' in error_str or '404' in error_str:
        return 'not_found'
    elif 'rate limit' in error_str or '429' in error_str:
        return 'rate_limit'
    elif 'timeout' in error_str:
        return 'network'
    else:
        return 'other'

