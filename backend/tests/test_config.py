"""
Tests for configuration module
"""
import pytest
from config.settings import Config


def test_config_initialization_no_validation():
    """Test that config initializes without errors when validation is disabled"""
    config = Config(validate_on_init=False)
    assert config is not None
    assert config.validate_on_init is False


def test_config_default_values():
    """Test that config has correct default values"""
    config = Config(validate_on_init=False)
    
    assert config.max_workers == 4
    assert config.pdf_dpi == 300
    assert config.cache_ttl_hours == 1
    assert config.max_file_size_mb == 50
    assert config.max_pages_per_pdf == 100
    assert config.auto_map_threshold == 0.85
    assert config.review_threshold == 0.7


def test_config_validate_method_missing_keys():
    """Test that validate method raises error on missing keys"""
    config = Config(validate_on_init=False)
    
    # All keys are empty, so validate() should raise
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        config.validate()


def test_config_model_names():
    """Test that config has correct model names"""
    config = Config(validate_on_init=False)
    
    assert config.gemini_pro_model == "gemini-2.5-pro"
    assert config.gemini_flash_model == "gemini-2.5-flash"
    assert config.grok_model == "x-ai/grok-4-fast"


def test_config_directories():
    """Test that config has correct directory paths"""
    config = Config(validate_on_init=False)
    
    assert config.input_directory == "./input"
    assert config.output_directory == "./output"


def test_config_thresholds_in_valid_range():
    """Test that thresholds are in valid range [0, 1]"""
    config = Config(validate_on_init=False)
    
    assert 0 <= config.auto_map_threshold <= 1
    assert 0 <= config.review_threshold <= 1
    assert config.review_threshold < config.auto_map_threshold
