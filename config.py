# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jayanthan$2005',
    'database': 'resume_analyzer',
    'auth_plugin': 'mysql_native_password'
}

# Application configuration
APP_CONFIG = {
    'SECRET_KEY': 'your-secret-key-here',
    'UPLOAD_FOLDER': 'static/uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max file size
}
