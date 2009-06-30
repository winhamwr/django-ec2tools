from django.conf import settings

ACCESS_KEY_ID = getattr(settings, 'EC2_AWS_ACCESS_KEY', None)
SECRET_ACCESS_KEY = getattr(settings, 'EC2_AWS_SECRET_KEY', None)