import os
from pathlib import Path
# from decouple import config
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into os.environ

DEBUG=True

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')


SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'storages',
    'core.apps.CoreConfig',  # Your main app
    # 'jobs.apps.JobsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hrms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hrms.wsgi.application'
# test
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'hrms_dev_91q0',
#         'USER': 'hrms_dev_91q0_user',
#         'PASSWORD': 'InIQXkg0mNUQuRrMrqTPjbfcuyAMc9Ee',
#         'HOST': 'dpg-d45nqruuk2gs73cmgn90-a.oregon-postgres.render.com',
#         'PORT': '5432',
#     }
# }

# main
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hrms_dev_7gpj',
        'USER': 'hrms_admin',
        'PASSWORD': '0JHxTlQTHD4POkp2upQQ3n5oz0SD5mw1',
        'HOST': 'dpg-d398h57fte5s73cktr0g-a.oregon-postgres.render.com',
        'PORT': '5432',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#     }
# }

# Cache setup (using default local memory or Redis in production)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-fallback-secret-key'







import os
from datetime import timedelta

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),  # 8 hour work day
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M:%S',
    'DATE_FORMAT': '%d/%m/%Y',
    'TIME_FORMAT': '%H:%M:%S',
}

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),
]



# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'manpower.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'hrms': {
            'handlers': ['console'],
            'propagate': True,
        },
        'manpower': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Session Configuration
SESSION_COOKIE_AGE = 28800  # 8 hours (work day)
SESSION_COOKIE_NAME = 'manpower_sessionid'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS Configuration (if using React/Vue frontend)
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only for development

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://localhost:8081",
    "http://localhost:8080"
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'client-id',  # Custom header for client profile
]

# Custom Application Settings
MANPOWER_SETTINGS = {
    'AUTO_GENERATE_EMPLOYEE_CODE': True,
    'DEFAULT_WEEKLY_OFF_DAY': 6,  # Saturday
    'DEFAULT_WORKING_HOURS_PER_DAY': 8,
    'OVERTIME_MULTIPLIER': 2.0,
    'PAYROLL_LOCK_DAYS': 3,  # Lock payroll after 3 days
    'ATTENDANCE_ENTRY_CUTOFF_DAYS': 5,  # Can enter attendance up to 5 days back
    'DEFAULT_PROBATION_PERIOD_MONTHS': 6,
    'ESI_CEILING_AMOUNT': 25000,
    'PF_CEILING_AMOUNT': 15000,
    'SUPPORTED_DOCUMENT_FORMATS': ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
    'MAX_DOCUMENT_SIZE_MB': 5,
    'ACTIVITY_LOG_RETENTION_MONTHS': 6,
    'BACKUP_RETENTION_DAYS': 30,
}

# Font Settings for PDF Generation
FONT_SETTINGS = {
    'DEFAULT_FONT': 'Bookman Old Style',
    'DEFAULT_FONT_SIZE': 10,
    'HEADER_FONT_SIZE': 14,
    'TITLE_FONT_SIZE': 16,
    'FONT_PATH': os.path.join(BASE_DIR, 'fonts'),
}

# Report Generation Settings
REPORT_SETTINGS = {
    'DEFAULT_PAGE_SIZE': 'A4',
    'DEFAULT_MARGINS': {
        'top': 72,
        'bottom': 18,
        'left': 72,
        'right': 72,
    },
    'EXCEL_SHEET_MAX_ROWS': 50000,
    'PDF_MAX_RECORDS_PER_PAGE': 30,
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'generate-monthly-reports': {
        'task': 'manpower.tasks.generate_monthly_reports',
        'schedule': 30.0,  # Every 30 seconds (adjust as needed)
    },
    'send-pending-payslips': {
        'task': 'manpower.tasks.send_pending_payslips',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-logs': {
        'task': 'manpower.tasks.cleanup_old_activity_logs',
        'schedule': 86400.0,  # Daily
    },
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'manpower',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# WhatsApp Integration Settings (if using)
WHATSAPP_SETTINGS = {
    'API_URL': 'https://api.whatsapp.com/send',
    'BUSINESS_PHONE': '+91XXXXXXXXXX',
    'API_TOKEN': 'your-whatsapp-business-api-token',
}

# Backup Settings
BACKUP_SETTINGS = {
    'BACKUP_PATH': os.path.join(BASE_DIR, 'backups'),
    'AUTO_BACKUP': True,
    'BACKUP_SCHEDULE': 'daily',  # daily, weekly, monthly
    'BACKUP_RETENTION_DAYS': 30,
    'BACKUP_DATABASE': True,
    'BACKUP_MEDIA': True,
}

# Audit Trail Settings
AUDIT_SETTINGS = {
    'ENABLE_AUDIT_LOG': True,
    'LOG_USER_ACTIONS': True,
    'LOG_DATA_CHANGES': True,
    'LOG_LOGIN_ATTEMPTS': True,
    'RETENTION_PERIOD_MONTHS': 6,
}

# Notification Settings
NOTIFICATION_SETTINGS = {
    'EMAIL_NOTIFICATIONS': True,
    'WHATSAPP_NOTIFICATIONS': True,
    'SMS_NOTIFICATIONS': False,
    'NOTIFICATION_TEMPLATES_PATH': os.path.join(BASE_DIR, 'templates', 'notifications'),
}

# Role-based Access Control
RBAC_SETTINGS = {
    'ENABLE_ROLE_BASED_ACCESS': True,
    'DEFAULT_ROLES': ['Admin', 'HR', 'Supervisor', 'Employee'],
    'ROLE_PERMISSIONS': {
        'Admin': ['*'],  # All permissions
        'HR': [
            'view_employee', 'add_employee', 'change_employee',
            'view_attendance', 'change_attendance',
            'view_payroll', 'add_payroll', 'change_payroll',
            'view_reports', 'generate_reports',
        ],
        'Supervisor': [
            'view_employee', 'view_attendance', 'add_attendance', 'change_attendance',
        ],
        'Employee': [
            'view_own_data', 'view_own_payslip', 'view_own_attendance',
        ],
    },
}

# Performance Settings
DATABASE_SETTINGS = {
    'CONNECTION_MAX_AGE': 600,  # 10 minutes
    'CONN_MAX_AGE': 0,
    'OPTIONS': {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    },
}

# Development/Production Environment Detection
if DEBUG:
    # Development settings
    CORS_ALLOW_ALL_ORIGINS = True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in development
else:
    # Production settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
