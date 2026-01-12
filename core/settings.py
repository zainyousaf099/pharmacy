
from pathlib import Path
import os
import sys
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent

# For packaged app, use a writable location for database
def get_database_path():
    # Check if running as packaged app (in Program Files or similar)
    if getattr(sys, 'frozen', False) or 'Program Files' in str(BASE_DIR) or 'resources' in str(BASE_DIR):
        # Use AppData folder for database (writable location)
        app_data = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
        db_folder = app_data / 'ClinicManagement'
        db_folder.mkdir(parents=True, exist_ok=True)
        db_path = db_folder / 'db.sqlite3'
        
        # Copy original database if it doesn't exist in AppData
        original_db = BASE_DIR / 'db.sqlite3'
        if not db_path.exists() and original_db.exists():
            shutil.copy2(original_db, db_path)
        
        return db_path
    else:
        # Development mode - use local database
        return BASE_DIR / 'db.sqlite3'

DATABASE_PATH = get_database_path()

SECRET_KEY = 'django-insecure-j548s$)v4@&*jzfqtjj-sd)f$k_8ylrbd4-w)j9b5wws%cvg83'

DEBUG = True

# Allow access from local network (LAN)
ALLOWED_HOSTS = ['*']  # Allows all IPs (for local network only)
# Alternative: ALLOWED_HOSTS = ['192.168.1.*', '192.168.0.*', 'localhost', '127.0.0.1']



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'accounts',
    'doctor',
    'opd',
    'pharmacy',
    'admission',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates',],
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

WSGI_APPLICATION = 'core.wsgi.application'




DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_PATH,
    }
}



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




LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



import os
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), 
]



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "newsite" / "media"

X_FRAME_OPTIONS = 'SAMEORIGIN'
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
