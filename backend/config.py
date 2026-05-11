"""
Configuration settings for the India Multi-Disease Epidemiology Framework backend.
"""
import os

class Config:
    """Base configuration."""
    DEBUG = False
    TESTING = False
    
    # Base paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data_processed")
    
    # API settings
    API_PREFIX = "/api"
    
    # Supported diseases
    SUPPORTED_DISEASES = ["covid", "dengue", "malaria", "idsp"]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
