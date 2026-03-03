import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Secret Key for Flask sessions
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-default-key")
    
    # SQLite Database Configuration
    # Fallback to local 'chat_history.db' if not set
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///chat_history.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application settings
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "medicalbot")

    @classmethod
    def validate(cls):
        """Validates that all required environment variables are set."""
        missing = []
        if not cls.PINECONE_API_KEY:
            missing.append("PINECONE_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

