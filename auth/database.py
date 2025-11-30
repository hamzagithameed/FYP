"""
Database connection and configuration for MongoDB
"""
import os
import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/inkwave")
DATABASE_NAME = "inkwave"

# Global database client
client = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, database
    try:
        # Check if using local MongoDB or Atlas
        is_local = "localhost" in MONGODB_URI or "127.0.0.1" in MONGODB_URI
        
        if is_local:
            # Local MongoDB - no SSL
            client = AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
        else:
            # MongoDB Atlas - use SSL with compatibility settings
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            client = AsyncIOMotorClient(
                MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000
            )
        
        database = client[DATABASE_NAME]
        # Test connection
        await client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        print("⚠️  App will continue without authentication")
        # Don't raise - allow app to start without MongoDB


async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✓ Closed MongoDB connection")


def get_database():
    """Get database instance"""
    return database


def get_users_collection():
    """Get users collection"""
    return database.users
