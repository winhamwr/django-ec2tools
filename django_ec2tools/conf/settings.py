import datetime

from django.conf import settings

from django_ec2tools.pruning_strategy import PruneByAge

ACCESS_KEY_ID = getattr(settings, 'EC2_AWS_ACCESS_KEY', None)
SECRET_ACCESS_KEY = getattr(settings, 'EC2_AWS_SECRET_KEY', None)

DATABASE_BACKUP_USER = getattr(settings, 'DATABASE_BACKUP_USER', settings.DATABASE_USER)
DATABASE_BACKUP_PASSWORD = getattr(settings, 'DATABASE_BACKUP_PASSWORD', settings.DATABASE_PASSWORD)

XFS_FREEZE_CMD = getattr(settings, 'XFS_FREEZE_CMD', '/usr/sbin/xfs_freeze')

MAX_SNAPSHOT_AGE = getattr(settings, 'EC2_MAX_SNAPSHOT_AGE', datetime.timedelta(2)) # 2 days
DEFAULT_PRUNE_STRATEGY = getattr(settings, 'EC2_DEFAULT_PRUNE_STRATEGY', PruneByAge(MAX_SNAPSHOT_AGE))

# The module from which all command-line and config strategies will be imported
PRUNE_STRATEGY_MODULE = getattr(settings, 'EC2_PRUNE_STRATEGY_MODULE', 'django_ec2tools.pruning_strategy')