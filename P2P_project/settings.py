# P2P_project/settings.py

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# 1. تحديد المسارات وتحميل متغيرات البيئة (.env)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# تحميل ملف .env من المجلد الرئيسي للمشروع
dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path)


# 2. الإعدادات الأساسية والأمان
# ==============================================================================
# اقرأ الـ SECRET_KEY من ملف .env دائماً
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-secret-key-for-development')

# اقرأ حالة الـ DEBUG من .env، واجعل القيمة الافتراضية False للـ production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# اقرأ الـ ALLOWED_HOSTS من .env
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# في حالة الـ DEBUG، اسمح بكل الـ hosts لتسهيل التطوير المحلي
if DEBUG:
    ALLOWED_HOSTS.append('*')


# 3. التطبيقات المثبتة (INSTALLED_APPS)
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
    'corsheaders', # مهم جداً للتواصل مع الـ Frontend

    # تطبيقات المشروع
    'p2p_trading.apps.P2PTradingConfig',
    'chat.apps.ChatConfig',
    'MainDashboard.apps.MaindashboardConfig',
]

# 4. الـ Middleware
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # يجب أن يكون في مكان متقدم
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# إعدادات CORS للسماح للـ Frontend بالوصول للـ API
CORS_ALLOW_ALL_ORIGINS = True # في التطوير. في الإنتاج، حدد الـ domain الخاص بالـ Frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


# 5. إعدادات الـ URLs والقوالب و ASGI/WSGI
# ==============================================================================
ROOT_URLCONF = 'P2P_project.urls'
WSGI_APPLICATION = 'P2P_project.wsgi.application'
#ASGI_APPLICATION = 'P2P_project.asgi.application' # مهم للشات و Django Channels

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


# 6. قواعد البيانات (Databases)
# ==============================================================================
DATABASES = {
    # قاعدة البيانات الرئيسية لكل موديلز الـ P2P
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
    # قاعدة بيانات منفصلة للشات (اختياري لكنه ممارسة جيدة)
    'chat_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('CHAT_DB_NAME'),
        'USER': os.environ.get('CHAT_DB_USER'),
        'PASSWORD': os.environ.get('CHAT_DB_PASSWORD'),
        'HOST': os.environ.get('CHAT_DB_HOST'),
        'PORT': os.environ.get('CHAT_DB_PORT', '5432'),
    },
    # قاعدة بيانات منفصلة main_dashboard (اختياري لكنه ممارسة جيدة)
    'main_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('MAIN_DB_NAME'),
        'USER': os.environ.get('MAIN_DB_USER'),
        'PASSWORD': os.environ.get('MAIN_DB_PASSWORD'),
        'HOST': os.environ.get('MAIN_DB_HOST'),
        'PORT': os.environ.get('MAIN_DB_PORT', '5432'),
    }
}

# موجه قواعد البيانات لتوجيه موديلز الشات إلى قاعدة البيانات الخاصة بها
DATABASE_ROUTERS = ['P2P_project.routers.DatabaseRouter']


# 7. إعدادات المصادقة (Authentication)
# ==============================================================================
# بما أن خدمة المستخدمين منفصلة، لا نحتاج لتحديد AUTH_USER_MODEL هنا
# المصادقة ستتم عبر API tokens يتم التحقق منها.
AUTH_USER_MODEL = 'MainDashboard.MainUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # نعتمد على JWT القادم من الخدمة الرئيسية
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# إعدادات JWT (يجب أن تتطابق مع إعدادات الخدمة الرئيسية)
# بما أن هذه الخدمة "تستهلك" الـ token ولا تنشئه، نحتاج فقط لمفتاح التحقق
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    # أهم جزء: مفتاح التحقق يجب أن يكون نفس الـ SECRET_KEY المستخدم في الخدمة الرئيسية لإنشاء الـ token
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


# 8. إعدادات الملفات (Static & Media)
# ==============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # مجلد لتجميع الملفات عند عمل collectstatic

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

# 9. إعدادات التدويل (Internationalization)
# ==============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# 10. إعدادات أخرى
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'