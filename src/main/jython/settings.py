import os
import django

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_HTTPS = not DEBUG

PROJECT_HOME = os.getcwd()
MEDIA_ROOT = PROJECT_HOME + '/media'

SECRET_KEY = 'j9ccpcmbvu*8=+r9nuj#3r)vvfvv@@ha@+=3$zaw89&luzw%j%'

DATABASE_ENGINE = 'postgresql_zxjdbc'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = PROJECT_HOME + '/db/testing.db'     # Or path to database file if using sqlite3.
DATABASE_NAME = 'kepler'
DATABASE_USER = 'kepler'             # Not used with sqlite3.
DATABASE_PASSWORD = 'k3pl3r'         # Not used with sqlite3.
DATABASE_HOST = 'kepler.hpc.jcu.edu.au'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

SESSION_COOKIE_SECURE = USE_HTTPS

TIME_ZONE = 'Australia/Brisbane'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.ssl.SSLRedirect',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'jython.hydrant',
#    'jython.forum',
)

#FORUM_BASE = '/forum'

TEMPLATE_DIRS = (
    PROJECT_HOME + '/templates/',
)

ROOT_URL = 'hydrant/'
MEDIA_URL = '/' + ROOT_URL + 'media'

LIB_DIRECTORY = (
    PROJECT_HOME + '/lib',
    PROJECT_HOME + '/target/project.classpath',
    #'%s/lib/jar' % os.environ.get("KEPLER"),
    #'%s/lib' % os.environ.get("PTII"),
)

ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'
ADMIN_MEDIA_ROOT = '/'.join(django.__file__.split('/')[:-1]) + '/contrib/admin/media/'
ROOT_URLCONF = 'jython.urls'

STORAGE_ROOT = PROJECT_HOME + '/storage'

LOGIN_URL = '/' + ROOT_URL + 'accounts/login/'

AUTH_PROFILE_MODULE = 'hydrant.userprofile'
EMAIL_HOST = 'mail.cluster'
EMAIL_SUBJECT_PREFIX = '[hydrant] '
EMAIL_SYSTEM_ADDRESS = '' # none to use user's email address

#TRAC_URL = 'https://dev.archer.edu.au/projects/kepler/'
#TRAC_USER = ''
#TRAC_PASSWORD = ''
#JAVA_TRUSTSTORE = '%s/jssecacerts' % PROJECT_HOME

MAX_RUNNING_JOBS = 50
