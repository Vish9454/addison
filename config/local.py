"""
    file used to save the credentials used in the project it should not be push to git/bucket.
"""
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-#agc67*8zk%79cf#8emwclz4sldkww-ib@3)s4i#eh7#20y)!!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Allow Cors origin
CORS_ORIGIN_ALLOW_ALL = True

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'addison_db',
        'USER': 'addison_user',
        'PASSWORD': '123@addison',
        'HOST': 'localhost',
        # 'PORT': '5432',
    }
}

SQL_PRINT_STATEMENT = 'django_sqlprint_middleware.SqlPrintMiddleware'

# sendgrid connection (SMTP CONNECTION)
SEND_GRID_API_KEY = (
    "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"
)
FROM_EMAIL = "vishal.singh@algoworks.com"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = SEND_GRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# urls
forgotpassword_url = 'http://<>/reset-password/'
emailverification_url = 'http://<>/email-verify/'

# AWS Bucket Credentials to store documents
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ACCESS_KEY_ID = 'AKIAQD6NXIUMR3ZMKAMS'
AWS_S3_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'addison-dev-s3'
AWS_S3_REGION_NAME = 'us-east-1'

STRIPE_SECRET_KEY = "sk_test_51JWcjzB7uOZlweKjiRiv23lawmSbROniE2gQfSbeHSwTWCmNKvsG958SrY0Hj2Wx9lCRCqXOQbeXnlmd5TgKVhLn00yaNWHyWA"
STRIPE_PUBLISHABLE_KEY = "pk_test_51JWcjzB7uOZlweKjoWceaOMFhGi6Maf0d7BDkADyQ5WB5ZxI0dKNC2ptWFFa81aLw1zUjZroojp4KRfrCe2YoNBE003BWJ2P6U"
STRIPE_PROD_ID = "prod_KDuwvqESzOVhxM"

INAPP_IOS_SECRET_KEY = "eb51e20675c94a78b8e897c0af8ba70b"

FCM_SERVER_KEY = "AAAAr9eBIvU:APA91bEJsWddvX0cIhq6C3UmUNotgwnLb5qafCLu22ZWusOn5mTFblRpLSQD0W2Bjg0h9BVumUjsF0yDOzK1Q2hGDhdJ8gWBhIMHv4uFu3pUnXKRyq3urz9dwyKQhict_q50YzB6OnV2"
