"""
Django settings for the Smart Ambulance Routing project.

HOW TO USE:
  - This is the central config file Django reads on startup.
  - SECRET_KEY must stay secret in production (doesn't matter for academic demo).
  - DEBUG=True shows detailed error pages — keep it True while developing.
  - INSTALLED_APPS tells Django which apps exist in this project.
  - CORS headers allow the browser to call our API from any origin.
"""

from pathlib import Path

# ── Base directory of the project (the folder containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Secret key — used by Django for security. Fine for academic use.
SECRET_KEY = 'django-insecure-ambulance-routing-daa-project-2024'

# ── Debug mode — shows error details in browser. Set False in production.
DEBUG = True

# ── Which hosts are allowed to serve the app. '*' = any host (fine for dev).
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
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

# ── URL configuration — tells Django where to find URL patterns
ROOT_URLCONF = 'ambulance_routing.urls'

# ── Template configuration — tells Django where to look for HTML files
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],           # We use app-level templates (core/templates/)
        'APP_DIRS': True,     # Django will look inside each app's templates/ folder
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── WSGI config (how Django talks to the web server — leave as default)
WSGI_APPLICATION = 'ambulance_routing.wsgi.application'

# ── Database — SQLite file stored in the project root
# We use this to store: Nodes, Edges, Hospitals, Ambulances, EmergencyRequests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Static files (CSS, JS) — where Django looks for them
STATIC_URL = '/static/'

# ── Default primary key type for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS settings — allow ALL origins to call our API
# This is needed so your HTML pages can call fetch('/api/...') without errors
CORS_ALLOW_ALL_ORIGINS = True

# ── Default: use UTC timezone
USE_TZ = True