"""
Configuration file for Overton Analyzer Web Application
"""

import os

class Config:
    # API Keys
    OVERTON_API_KEY = os.environ.get('OVERTON_API_KEY', '')

    # API Endpoints
    OVERTON_BASE_URL = 'https://api.overton.io'
    OPENALEX_BASE_URL = 'https://api.openalex.org'

    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = True

    # Data Settings
    MAX_RESULTS = 500
    DEFAULT_QUERY = 'agent based models'

    # Export Settings
    REPORTS_DIR = 'reports'
    DATA_DIR = 'data'

    # Analysis Settings
    MIN_CITATIONS = 1
    NETWORK_MIN_CONNECTIONS = 2
    TOP_N_RESULTS = 50

    # Sector Categories
    SECTORS = {
        'think_tank': 'Think Tanks',
        'government': 'Government',
        'academia': 'Academia',
        'private': 'Private Sector',
        'ngo': 'NGO',
        'international': 'International Organizations'
    }
