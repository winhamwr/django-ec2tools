from optparse import make_option
import logging, os.path, ConfigParser

import boto
from boto.ec2.connection import EC2ResponseError

from django.core.management.base import CommandError, BaseCommand
from django.core.exceptions import ImproperlyConfigured

from django_ec2tools.ebs import prune_snapshots
from django_ec2tools.conf.settings import ACCESS_KEY_ID, SECRET_ACCESS_KEY, PRUNE_STRATEGY_MODULE, DEFAULT_PRUNE_STRATEGY

CONNECTION_ERROR_MSG = """The connection to AWS failed. Please check your network connection and your AWS credentials (settings.EC2_AWS_ACCESS_KEY and settings.EC2_AWS_SECRET_KEY).
                    Error: %s"""
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-v', '--volume',  action="store", dest="volume",
                    help="Volume whose snapshots to prune (eg. 'vol-fooobarr')"),
        make_option('-s', '--strategy',  action="store", dest="strategy",
                    help="Pruning strategy. eg. 'rolling_2day'"),
        make_option('-p', '--strategy-module',  action="store", dest="strategy_module",
                    default=PRUNE_STRATEGY_MODULE,
                    help="Python module where your pruning strategy is located. eg. 'django_ec2tools.pruning_strategy'"),
        make_option('-A', '--all',  action="store_true", dest="all_volumes",
                    default=False,
                    help="Prune snapshots across all volumes contained in the configuration file"),
        make_option('-a', '--access-key',  action="store", dest="aws_access_key",
                    help="AWS Access Key"),
        make_option('-k', '--secret-key', action="store", dest="aws_secret_key",
                    help="AWS Secret Access Key"),
        make_option('-c', '--config-file', action="store",
                    default="~/.ec2tools.ini",
                    dest="config_file",
                    help="Path to the .ini configuration file (defaults to ~/.ec2tools.ini)"),
        make_option('-V', '--verbose', action="store_true", dest="verbose", default=False,
                    help="Increase verbosity"),
    )

    help = """
    Prune EBS snapshots according to a defined retention strategy.
    See README.rst for details"""

    args = '[volume_id]...'

    def handle(self, *args, **options):

        if not (ACCESS_KEY_ID and SECRET_ACCESS_KEY) and \
           not (options.get('aws_access_key', None) and options.get('aws_secret_key', None)):
            raise CommandError("access_key and secret_key required since no aws account info was found in your settings file")

        access_key = options.get('aws_access_key') or ACCESS_KEY_ID
        secret_key = options.get('aws_secret_key') or SECRET_ACCESS_KEY

        volume_id = options.get('volume', None)
        strategy = options.get('strategy', None)
        verbose = options.get('verbose')
        prune_strategy_module = options.get('strategy_module')

        if verbose:
            verbosity = logging.INFO
        else:
            verbosity = logging.WARNING
        logging.basicConfig(level=verbosity, format="%(message)s")

        if strategy:
            strategy = self._build_strategy(strategy, prune_strategy_module)
        else:
            strategy = DEFAULT_PRUNE_STRATEGY

        config_file = options.get('config_file')
        config_file = os.path.join(os.getcwd(), os.path.expanduser(config_file))

        volumes = args
        if volume_id:
            volumes = list(volumes)
            volumes.append(volume_id)

        # Validation
        # Must have some info
        if not volumes and not options['all_volumes']:
            raise CommandError("Either volumes or the --all flag must be specified")

        ec2_conn = boto.ec2.EC2Connection(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key)


        pruned_count = 0 # Number of snapshots removed
        for volume in volumes:
            if volume[:4] != 'vol-' or len(volume) != 12:
                raise CommandError("vol-id must be in form vol-aaaaaaaa. Error: [%s]" % volume)
            try:
                pruned_count += prune_snapshots(ec2_conn, volume, strategy)
            except EC2ResponseError, e:
                raise CommandError(CONNECTION_ERROR_MSG % e)

        if options.get('all_volumes'):
            config = ConfigParser.ConfigParser()
            config.read(config_file)

            # Prune snapshots for all volumes in the config file
            if not config.has_section('volume_aliases'):
                raise CommandError("volume_aliases section not found in config file: %s. Aborting" % config_file)

            for alias, section_name in config.items('volume_aliases'):
                volume_id = config.get(section_name, 'volume_id')

                if strategy:
                    # If we were given a command line strategy, use that
                    volume_strategy = strategy
                elif config.has_option(section_name, 'strategy'):
                    # If there's a strategy specified in the vol config, use that
                    strategy_name = config.get(section_name, 'strategy')
                    volume_strategy = self._build_strategy(strategy_name, prune_strategy_module)
                elif config.has_option('defaults', 'strategy'):
                    # If no strategy in the vol config, use the defaults config strategy
                    strategy_name = config.get('defaults', 'strategy')
                    volume_strategy = self._build_strategy(strategy_name, prune_strategy_module)
                else:
                    # Otherwise, just let prune_snapshots figure out the strategy
                    volume_strategy = DEFAULT_PRUNE_STRATEGY

                try:
                    pruned_count += prune_snapshots(ec2_conn, volume_id, volume_strategy)
                except EC2ResponseError, e:
                    raise CommandError(CONNECTION_ERROR_MSG % e)

        print "Pruned [%s] snapshots" % pruned_count

    def _build_strategy(self, strategy, prune_strategy_module):
        try:
            strat_module = my_import(prune_strategy_module)
        except ImportError:
            raise ImproperlyConfigured("The module for importing pruning \
            strategies was not found. Please ensure that django_ec2tools is on \
            the python path and that if you have EC2_PRUNE_STRATEGY_MODULE \
            set in settings.py, that it points to an existing module on the \
            python path")
        try:
            strat_callable = getattr(strat_module, strategy)
        except AttributeError:
            raise CommandError("The given strategy was not found in the strategy module. \
            Strategy: [%s]. Module: [%s]" % (strategy, prune_strategy_module))
        if not callable(strat_callable):
            raise CommandError("The given strategy is not a callable. \
            Strategy: [%s]"% strategy)

    def _snapshot_from_alias(self, alias, config, ec2_conn):
        """
        Take a snapshot based on the alias in the given config file.
        Returns a tuple of the (snapshot_id, volume_id)
        """
        try:
            alias_section = config.get('volume_aliases', alias)
        except ConfigParser.NoSectionError:
            raise CommandError("volume_aliases section not found in config file: %s. Aborting" % config_file)
        except ConfigParser.NoOptionError:
            logging.warn("Volume alias: %s not found. Not snapshotting" % alias)
            return

        try:
            volume_id = config.get(alias_section, 'volume_id')
            mountpoint = config.get(alias_section, 'mountpoint')
        except ConfigParser.NoOptionError:
            logging.warn("Volume alias: %s does not have both a volume_id and mountpoint. Not snapshotting" % alias)
            return

        if config.has_option(alias_section, 'lock_db'):
            lock_db = config.get(alias_section, 'lock_db')
        else:
            lock_db = False

        snapshot_id = take_snapshot(ec2_conn, volume_id, mountpoint, lock_db)

        return (snapshot_id, volume_id)

# From http://stackoverflow.com/questions/211100/pythons-import-doesnt-work-as-expected
# @author dwestbrook
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod