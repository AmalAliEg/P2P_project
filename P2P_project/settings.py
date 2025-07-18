# P2P_project/settings.py

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# 1. Path Configuration and Environment Variables (.env)
#==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root directory
dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path)


# 2. Core Settings and Security
# ==============================================================================
# Always read SECRET_KEY from .env file
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-secret-key-for-development')

# Read DEBUG state from .env, default to False for production
DEBUG = 'True'

# Read ALLOWED_HOSTS from .env
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# In DEBUG mode, allow all hosts for local development
if DEBUG:
    ALLOWED_HOSTS.append('*')


# 3.  (INSTALLED_APPS)
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'debug_toolbar',
    'corsheaders',
    'drf_yasg',

    # project app
    'p2p_trading.apps.P2PTradingConfig',
    'chat.apps.ChatConfig',
    'MainDashboard.apps.MaindashboardConfig',
]

# 4.  Middleware
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# CORS settings to allow Frontend access to API
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


# 5. URLs, Templates, and ASGI/WSGI Configuration
# ==============================================================================
ROOT_URLCONF = 'P2P_project.urls'
WSGI_APPLICATION = 'P2P_project.wsgi.application'

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


# 6. (Databases)
# ==============================================================================
DATABASES = {
    #main database for all P2P models
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
    # database for all chat models
    'chat_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('CHAT_DB_NAME'),
        'USER': os.environ.get('CHAT_DB_USER'),
        'PASSWORD': os.environ.get('CHAT_DB_PASSWORD'),
        'HOST': os.environ.get('CHAT_DB_HOST'),
        'PORT': os.environ.get('CHAT_DB_PORT', '5432'),
    },
    # database for all  main_dashboard models
    'main_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('MAIN_DB_NAME'),
        'USER': os.environ.get('MAIN_DB_USER'),
        'PASSWORD': os.environ.get('MAIN_DB_PASSWORD'),
        'HOST': os.environ.get('MAIN_DB_HOST'),
        'PORT': os.environ.get('MAIN_DB_PORT', '5432'),
    }
}

# Database router to direct chat models to their specific database
DATABASE_ROUTERS = ['P2P_project.routers.DatabaseRouter']



# ==============================================================================
# 7. Authentication Settings
AUTH_USER_MODEL = 'MainDashboard.MainUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # نعتمد على JWT القادم من الخدمة الرئيسية
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'

}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    # Most important: verification key must match the SECRET_KEY used in the main service for token creation
    'SIGNING_KEY': os.environ.get('MAIN_SERVICE_SECRET_KEY'),
    'VERIFYING_KEY': os.environ.get('MAIN_SERVICE_SECRET_KEY'),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}


# 8. Static file
# ==============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
# Password validation
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 9.  (Internationalization) setting
# ==============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# 10. إعدادات أخرى
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'