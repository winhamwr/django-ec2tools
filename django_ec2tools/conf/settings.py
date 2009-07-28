from django.conf import settings

ACCESS_KEY_ID = getattr(settings, 'EC2_AWS_ACCESS_KEY', None)
SECRET_ACCESS_KEY = getattr(settings, 'EC2_AWS_SECRET_KEY', None)

DATABASE_BACKUP_USER = getattr(settings, 'DATABASE_BACKUP_USER', settings.DATABASE_USER)
DATABASE_BACKUP_PASSWORD = getattr(settings, 'DATABASE_BACKUP_PASSWORD', settings.DATABASE_PASSWORD)

XFS_FREEZE_CMD = getattr(settings, 'XFS_FREEZE_CMD', '/usr/sbin/xfs_freeze')