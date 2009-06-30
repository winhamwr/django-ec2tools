from subprocess import call
import logging

from django_ec2tools.conf.settings import DATABASE_BACKUP_PASSWORD, DATABASE_BACKUP_USER
from django.conf import settings

def take_snapshot(ec2_conn, vol_id, freeze_dir, lock_db=True, fs='xfs'):
    """
    Take a snapshot of the given volume, handling the freezing and unfreezing
    of the file system and locking and unlocking the db (useful for
    non-transactional databases like MyISAM mysql).
    """
    if fs != 'xfs':
        raise NotImplementedError("Support for snapshots across file systems other than xfs not currently supported")

    if lock_db:
        try:
            from django.db import load_backend

            backend = load_backend(settings.DATABASE_ENGINE)
            connection = backend.DatabaseWrapper({
                'DATABASE_HOST': settings.DATABASE_HOST,
                'DATABASE_NAME': settings.DATABASE_NAME,
                'DATABASE_OPTIONS': settings.DATABASE_OPTIONS,
                'DATABASE_PASSWORD': DATABASE_BACKUP_PASSWORD,
                'DATABASE_PORT': settings.DATABASE_PORT,
                'DATABASE_USER': DATABASE_BACKUP_USER,
                'TIME_ZONE': settings.TIME_ZONE,
            })
        except ImportError:
            # Pre Django 1.1
            backend = __import__('django.db.backends.' + settings.DATABASE_ENGINE
                + ".base", {}, {}, ['base'])
            backup = {}
            # Save the 'real' db settings so we can restore them
            prev_user = settings.DATABASE_USER
            prev_pw = settings.DATABASE_PASSWORD
            settings.DATABASE_USER = DATABASE_BACKUP_USER
            settings.DATABASE_PASSWORD = DATABASE_BACKUP_PASSWORD

            connection = backend.DatabaseWrapper()
            connection._cursor(settings)

            # Restore the db settings
            settings.DATABASE_USER = prev_user
            settings.DATABASE_PASSWORD = prev_pw


        cursor = connection.cursor()
        cursor.execute('FLUSH TABLES WITH READ LOCK;')

    # Freeze the xfs file system
    call(['xfs_freeze', '-f', freeze_dir])

    snapshot = ec2_conn.create_snapshot(vol_id)

    # Unfreeze the xfs file system
    call(['xfs_freeze', '-u', freeze_dir])

    if lock_db:
        cursor.execute('UNLOCK TABLES;')

    logging.info("Created snapshot with id: %s" % snapshot.id)
