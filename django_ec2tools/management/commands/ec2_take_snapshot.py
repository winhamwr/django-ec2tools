from optparse import make_option
import logging, os.path

from boto import ec2

from django.core.management.base import CommandError, BaseCommand
from django.core.exceptions import ImproperlyConfigured

from django_ec2tools.ebs import take_snapshot
from django_ec2tools.conf.settings import ACCESS_KEY_ID, SECRET_ACCESS_KEY

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--vol-id', '-V', action='store', dest='vol_id',
                    help='The volume to snapshot. Eg. vol-aaaaaaaa'),
        make_option('--freeze-dir', '-d', action='store', dest='freeze_dir',
                    help='The directory that the EBS volume is mounted on'),
        make_option('--lock-db', '-l', default=False, action='store_true',
                    dest='lock_db', help='Lock the db during the snapshot'),
        make_option('-a', '--access_key',  dest="aws_access_key",
                    help="AWS Access Key"),
        make_option('-s', '--secret_key', default=None, dest="aws_secret_key",
                 help="AWS Secret Access Key"),
    )

    help = """
    Take a snapshot of the EBS volume on this ec2 instance, handling directory
    locking and database locking."""

    args = '[vol-id freeze-dir]'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

        if not (ACCESS_KEY_ID and SECRET_ACCESS_KEY) and \
           not (options.get('aws_access_key', None) and options.get('aws_secret_key', None)):
            raise CommandError("access_key and secret_key required since no aws account info was found in your settings file")

        access_key = options.get('aws_access_key', ACCESS_KEY_ID)
        secret_key = options.get('aws_secret_key', SECRET_ACCESS_KEY)

        if len(args) != 3:
            raise ComandError("Both a volume id and a freeze directory are required")

        vol_id = args[1]
        if vol_id[:3] != 'vol-' or len(vol_id) != 12:
            raise CommandError("vol-id must be in form vol-aaaaaaaa")

        freeze_dir = args[2]
        freeze_dir = os.path.abspath(freeze_dir)

        ec2_conn = ec2.EC2Connection(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key)
        take_snapshot(ec2_conn, vol_id, freeze_dir, options['lock_db'])
