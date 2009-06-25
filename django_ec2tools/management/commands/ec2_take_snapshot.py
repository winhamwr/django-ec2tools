import logging
from django.core.management.base import NoArgsCommand
from django_ec2tools.ebs import take_snapshot

class Command(NoArgsCommand):
    help = 'Take a snapshot for each of your configured EBS volumes.'
    
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        take_snapshot()
