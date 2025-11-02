from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth_schema import RegisterSchema, UserResponseSchema, TenantResponseSchema
from werkzeug.security import check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create Blueprint
bp = Blueprint('auth', __name__)

# Initialize schemas
register_schema = RegisterSchema()
user_schema = UserResponseSchema()
tenant_schema = TenantResponseSchema()


@bp.route('/register', methods=['POST'])
def register():
    """User Registration Endpoint"""

    """
    User Registration Endpoint
    
    Creates a new tenant and admin user in one transaction.
    First user in a tenant is always assigned 'admin' role.
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Acme Inc"
        }
    
    Returns:
        201: Registration successful with JWT tokens
        400: Validation error or email already exists
        500: Server error
    
    Example:
        POST /api/auth/register
        {
            "email": "john@acme.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Acme Inc"
        }
        
        Response:
        {
            "message": "Registration successful",
            "user": {...},
            "tenant": {...},
            "access_token": "eyJhbGc...",
            "refresh_token": "eyJhbGc..."
        }
    """
    try:
        # Step 1: Get and validate data
        data = request.get_json()
        
        try:
            validated_data = register_schema.load(data)
        except ValidationError as err:
            return jsonify({"error": "Validation failed", "details": err.messages}), 400
        
        # Step 2: Check if email already registered
        existing_user = User.query.filter_by(email=validated_data['email']).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        # Step 3: Create new tenant
        tenant = Tenant(
            company_name=validated_data['company_name'],
            plan='free',
            status='active'
        )
        
        # Step 4: Add and flush to generate tenant_id
        db.session.add(tenant)
        db.session.flush()  # Generates UUID without committing
        
        # Step 5: Hash password
        password_hash = generate_password_hash(validated_data['password'])
        
        # Step 6: Create admin user with tenant_id
        user = User(
            email=validated_data['email'],
            password_hash=password_hash,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            tenant_id=tenant.tenant_id,  # Now has value
            role='admin',
            is_active=True
        )
        
        # Step 7: Save user and commit transaction
        db.session.add(user)
        db.session.commit()
        
        # Step 8: Generate JWT tokens
        access_token = create_access_token(
            identity=user.user_id,
            additional_claims={
                "tenant_id": user.tenant_id,
                "email": user.email,
                "role": user.role
            }
        )
        
        refresh_token = create_refresh_token(identity=user.user_id)
        
        # Step 9: Return response
        return jsonify({
            "message": "Registration successful",
            "user": user_schema.dump(user),
            "tenant": tenant_schema.dump(tenant),
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Login Endpoint

    Flow:
    1️⃣ Receive email, password
    2️⃣ Find user in DB
    3️⃣ Verify password hash
    4️⃣ Generate JWT tokens (24h expiry)
    5️⃣ Return user info + tokens

    Responses:
      200 ✅ Login successful
      401 ❌ Wrong password
      404 ❌ User not found
    """

    data = request.get_json() or {}

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Step 1: Lookup user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Step 2: Verify password
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Step 3: Create JWT tokens
    access_token = create_access_token(
        identity=user.user_id,
        additional_claims={
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role
        }
    )
    refresh_token = create_refresh_token(identity=user.user_id)

    # Step 4: Prepare user info
    user_info = {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }

    # Step 5: Return response
    return jsonify({
        "message": "Login successful",
        "user": user_info,
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh Token Endpoint
    - Requires a valid refresh token
    - Returns a new access token
    """

    current_user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    new_access_token = create_access_token(
        identity=user.user_id,
        additional_claims={
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role
        }
    )

    return jsonify({
        "access_token": new_access_token
    }), 200

# for saqib: (move or change as needed)

@bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Return current logged-in user's info.
    - Requires valid access token
    """

    current_user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_info = {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }

    return jsonify({"user": user_info}), 200
