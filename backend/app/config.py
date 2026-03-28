import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    def __init__(self) -> None:
        max_content_length_mb = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5"))

        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL", "sqlite:///career_match.db"
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.MAX_CONTENT_LENGTH = max_content_length_mb * 1024 * 1024
        self.ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "txt"}
        self.TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "")
        self.TINYFISH_BASE_URL = os.getenv(
            "TINYFISH_BASE_URL", "https://agent.tinyfish.ai"
        ).rstrip("/")
        self.TINYFISH_API_TIMEOUT_SECONDS = int(
            os.getenv("TINYFISH_API_TIMEOUT_SECONDS", "60")
        )
        self.TINYFISH_DEFAULT_BROWSER_PROFILE = os.getenv(
            "TINYFISH_DEFAULT_BROWSER_PROFILE", "lite"
        )
        self.TINYFISH_DEFAULT_PROXY_ENABLED = (
            os.getenv("TINYFISH_DEFAULT_PROXY_ENABLED", "false").lower() == "true"
        )
        self.TINYFISH_DEFAULT_PROXY_COUNTRY_CODE = os.getenv(
            "TINYFISH_DEFAULT_PROXY_COUNTRY_CODE", "US"
        )
