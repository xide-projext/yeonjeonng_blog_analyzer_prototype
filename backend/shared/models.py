"""
Shared data models for Blog SEO Analyzer.

This module contains Pydantic models used across different services.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, validator


class BlogPostBase(BaseModel):
    """Base blog post model."""
    
    url: HttpUrl
    title: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    platform: Optional[str] = None
    language: str = "ko"


class BlogPostCreate(BlogPostBase):
    """Blog post creation model."""
    pass


class BlogPostInDB(BlogPostBase):
    """Blog post database model."""
    
    id: UUID
    status: str = "pending"
    crawled_at: datetime
    user_id: Optional[UUID] = None

    class Config:
        orm_mode = True


class BlogPost(BlogPostInDB):
    """Blog post response model."""
    pass


class SEOAnalysisBase(BaseModel):
    """Base SEO analysis model."""
    
    overall_score: Optional[int] = None
    keyword_density: Optional[Dict[str, Any]] = None
    meta_score: Optional[int] = None
    heading_structure: Optional[Dict[str, Any]] = None
    link_analysis: Optional[Dict[str, Any]] = None
    image_optimization: Optional[Dict[str, Any]] = None
    readability_score: Optional[float] = None
    technical_seo: Optional[Dict[str, Any]] = None

    @validator('overall_score')
    def validate_score(cls, v):
        """Validate overall score is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Overall score must be between 0 and 100')
        return v


class SEOAnalysisCreate(SEOAnalysisBase):
    """SEO analysis creation model."""
    blog_post_id: UUID


class SEOAnalysisInDB(SEOAnalysisBase):
    """SEO analysis database model."""
    
    id: UUID
    blog_post_id: UUID
    analyzed_at: datetime

    class Config:
        orm_mode = True


class SEOAnalysis(SEOAnalysisInDB):
    """SEO analysis response model."""
    pass


class NLPAnalysisBase(BaseModel):
    """Base NLP analysis model."""
    
    keywords: Optional[Dict[str, Any]] = None
    topics: Optional[Dict[str, Any]] = None
    sentiment_score: Optional[float] = None
    tone_analysis: Optional[Dict[str, Any]] = None
    entity_extraction: Optional[Dict[str, Any]] = None
    language_quality: Optional[Dict[str, Any]] = None

    @validator('sentiment_score')
    def validate_sentiment(cls, v):
        """Validate sentiment score is between -1 and 1."""
        if v is not None and (v < -1 or v > 1):
            raise ValueError('Sentiment score must be between -1 and 1')
        return v


class NLPAnalysisCreate(NLPAnalysisBase):
    """NLP analysis creation model."""
    blog_post_id: UUID


class NLPAnalysisInDB(NLPAnalysisBase):
    """NLP analysis database model."""
    
    id: UUID
    blog_post_id: UUID
    analyzed_at: datetime

    class Config:
        orm_mode = True


class NLPAnalysis(NLPAnalysisInDB):
    """NLP analysis response model."""
    pass


class CompetitionAnalysisBase(BaseModel):
    """Base competition analysis model."""
    
    competitor_urls: Optional[List[str]] = None
    keyword_overlap: Optional[Dict[str, Any]] = None
    content_gaps: Optional[Dict[str, Any]] = None
    ranking_potential: Optional[Dict[str, Any]] = None


class CompetitionAnalysisCreate(CompetitionAnalysisBase):
    """Competition analysis creation model."""
    blog_post_id: UUID


class CompetitionAnalysisInDB(CompetitionAnalysisBase):
    """Competition analysis database model."""
    
    id: UUID
    blog_post_id: UUID
    analyzed_at: datetime

    class Config:
        orm_mode = True


class CompetitionAnalysis(CompetitionAnalysisInDB):
    """Competition analysis response model."""
    pass


class AnalysisJobBase(BaseModel):
    """Base analysis job model."""
    
    job_type: str
    status: str = "pending"
    progress: int = 0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class AnalysisJobCreate(AnalysisJobBase):
    """Analysis job creation model."""
    blog_post_id: UUID


class AnalysisJobInDB(AnalysisJobBase):
    """Analysis job database model."""
    
    id: UUID
    blog_post_id: UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True


class AnalysisJob(AnalysisJobInDB):
    """Analysis job response model."""
    pass


class CrawlResult(BaseModel):
    """Crawling result model."""
    
    url: str
    success: bool
    status_code: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    platform: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None


class AnalysisRequest(BaseModel):
    """Analysis request model."""
    
    url: HttpUrl
    analysis_types: List[str] = ["seo", "nlp"]  # Default analyses
    priority: int = 1  # 1 = high, 2 = medium, 3 = low

    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        """Validate analysis types."""
        valid_types = {"seo", "nlp", "competition", "all"}
        if not all(t in valid_types for t in v):
            raise ValueError(f'Invalid analysis types. Valid types: {valid_types}')
        return v


class AnalysisResponse(BaseModel):
    """Comprehensive analysis response model."""
    
    blog_post: BlogPost
    seo_analysis: Optional[SEOAnalysis] = None
    nlp_analysis: Optional[NLPAnalysis] = None
    competition_analysis: Optional[CompetitionAnalysis] = None
    analysis_jobs: List[AnalysisJob] = []


class UserBase(BaseModel):
    """Base user model."""
    
    email: str
    username: str
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserInDB(UserBase):
    """User database model."""
    
    id: UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class User(UserBase):
    """User response model."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Authentication token model."""
    
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload model."""
    
    sub: Optional[str] = None
    exp: Optional[int] = None 