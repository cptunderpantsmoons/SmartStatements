"""
Request and response models for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import os
from pathlib import Path


class ProcessRequest(BaseModel):
    """Request model for file processing"""
    file_path: str = Field(..., description="Path to the input file")
    user_id: str = Field(..., description="User ID for tracking")
    year: int = Field(default=2025, ge=2000, le=2100, description="Financial year")

    @validator('file_path')
    def validate_file_path(cls, v):
        """Validate that file exists and is supported type"""
        if not os.path.exists(v):
            raise ValueError(f'File does not exist: {v}')
        
        supported_types = {'.pdf', '.xlsx', '.xls'}
        file_ext = Path(v).suffix.lower()
        if file_ext not in supported_types:
            raise ValueError(f'Unsupported file type: {file_ext}. Supported: {supported_types}')
        
        # Check file size (50MB limit)
        file_size_mb = os.path.getsize(v) / (1024 * 1024)
        if file_size_mb > 50:
            raise ValueError(f'File too large: {file_size_mb:.2f}MB (max 50MB)')
        
        return v

    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format"""
        if not v or len(v) < 1:
            raise ValueError('user_id cannot be empty')
        if len(v) > 255:
            raise ValueError('user_id too long (max 255 characters)')
        return v

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "file_path": "/path/to/file.pdf",
                "user_id": "user-uuid-123",
                "year": 2025
            }
        }


class ProcessResponse(BaseModel):
    """Response model for processing"""
    status: str = Field(..., description="Processing status")
    report_id: Optional[str] = Field(None, description="Report ID")
    processing_time_seconds: float = Field(..., description="Time taken to process")
    statements_file: Optional[str] = Field(None, description="Path to generated statements")
    certificate_file: Optional[str] = Field(None, description="Path to certificate")
    qa_report: Optional[Dict[str, Any]] = Field(None, description="QA audit results")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "status": "success",
                "report_id": "123e4567-e89b-12d3-a456-426614174000",
                "processing_time_seconds": 120.5,
                "statements_file": "/output/2025_Final.xlsx",
                "certificate_file": "/output/verification_certificate.html",
                "qa_report": {"overall_status": "PASS", "overall_score": 95}
            }
        }


class StatusRequest(BaseModel):
    """Request model for status check"""
    report_id: str = Field(..., description="Report ID to check")

    @validator('report_id')
    def validate_report_id(cls, v):
        """Validate report ID format"""
        if not v or len(v) < 1:
            raise ValueError('report_id cannot be empty')
        return v


class StatusResponse(BaseModel):
    """Response model for status check"""
    report_id: str = Field(..., description="Report ID")
    status: str = Field(..., description="Current status")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    overall_score: Optional[float] = Field(None, description="QA score if available")
    error_message: Optional[str] = Field(None, description="Error if failed")

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "report_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "progress": 50
            }
        }


class ReportsResponse(BaseModel):
    """Response model for user reports"""
    reports: List[Dict[str, Any]] = Field(..., description="List of reports")
    total_count: int = Field(..., description="Total number of reports")
    completed_count: int = Field(..., description="Number of completed reports")
    failed_count: int = Field(..., description="Number of failed reports")

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "reports": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "year": 2025,
                        "status": "completed",
                        "overall_score": 95
                    }
                ],
                "total_count": 1,
                "completed_count": 1,
                "failed_count": 0
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO timestamp")

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "error": "File not found",
                "details": "/path/to/file.pdf does not exist",
                "timestamp": "2025-11-05T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="ISO timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")

    class Config:
        schema_extra: Dict[str, Any] = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-05T10:30:00Z",
                "services": {
                    "database": "operational",
                    "ai_models": "operational",
                    "cache": "operational"
                }
            }
        }
