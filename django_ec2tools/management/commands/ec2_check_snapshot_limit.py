from optparse import make_option
import logging

from boto import ec2

from django.core.management.base import CommandError, BaseCommand
from django.core.mail import mail_managers

from django_ec2tools.ebs import get_num_snapshots
from django_ec2tools.conf.settings import ACCESS_KEY_ID, SECRET_ACCESS_KEY

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-a', '--access-key',  action="store", dest="aws_access_key",
                    help="AWS Access Key"),
        make_option('-k', '--secret-key', action="store", dest="aws_secret_key",
                    help="AWS Secret Access Key"),
        make_option('--warning-threshold',  action="store", dest="warning_threshold",
                    default=400, type=int, help="The snapshot count threshold passed which a warning will be generated if using --check-snapshot-limit"),
    )

    help = """
    Check the number of snapshots on your AWS account and send a warning if it's
    over a certain threshold."""

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format="%(message)s")

        if not (ACCESS_KEY_ID and SECRET_ACCESS_KEY) and \
           not (options.get('aws_access_key', None) and options.get('aws_secret_key', None)):
            raise CommandError("access_key and secret_key required since no aws account info was found in your settings file")

        access_key = options.get('aws_access_key') or ACCESS_KEY_ID
        secret_key = options.get('aws_secret_key') or SECRET_ACCESS_KEY

        limit = options.get('warning_threshold')

        ec2_conn = ec2.EC2Connection(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key)

        num_snapshots = get_num_snapshots(ec2_conn)
        logging.info("Found %s snapshots" % num_snapshots)

        if num_snapshots > limit:
            msg_tpl = "Your AWS account with access key %s is nearing the snapshot limit. You currently have %s snapshots"
            msg = msg_tpl % ('*'*15 + access_key[-5:], num_snapshots)
            mail_managers("AWS Snapshots nearing limit", msg)
            logging.critical("Sending warning email")
            return "Snapshots over the threshold"