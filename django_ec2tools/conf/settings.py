from django.conf import settings

volume_1 = {
    'volume_id': 'vol-acba54c5',
    'device': '/dev/sdm',
    'mount_point': '/vol/db',
    'lock_db': True,
}

volume_2 = {
    'volume_id': 'vol-afba54c6',
    'device': '/dev/sdf',
    'mount_point': '/vol/fs',
    'lock_db': False,
}

EC2_INSTANCE = {
    'instance_id': 'i-0180a668',
    'volumes': []
}