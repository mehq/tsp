from decouple import config

# A list of strings representing the host/domain names that this Django site
# can serve. This is a security measure to prevent HTTP Host header attacks
ALLOWED_HOSTS = [host for host in config("ALLOWED_HOSTS").split(",") if host]

# A boolean that turns on/off debug mode.
DEBUG = config("DEBUG", default=False, cast=bool)

# A list of strings designating all applications that are enabled in this
# project.
INSTALLED_APPS = [
    "tsp.apps.core",
]

# A list of middleware to use.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# A string representing the full Python import path to this project's root
# URLconf.
ROOT_URLCONF = "tsp.urls"

# A secret key for this project. This is used to provide cryptographic
# signing, and should be set to a unique, unpredictable value.
SECRET_KEY = config("SECRET_KEY")

# A string representing the time zone for this project.
TIME_ZONE = "UTC"

# A boolean that specifies if datetimes will be timezone-aware by default or
# not.
USE_TZ = True

# The full Python path of the WSGI application object that Django’s built-in
# servers (e.g. runserver) will use.
WSGI_APPLICATION = "tsp.wsgi.application"
