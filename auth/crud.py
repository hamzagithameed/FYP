"""
CRUD operations for user management
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from .database import get_users_collection
from .security import get_password_hash, verify_password
from .models import UserCreate, UserInDB, UserResponse


async def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user by email
    
    Args:
        email: User email
    
    Returns:
        dict: User document or None
    """
    users = get_users_collection()
    user = await users.find_one({"email": email.lower()})
    return user


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Get user by ID
    
    Args:
        user_id: User ID
    
    Returns:
        dict: User document or None
    """
    users = get_users_collection()
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        return user
    except:
        return None


async def create_user(user_data: UserCreate) -> UserResponse:
    """
    Create a new user
    
    Args:
        user_data: User registration data
    
    Returns:
        UserResponse: Created user data
    """
    users = get_users_collection()
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Create user document
    now = datetime.utcnow()
    user_doc = {
        "name": user_data.name,
        "email": user_data.email.lower(),
        "hashed_password": get_password_hash(user_data.password),
        "created_at": now,
        "updated_at": now
    }
    
    # Insert into database
    result = await users.insert_one(user_doc)
    
    # Return user response
    return UserResponse(
        id=str(result.inserted_id),
        name=user_doc["name"],
        email=user_doc["email"],
        created_at=user_doc["created_at"]
    )


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user with email and password
    
    Args:
        email: User email
        password: Plain text password
    
    Returns:
        dict: User document if authenticated, None otherwise
    """
    user = await get_user_by_email(email)
    
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user


def user_doc_to_response(user_doc: dict) -> UserResponse:
    """
    Convert user document to UserResponse
    
    Args:
        user_doc: User document from database
    
    Returns:
        UserResponse: User response model
    """
    return UserResponse(
        id=str(user_doc["_id"]),
        name=user_doc["name"],
        email=user_doc["email"],
        created_at=user_doc["created_at"]
    )
