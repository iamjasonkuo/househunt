import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-sauce'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    POSTS_PER_PAGE = 25
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    UPLOADED_PHOTOS_DEST = os.getcwd()
    ZWSID = os.environ.get('ZWSID')
    GOOGLEMAPS_KEY = os.environ.get('GOOGLEMAPS_KEY')
    GOOGLEMAPS_GEOCODING_KEY = os.environ.get('GOOGLEMAPS_GEOCODING_KEY')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
    S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET_NAME)
    AWS_USERNAME = os.environ.get('AWS_USERNAME')
    AWS_PASSWORD = os.environ.get('AWS_PASSWORD')
    FLASKS3_BUCKET_NAME = os.environ.get('FLASKS3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    UPLOADED_PATH = os.path.join(basedir, 'app/static/uploads')
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_PARALLEL_UPLOADS = 3
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = 'image/*, .pdf'
    # DROPZONE_REDIRECT_VIEW = 'results'
    DEBUG = True
    PORT = 5000
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
