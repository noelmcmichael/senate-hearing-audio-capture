"""
Production configuration for Senate Hearing Audio Capture
"""

import os
from typing import Optional

class ProductionConfig:
    """Production configuration settings"""
    
    # Environment
    ENV = os.getenv('ENV', 'production')
    DEBUG = False
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '20'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '30'))
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL')
    REDIS_PREFIX = os.getenv('REDIS_PREFIX', 'senate_hearing')
    REDIS_TTL = int(os.getenv('REDIS_TTL', '3600'))
    
    # Google Cloud Storage
    AUDIO_BUCKET = os.getenv('AUDIO_BUCKET')
    BACKUP_BUCKET = os.getenv('BACKUP_BUCKET')
    
    # API Keys (from Secret Manager)
    CONGRESS_API_KEY = os.getenv('CONGRESS_API_KEY')
    
    # Processing Settings
    MAX_CONCURRENT_PROCESSING = int(os.getenv('MAX_CONCURRENT_PROCESSING', '5'))
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', '3600'))
    
    # Monitoring
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # Feature Flags
    ENABLE_VOICE_RECOGNITION = os.getenv('ENABLE_VOICE_RECOGNITION', 'true').lower() == 'true'
    ENABLE_AUTOMATED_PROCESSING = os.getenv('ENABLE_AUTOMATED_PROCESSING', 'true').lower() == 'true'
    ENABLE_LEARNING_SYSTEM = os.getenv('ENABLE_LEARNING_SYSTEM', 'true').lower() == 'true'
    
    # Performance
    WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', '1'))
    WORKER_THREADS = int(os.getenv('WORKER_THREADS', '4'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'AUDIO_BUCKET',
            'CONGRESS_API_KEY',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
                
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
            
        return True
    
    @classmethod
    def get_database_config(cls) -> dict:
        """Get database configuration"""
        return {
            'url': cls.DATABASE_URL,
            'pool_size': cls.DATABASE_POOL_SIZE,
            'max_overflow': cls.DATABASE_MAX_OVERFLOW,
            'echo': False
        }
        
    @classmethod
    def get_redis_config(cls) -> dict:
        """Get Redis configuration"""
        return {
            'url': cls.REDIS_URL,
            'prefix': cls.REDIS_PREFIX,
            'ttl': cls.REDIS_TTL
        }
        
    @classmethod
    def get_storage_config(cls) -> dict:
        """Get storage configuration"""
        return {
            'audio_bucket': cls.AUDIO_BUCKET,
            'backup_bucket': cls.BACKUP_BUCKET
        }
        
    @classmethod
    def get_processing_config(cls) -> dict:
        """Get processing configuration"""
        return {
            'max_concurrent': cls.MAX_CONCURRENT_PROCESSING,
            'timeout': cls.PROCESSING_TIMEOUT,
            'enable_voice_recognition': cls.ENABLE_VOICE_RECOGNITION,
            'enable_automated_processing': cls.ENABLE_AUTOMATED_PROCESSING,
            'enable_learning_system': cls.ENABLE_LEARNING_SYSTEM
        }
        
    @classmethod
    def get_monitoring_config(cls) -> dict:
        """Get monitoring configuration"""
        return {
            'enabled': cls.MONITORING_ENABLED,
            'sentry_dsn': cls.SENTRY_DSN,
            'log_level': cls.LOG_LEVEL,
            'log_format': cls.LOG_FORMAT
        }

# Initialize configuration
config = ProductionConfig()

# Validate configuration on import
try:
    config.validate()
except ValueError as e:
    print(f"Configuration validation failed: {e}")
    # In production, you might want to exit here
    # sys.exit(1)