from pathlib import Path
import os
 
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "django-insecure-schimba-aceasta-cheie-la-productie"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "Atelier_Ciocolata.apps.AtelierCiocolataConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # LAB 1,8;   LAB 2,2 IP și jurnalul accesărilor.
    "Atelier_Ciocolata.middleware.AccesariMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        # LAB 2, TASK 2, SUBPUNCTUL 6: datele firmei disponibile în toate template-urile.
        "Atelier_Ciocolata.context_processors.company_context",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

# LAB 3, 2: PostgreSQL este baza de date implicită.
# Variabilele de mediu pot înlocui datele de conectare fără modificarea codului.
# Pentru testare locală fără PostgreSQL: DB_ENGINE=sqlite.
DATABASES ={ 
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "2026",
        "USER": "vlad",
        "PASSWORD": "vlad",
        "HOST": "localhost",
        "PORT": "5432",
    }
}    
LANGUAGE_CODE = "ro"
TIME_ZONE = "Europe/Bucharest"
USE_I18N = True
USE_TZ = True

# LAB 2, TASK 2,  5 și 8: resurse statice și upload-uri.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LAB 2, TASK 2, SUBPUNCTUL 6: datele firmei trimise de context processor.
COMPANY_INFO = {
    "nume": "Atelierul de Ciocolată ",
    "an_infiintare": 2026,
    "telefon": "0773 746 728",
    "adresa": " Focșani, România",
    "slogan": "Bucurie în fiecare bucățică",
    "email": "vladnita777@gmail.com",
}
