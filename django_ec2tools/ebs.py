from subprocess import call
import logging, datetime

from django.conf import settings

from django_ec2tools.conf.settings import DATABASE_BACKUP_PASSWORD, DATABASE_BACKUP_USER, XFS_FREEZE_CMD, MAX_SNAPSHOT_AGE
from pruning_strategy import PruneByAge

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
    call([XFS_FREEZE_CMD, '-f', freeze_dir])

    try:
        snapshot = ec2_conn.create_snapshot(vol_id)
    finally:
        # Unfreeze the xfs file system even if our snapshot threw an error
        call([XFS_FREEZE_CMD, '-u', freeze_dir])

    # Unfreeze the xfs file system
    call([XFS_FREEZE_CMD, '-u', freeze_dir])

    if lock_db:
        cursor.execute('UNLOCK TABLES;')

    logging.info("Created snapshot with id: %s" % snapshot.id)

    return snapshot.id

def prune_snapshots(ec2_conn, vol_id, should_prune):
    """
    Prune the given volume's snapshots according to the pruning strategy.
    Return the number of snapshots deleted.
    """

    all_snapshots = ec2_conn.get_all_snapshots()

    vols_snapshots = filter(lambda x: x.volume_id == vol_id, all_snapshots)
    logging.info("volume: [%s] has [%s] snapshots" % (vol_id, len(vols_snapshots)))

    pruned_snapshots = 0
    for snapshot in all_snapshots:
        if should_prune(ec2_conn, snapshot, vol_id):
            logging.info("Deleting snapshot with id: %s" % snapshot.id)
            snapshot.delete()
            pruned_snapshots += 1

    return pruned_snapshots

def get_num_snapshots(ec2_conn):
    """
    Get the total number of snapshots that exist on this account.
    """
    all_snapshots = ec2_conn.get_all_snapshots()

    return len(all_snapshots)