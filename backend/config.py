import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///flowspec.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # ExaBGP Configuration
    EXABGP_HOST = os.getenv('EXABGP_HOST', 'localhost')
    EXABGP_PORT = int(os.getenv('EXABGP_PORT', 6001))
    EXABGP_TIMEOUT = int(os.getenv('EXABGP_TIMEOUT', 5))
    
    # FastNetMon Configuration
    FASTNETMON_API_URL = os.getenv('FASTNETMON_API_URL', 'http://localhost:8080')
    FASTNETMON_ENABLED = os.getenv('FASTNETMON_ENABLED', 'false').lower() == 'true'
    
    # Rule Defaults
    DEFAULT_RULE_TTL_MINUTES = int(os.getenv('DEFAULT_RULE_TTL_MINUTES', 60))
    MAX_RULE_TTL_MINUTES = int(os.getenv('MAX_RULE_TTL_MINUTES', 1440))  # 24 hours
    
    # API Rate Limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true'
    RATELIMIT_RULES_PER_HOUR = int(os.getenv('RATELIMIT_RULES_PER_HOUR', 100))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
