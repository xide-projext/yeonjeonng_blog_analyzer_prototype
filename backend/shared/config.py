"""
Configuration management for Blog SEO Analyzer.

This module handles all configuration settings with type hints and validation.
"""

import os
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    LOG_LEVEL: str = "info"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "blog_seo_analyzer"
    DATABASE_USER: str = "blog_seo"
    DATABASE_PASSWORD: str

    # Redis
    REDIS_URL: RedisDsn
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: RedisDsn
    CELERY_RESULT_BACKEND: RedisDsn

    # Crawling
    USER_AGENT: str = "BlogSEOAnalyzer/1.0"
    REQUEST_DELAY: float = 1.0
    CONCURRENT_REQUESTS: int = 16
    DOWNLOAD_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # NLP Models
    NLP_MODELS_PATH: str = "./models"
    SPACY_MODEL: str = "ko_core_news_sm"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090

    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None

    # Environment
    ENVIRONMENT: str = "development"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


class CrawlingSettings:
    """Crawling-specific settings and configurations."""

    # Platform-specific selectors
    PLATFORM_SELECTORS = {
        "naver": {
            "title": "h3.se_title, .se-title-text",
            "content": ".se-main-container, .se-component",
            "meta_description": "meta[name='description']",
            "author": ".nick, .blog_nick",
            "date": ".se-date, .blog_date"
        },
        "tistory": {
            "title": "h1.entry-title, .article-header h1",
            "content": ".entry-content, .article-view",
            "meta_description": "meta[name='description']",
            "author": ".author, .writer",
            "date": ".article-date, .published"
        },
        "wordpress": {
            "title": "h1.entry-title, .wp-block-post-title",
            "content": ".entry-content, .wp-block-post-content",
            "meta_description": "meta[name='description']",
            "author": ".author, .wp-block-post-author",
            "date": ".entry-date, .wp-block-post-date"
        },
        "medium": {
            "title": "h1, article h1",
            "content": "article section, .postArticle-content",
            "meta_description": "meta[name='description']",
            "author": ".postMetaInline a, .author",
            "date": ".date, time"
        },
        "brunch": {
            "title": ".wrap_title h1",
            "content": ".wrap_body",
            "meta_description": "meta[name='description']",
            "author": ".by_author",
            "date": ".wrap_date"
        }
    }

    # Headers for different platforms
    HEADERS = {
        "User-Agent": "BlogSEOAnalyzer/1.0 (+https://github.com/blog-seo-analyzer)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    # Rate limiting settings per platform
    RATE_LIMITS = {
        "naver": {"delay": 2.0, "concurrent": 5},
        "tistory": {"delay": 1.0, "concurrent": 10},
        "wordpress": {"delay": 0.5, "concurrent": 20},
        "medium": {"delay": 1.5, "concurrent": 8},
        "brunch": {"delay": 2.0, "concurrent": 5}
    }


# Global settings instance
settings = Settings()
crawling_settings = CrawlingSettings() 