"""
OAuth API Endpoints

Handles OAuth flows for Microsoft and Google email providers.
"""
from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.extensions import db
from app.models.user_email_provider import UserEmailProvider
from app.services.oauth_service import OAuthService

bp = Blueprint('oauth', __name__)


@bp.route('/microsoft/authorize', methods=['GET'])
@jwt_required()
def microsoft_authorize():
    """
    Start Microsoft OAuth flow.
    
    Returns:
        JSON with authorization_url and state
    """
    claims = get_jwt()
    user_id = get_jwt_identity()
    
    if not user_id:
        current_app.logger.warning("Microsoft OAuth authorize: Missing user_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        auth_url, state = OAuthService.get_microsoft_authorization_url(user_id)
        current_app.logger.debug(f"Microsoft OAuth authorize: Generated URL for user_id={user_id}")
        
        return jsonify({
            "authorization_url": auth_url,
            "state": state
        }), 200
    
    except ValueError as e:
        current_app.logger.error(f"Microsoft OAuth authorize error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        current_app.logger.exception(f"Microsoft OAuth authorize unexpected error: {str(e)}")
        return jsonify({"error": "Failed to generate authorization URL"}), 500


@bp.route('/microsoft/callback', methods=['GET'])
def microsoft_callback():
    """
    Handle Microsoft OAuth callback.
    
    Query Parameters:
        code: Authorization code from Microsoft
        state: State parameter for CSRF protection
        error: Error code if authorization failed
        error_description: Error description
    
    Returns:
        Redirect to frontend with success/error status
    """
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    code = request.args.get('code')
    state = request.args.get('state')
    
    if error:
        current_app.logger.warning(f"Microsoft OAuth callback error: {error} - {error_description}")
        # Redirect to frontend with error
        # In production, replace with your frontend URL
        frontend_url = request.args.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        return redirect(f"{frontend_url}?error={error}&error_description={error_description}&provider=microsoft")
    
    if not code or not state:
        current_app.logger.warning("Microsoft OAuth callback: Missing code or state")
        frontend_url = request.args.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        return redirect(f"{frontend_url}?error=missing_code_or_state&provider=microsoft")
    
    try:
        result = OAuthService.handle_microsoft_callback(code, state)
        current_app.logger.info(f"Microsoft OAuth callback success: provider_id={result['provider_id']}")
        
        # Redirect to frontend with success
        frontend_url = request.args.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        return redirect(
            f"{frontend_url}?success=true&provider=microsoft&email={result['email']}&provider_id={result['provider_id']}"
        )
    
    except ValueError as e:
        current_app.logger.error(f"Microsoft OAuth callback error: {str(e)}")
        frontend_url = request.args.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        return redirect(f"{frontend_url}?error={str(e)}&provider=microsoft")
    
    except Exception as e:
        current_app.logger.exception(f"Microsoft OAuth callback unexpected error: {str(e)}")
        frontend_url = request.args.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        return redirect(f"{frontend_url}?error=internal_error&provider=microsoft")


@bp.route('/google/authorize', methods=['GET'])
@jwt_required()
def google_authorize():
    """
    Start Google OAuth flow.
    
    Returns:
        JSON with authorization_url and state
    """
    claims = get_jwt()
    user_id = get_jwt_identity()
    
    if not user_id:
        current_app.logger.warning("Google OAuth authorize: Missing user_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        auth_url, state = OAuthService.get_google_authorization_url(user_id)
        current_app.logger.debug(f"Google OAuth authorize: Generated URL for user_id={user_id}")
        
        return jsonify({
            "authorization_url": auth_url,
            "state": state
        }), 200
    
    except ValueError as e:
        current_app.logger.error(f"Google OAuth authorize error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        current_app.logger.exception(f"Google OAuth authorize unexpected error: {str(e)}")
        return jsonify({"error": "Failed to generate authorization URL"}), 500


@bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    Handle Google OAuth callback.
    
    Query Parameters:
        code: Authorization code from Google
        state: State parameter for CSRF protection
        error: Error code if authorization failed
        error_description: Error description
    
    Returns:
        HTML page with success/error status (or redirect if redirect_uri provided)
    """
    from flask import render_template_string
    
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Success HTML template
    success_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Success</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #4CAF50; font-size: 24px; margin-bottom: 20px; }
            .info { color: #666; margin: 10px 0; }
            .close { margin-top: 20px; color: #999; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅ Success!</div>
            <h2>Google Account Connected</h2>
            <div class="info">Email: {{ email }}</div>
            <div class="info">Provider ID: {{ provider_id }}</div>
            <p class="close">You can close this window now.</p>
        </div>
    </body>
    </html>
    """
    
    # Error HTML template
    error_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .error { color: #f44336; font-size: 24px; margin-bottom: 20px; }
            .info { color: #666; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error">❌ Error</div>
            <h2>OAuth Connection Failed</h2>
            <div class="info">{{ error }}</div>
            <p>Please try again or contact support.</p>
        </div>
    </body>
    </html>
    """
    
    if error:
        current_app.logger.warning(f"Google OAuth callback error: {error} - {error_description}")
        error_msg = error_description or error
        return render_template_string(error_html, error=error_msg)
    
    if not code or not state:
        current_app.logger.warning("Google OAuth callback: Missing code or state")
        return render_template_string(error_html, error="Missing authorization code or state parameter")
    
    try:
        result = OAuthService.handle_google_callback(code, state)
        current_app.logger.info(f"Google OAuth callback success: provider_id={result['provider_id']}, email={result['email']}")
        
        # Check if redirect_uri is provided
        frontend_url = request.args.get('redirect_uri')
        if frontend_url:
            return redirect(
                f"{frontend_url}?success=true&provider=google&email={result['email']}&provider_id={result['provider_id']}"
            )
        
        # Otherwise show success page
        return render_template_string(
            success_html,
            email=result['email'],
            provider_id=result['provider_id']
        )
    
    except ValueError as e:
        error_msg = str(e)
        current_app.logger.error(f"Google OAuth callback error: {error_msg}")
        
        # Check if it's a state validation error
        if "state" in error_msg.lower() or "expired" in error_msg.lower():
            error_msg = "OAuth session expired. Please start the OAuth flow again from the beginning."
        
        frontend_url = request.args.get('redirect_uri')
        if frontend_url:
            return redirect(f"{frontend_url}?error={error_msg}&provider=google")
        
        return render_template_string(error_html, error=error_msg)
    
    except Exception as e:
        error_msg = f"Internal error: {str(e)}"
        current_app.logger.exception(f"Google OAuth callback unexpected error: {str(e)}")
        
        frontend_url = request.args.get('redirect_uri')
        if frontend_url:
            return redirect(f"{frontend_url}?error=internal_error&provider=google")
        
        return render_template_string(error_html, error=error_msg)


@bp.route('/providers', methods=['GET'])
@jwt_required()
def list_providers():
    """
    List all active email providers for the current user.
    
    Returns:
        JSON array of provider objects with provider_id, email, provider type, created_at
    """
    user_id = get_jwt_identity()
    
    if not user_id:
        current_app.logger.warning("List providers: Missing user_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        providers = UserEmailProvider.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(UserEmailProvider.created_at.desc()).all()
        
        current_app.logger.debug(f"List providers: Found {len(providers)} providers for user_id={user_id}")
        
        providers_data = [provider.to_dict() for provider in providers]
        
        return jsonify({
            "providers": providers_data
        }), 200
    
    except Exception as e:
        current_app.logger.exception(f"List providers error: {str(e)}")
        return jsonify({"error": "Failed to list providers"}), 500


@bp.route('/providers/<provider_id>', methods=['DELETE'])
@jwt_required()
def disconnect_provider(provider_id):
    """
    Disconnect an email provider (set is_active=False).
    
    Args:
        provider_id: Provider ID to disconnect
    
    Returns:
        JSON with success message
    """
    user_id = get_jwt_identity()
    
    if not user_id:
        current_app.logger.warning("Disconnect provider: Missing user_id in JWT token")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        provider = UserEmailProvider.query.filter_by(
            provider_id=provider_id,
            user_id=user_id
        ).first()
        
        if not provider:
            current_app.logger.warning(f"Disconnect provider: Provider not found provider_id={provider_id}, user_id={user_id}")
            return jsonify({"error": "Provider not found"}), 404
        
        # Set is_active=False instead of deleting (soft delete)
        provider.is_active = False
        db.session.commit()
        
        current_app.logger.info(f"Disconnected provider: provider_id={provider_id}, user_id={user_id}, email={provider.email}")
        
        return jsonify({
            "message": "Provider disconnected successfully",
            "provider_id": provider_id
        }), 200
    
    except Exception as e:
        current_app.logger.exception(f"Disconnect provider error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to disconnect provider"}), 500

