DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROJECT_HOME = '/home/tristan/projects/hydrant'
MEDIA_ROOT = PROJECT_HOME + '/media'

SECRET_KEY = 'j9ccpcmbvu*8=+r9nuj#3r)vvfvv@@ha@+=3$zaw89&luzw%j%'

DATABASE_ENGINE = 'postgresql_zxjdbc'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = PROJECT_HOME + '/db/testing.db'     # Or path to database file if using sqlite3.
DATABASE_NAME = 'kepler'
DATABASE_USER = 'kepler'             # Not used with sqlite3.
DATABASE_PASSWORD = 'k3pl3r'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

#TIME_ZONE = 'Brisbane/Australia'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'jython.kepler'
)

TEMPLATE_DIRS = (
    PROJECT_HOME + '/templates/',
)

ROOT_URL = ''
MEDIA_URL = '/' + ROOT_URL + 'media/'

LIB_DIRECTORY = PROJECT_HOME + '/lib'
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'
ROOT_URLCONF = 'jython.urls'

STORAGE_ROOT = PROJECT_HOME + '/storage'
