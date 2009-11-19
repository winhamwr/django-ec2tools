django-ec2tools
===============

Django ec2tools is a set of management commands designed to making it easier to run Django on an Amazon EC2 instance using EBS and all of that good stuff. This currently consists of a management command for taking snapshots of your EBS volumes for backup purposes, a command to prune your snapshots based on a flexible retention/pruning strategy and a command to warn you via email if you cross a certain threshold number of snapshots on your way to the 500 snapshot limit.

Installation
------------

* Put django-ec2tools on your python path (you're using pip + virtualenv, so that's easy, right?). ::

    pip install -e git+git://github.com/winhamwr/django-ec2tools.git#egg=django-ec2tools

* Put django_ec2tools in your INSTALLED_APPS list

Optionally:
  * Add AWS access and secret keys to your settings file as EC2_AWS_ACCESS_KEY and EC2_AWS_SECRET_KEY respectively. This makes it possible to run commands without including that information on the command line.
  * If you need database locking, either give your normal database user RELOAD priveleges on *.* in your database or provide DATABASE_BACKUP_USER and DATABASE_BACKUP_PASSWORD settings to a user that does have those privs (so they can FLUSH and LOCK all tables to ensure data integrity for MyISAM tables)

Usage
-----

Taking a Snapshot of your mounted EBS volume
############################################

Take a snapshot of the XFS-formatted EBS volume containing your database (locking the database to ensure data integrity for your MyISAM tables). ::

  manage.py ec2_take_snapshot --volume vol-fooobarr -m /vol/mount/point/db --lock-db --access-key aaa --secret-key aaa

Take a snapshot of the volume named `db` from your ~/.ec2tools.ini config file (and your aws keys in your settings file) ::

  manage.py ec2_take_snapshot db

Pruning your snapshots
######################

Prune snapshots for a particular volume based on the default pruning strategy (Keep anything younger than 2 days) ::

  manage.py ec2_prune_snapshots vol-fooobarr

Prune snapshots for all volumes in your configuration file based on a custom strategy you wrote. ::

  manage.py ec2_prune_snapshots --all --strategy alternating_weekends --strategy-module my_proj.core.pruning_strategy

Default Pruning Strategy
~~~~~~~~~~~~~~~~~~~~~~~~

The default pruning strategy deletes snapshots more than 2 days old. You can configure the default strategy in several ways:
 1. Set EC2_MAX_SNAPSHOT_AGE to some datetime.timedelta representing the max age
 2. Set the EC2_DEFAULT_PRUNE_STRATEGY to the strategy you'd like. django_ec2tools.pruning_strategy has some simple options. See _`Writing Custom Pruning Strategies` for info on how to write your own.
 3. In your `~/.ec2tools.ini` set a strategy option in a volume's section
 4. In your '~/.ec2tools.ini` set a strategy option in the [defaults] (not [DEFAULT]) section.

Checking your snapshot count
############################

At one point, I didn't realize that there was a 500 snapshot limit per AWS account, and after hitting that limit, my backups weren't completing (this spurred the creation of the ec2_prune_snapshots command). This command checks the number of snapshots you have versus a threshold (defaults to 400) and warns you via email if you're above the threshold. This should probably be ran at least daily via cron. ::

  manage.py ec2_check_snapshot_limit --threshold 450

Note: The emails are sent based on the settings.MANAGERS tuple in your project (which is usually the same as settings.ADMINS).

Configuration File
------------------

To eliminate repetition and the need to locate volume ids every backup, you can use a configuration file to set up aliases for your volumes. This file should be located in your HOME directory and named `.ec2tools.ini`

Example
#######

`~/.ec2tools.ini` file ::

  [defaults]
  strategy = oneday_rolling

  [volume_aliases]
  db = db
  fs = fs

  [db]
  volume_id = vol-fooobarr
  mountpoint = /vol/mount/point/db
  lock_db = True

  [fs]
  volume_id = vol-something
  mountpoint = /vol/mount/point/fs
  strategy = oneweek_rolling

volume_aliases
  This section contains variables with an alias name and then a section name representing volume alias definitions. The command line refers to the alias name (not the section name), but you should probably keep them the same to save yourself some hassle.

Volume alias sections
  Each section must define a volume_id and a mountpoint. If `lock_db` isn't defined, then it defaults to False.

strategy
  In each volume section, you can define a strategy to use just for that volume. You can also define a default strategy in [defaults] that will apply to every volume that doesn't have a strategy defined. Be advised though, that entering a strategy on the command line overrides the config file settings.

Writing Custom Pruning Strategies
---------------------------------

A pruning strategy is just a callable that takes a boto ec2.EC2Connection, a boto snapshot object and the volume_id of the volume that's being pruned and then returns True to delete/prune it or False to keep it. To that end, you can just write any old function that fullfils those requirements and call it your strategy. Alternatively, you can subclass PruneStrategyBase and write a _should_prune(self, ec2_conn, snapshot, pruning_vol_id) method. This is only really useful if you want to do something like PruneByAge where you can write one class and then customize it based on how you initialize it. The class-based approache is also nice for things like PruneByAgeWithParents where you can use inheritance keep some things DRY.

See `django_ec2tools.pruning_strategy` for examples.


Also, thanks to Django-filter for letting me rip off all of their project cruft stuff :)

.. _Boto: http://code.google.com/p/boto/