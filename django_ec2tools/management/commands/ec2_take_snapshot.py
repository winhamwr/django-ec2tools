from optparse import make_option
import logging, os.path, ConfigParser, pickle

from boto import ec2

from django.core.management.base import CommandError, BaseCommand
from django.core.exceptions import ImproperlyConfigured

from django_ec2tools.ebs import take_snapshot
from django_ec2tools.conf.settings import ACCESS_KEY_ID, SECRET_ACCESS_KEY

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--lock-db', '-l', default=False, action='store_true',
                    dest='lock_db', help='Lock the db during the snapshot'),
        make_option('-v', '--volume',  action="store", dest="volume",
                    help="Volume id (eg. 'vol-fooobarr')"),
        make_option('-m', '--mountpoint', action="store", dest="mountpoint",
                    help="Volume mount point (for filesystem freezing)"),
        make_option('-A', '--all',  action="store_true", dest="snapshot_all",
                    default=False,
                    help="Snapshot all volumes contained in the configuration file"),
        make_option('-a', '--access-key',  action="store", dest="aws_access_key",
                    help="AWS Access Key"),
        make_option('-k', '--secret-key', action="store", dest="aws_secret_key",
                    help="AWS Secret Access Key"),
        make_option('-c', '--config-file', action="store",
                    default="~/.ec2tools.ini",
                    dest="config_file",
                    help="Path to the .ini configuration file (defaults to ~/.ec2tools.ini)"),
    )

    help = """
    Take a snapshot of the EBS volume on this ec2 instance, handling directory
    locking and database locking."""

    args = '[snapshot]...'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

        if not (ACCESS_KEY_ID and SECRET_ACCESS_KEY) and \
           not (options.get('aws_access_key', None) and options.get('aws_secret_key', None)):
            raise CommandError("access_key and secret_key required since no aws account info was found in your settings file")

        access_key = options.get('aws_access_key') or ACCESS_KEY_ID
        secret_key = options.get('aws_secret_key') or SECRET_ACCESS_KEY

        arg_count = len(args)
        volume = options.get('volume', None)
        mountpoint = options.get('mountpoint', None)
        config_file = options.get('config_file')
        config_file = os.path.join(os.getcwd(), os.path.expanduser(config_file))

        # Validation
        # Must have some info
        if arg_count == 0 and not ( volume and mountpoint ) and not options['snapshot_all']:
            raise CommandError("Either a snapshot from the config file, a volume and mountpoint or the --all flag must be specified")

        if options.get('snapshot_all', False) and ( arg_count > 0 or volume ):
            print "--all flag given, so snapshot arguments and --volume options are being ignored"

        ec2_conn = ec2.EC2Connection(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key)

        # If specifying volume, must fully specify
        if volume or mountpoint:
            if not volume or not mountpoint:
                raise CommandError("Both a volume id and a volume mount point directory are required")

            if volume[:4] != 'vol-' or len(volume) != 12:
                raise CommandError("vol-id must be in form vol-aaaaaaaa")

            freeze_dir = os.path.abspath(mountpoint)

            snapshot_id = take_snapshot(ec2_conn, volume, freeze_dir, options['lock_db'])
            output = [('', snapshot_id, volume)]
            print pickle.dumps(output)

        else:
            config = ConfigParser.ConfigParser()
            config.read(config_file)

            if options.get('snapshot_all'):
                # Take a snapshot of everything in our config file
                try:
                    aliases = config.options('volume_aliases')
                except ConfigParser.NoSectionError:
                    raise CommandError("volume_aliases section not found in config file: %s. Aborting" % config_file)

                snapshots = []
                for alias in aliases:
                    snapshot_id, volume_id = self._snapshot_from_alias(alias, config, ec2_conn)
                    snapshots.append((alias, snapshot_id, volume_id))
            else:
                snapshots = []
                for arg in args:
                    snapshot_id, volume_id = self._snapshot_from_alias(arg, config, ec2_conn)
                    snapshots.append((alias, snapshot_id, volume_id))


            # Output the snapshot results
            print pickle.dumps(snapshots)


    def _snapshot_from_alias(self, alias, config, ec2_conn):
        """
        Take a snapshot based on the alias in the given config file.
        """
        try:
            alias_section = config.get('volume_aliases', alias)
        except ConfigParser.NoSectionError:
            raise CommandError("volume_aliases section not found in config file: %s. Aborting" % config_file)
        except ConfigParser.NoOptionError:
            print "Volume alias: %s not found. Not snapshotting" % alias
            return

        try:
            volume_id = config.get(alias_section, 'volume_id')
            mountpoint = config.get(alias_section, 'mountpoint')
        except ConfigParser.NoOptionError:
            print "Volume alias: %s does not have both a volume_id and mountpoint. Not snapshotting" % alias
            return

        if config.has_option(alias_section, 'lock_db'):
            lock_db = config.get(alias_section, 'lock_db')
        else:
            lock_db = False

        snapshot_id = take_snapshot(ec2_conn, volume_id, mountpoint, lock_db)

        return (volume_id, snapshot_id)