import os
import sys
from ragendja.settings_pre import *

DEBUG=True

# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
MEDIA_VERSION = 1

ROOT_URLCONF = 'urls'  # Replace 'project.urls' with just 'urls'

DATABASE_ENGINE = 'appengine'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'ragendja.auth.middleware.GoogleAuthenticationMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
)

# Change the User model class
AUTH_USER_MODULE = 'app.models'
#LOGIN_REDIRECT_URL = '/'
AUTH_ADMIN_USER_AS_SUPERUSER = True

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'appenginepatcher',
    #'django.contrib.admin',
)

ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (
    ROOT_PATH + '/app/templates',
)
# add the lib dir to the system path, so we can import
sys.path.append(ROOT_PATH + '/lib')

SECRET_KEY = 'AABCDGFS'

from ragendja.settings_post import *
