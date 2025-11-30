"""
Authentication module for InkWave
"""
from .database import connect_to_mongo, close_mongo_connection, get_database, get_users_collection
from .security import verify_password, get_password_hash, create_access_token, decode_access_token
from .models import UserCreate, UserLogin, UserResponse, Token, UserInDB
from .crud import get_user_by_email, get_user_by_id, create_user, authenticate_user, user_doc_to_response

__all__ = [
    # Database
    "connect_to_mongo",
    "close_mongo_connection",
    "get_database",
    "get_users_collection",
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    # Models
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "UserInDB",
    # CRUD
    "get_user_by_email",
    "get_user_by_id",
    "create_user",
    "authenticate_user",
    "user_doc_to_response",
]
