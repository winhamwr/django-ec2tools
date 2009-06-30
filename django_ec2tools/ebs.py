from subprocess import call
import logging

from django.db import connection, transaction

def take_snapshot(ec2_conn, vol_id, freeze_dir, lock_db=True, fs='xfs'):
    """
    Take a snapshot of the given volume, handling the freezing and unfreezing
    of the file system and locking and unlocking the db (useful for
    non-transactional databases like MyISAM mysql).
    """
    if fs != 'xfs':
        raise NotImplementedError("Support for snapshots across file systems other than xfs not currently supported")

    if lock_db:
        cursor = connection.cursor()
        cursor.execute('FLUSH TABLES WITH READ LOCK;')

    # Freeze the xfs file system
    call(['xfs_freeze', '-f', freeze_dir])

    snapshot = ec2_conn.create_snapshot(vol_id)

    # Unfreeze the xfs file system
    call(['xfs_freeze', '-u', freeze_dir])

    if lock_db:
        cursor.execute('UNLOCK TABLES;')

    logging.info("Created snapshot with id: " % snapshot.id)
