"""
Tests for API request/response models
"""
import pytest
from pydantic import ValidationError
from api.models import ProcessRequest, StatusRequest


def test_process_request_valid():
    """Test ProcessRequest with valid data"""
    req = ProcessRequest(
        file_path="/tmp/test.pdf",
        user_id="user123",
        year=2025
    )
    
    assert req.file_path == "/tmp/test.pdf"
    assert req.user_id == "user123"
    assert req.year == 2025


def test_process_request_default_year():
    """Test ProcessRequest with default year"""
    req = ProcessRequest(
        file_path="/tmp/test.pdf",
        user_id="user123"
    )
    
    assert req.year == 2025


def test_process_request_invalid_file_not_exists(tmp_path):
    """Test ProcessRequest with non-existent file"""
    with pytest.raises(ValidationError) as exc:
        ProcessRequest(
            file_path="/nonexistent/file.pdf",
            user_id="user123"
        )
    
    assert "File does not exist" in str(exc.value)


def test_process_request_invalid_file_type(tmp_path):
    """Test ProcessRequest with unsupported file type"""
    # Create a .txt file
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    with pytest.raises(ValidationError) as exc:
        ProcessRequest(
            file_path=str(test_file),
            user_id="user123"
        )
    
    assert "Unsupported file type" in str(exc.value)


def test_process_request_empty_user_id(tmp_path):
    """Test ProcessRequest with empty user_id"""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")
    
    with pytest.raises(ValidationError) as exc:
        ProcessRequest(
            file_path=str(test_file),
            user_id=""
        )
    
    assert "cannot be empty" in str(exc.value).lower()


def test_process_request_year_out_of_range(tmp_path):
    """Test ProcessRequest with year out of valid range"""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")
    
    with pytest.raises(ValidationError):
        ProcessRequest(
            file_path=str(test_file),
            user_id="user123",
            year=1999  # Too old
        )
    
    with pytest.raises(ValidationError):
        ProcessRequest(
            file_path=str(test_file),
            user_id="user123",
            year=2101  # Too far in future
        )


def test_status_request_valid():
    """Test StatusRequest with valid data"""
    req = StatusRequest(report_id="123e4567-e89b-12d3-a456-426614174000")
    
    assert req.report_id == "123e4567-e89b-12d3-a456-426614174000"


def test_status_request_empty_id():
    """Test StatusRequest with empty report_id"""
    with pytest.raises(ValidationError) as exc:
        StatusRequest(report_id="")
    
    assert "cannot be empty" in str(exc.value).lower()
