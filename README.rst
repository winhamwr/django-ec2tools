django-ec2tools
===============

Django ec2tools is a set of management commands designed to help running Django on an Amazon EC2 instance using EBS and all of that good stuff. Right now, that pretty much just consists of a management command for taking snapshots of your EBS volumes for backup purposes.

Installation
------------

  * Install the Boto_ AWS library::
      pip install boto

  * Put django-ec2tools on your python path (you're using pip + virtualenv, so that's easy, right?).::
      pip install -e git+git://github.com/winhamwr/django-ec2tools.git#egg=django-ec2tools

  * Put django_ec2tools in your INSTALLED_APPS list

Optionally:
  * Add AWS access and secret keys to your settings file as EC2_AWS_ACCESS_KEY and EC2_AWS_SECRET_KEY respectively. This makes it possible to run commands without including that information on the command line.
  * If you need database locking, either give your normal database user RELOAD priveleges on *.* in your database or provide DATABASE_BACKUP_USER and DATABASE_BACKUP_PASSWORD settings to a user that does have those privs (so they can FLUSH and LOCK all tables to ensure data integrity for MyISAM tables)

Usage
-----

### Taking a Snapshot of your mounted EBS volume

Take a snapshot of the XFS-formatted EBS volume containing your database (locking the database to ensure data integrity for your MyISAM tables).::
  manage.py ec2_take_snapshot -v vol-fooobarr -m /vol/mount/point/db --lock-db --access-key aaa --secret-key aaa

Take a snapshot of the volume named `db` from your ~/.ec2tools.ini config file (and your aws keys in your settings file)::
  manage.py ec2_take_snapshot db

Configuration File
------------------

To eliminate repetition and the need to locate volume ids every backup, you can use a configuration file to set up aliases for your volumes. This file should be located in your HOME directory and named `.ec2tools.ini`

### Example `~/.ec2tools.ini` file::
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

#### volume_aliases

This section contains variables with an alias name and then a section name representing volume alias definitions. The command line refers to the alias name (not the section name), but you should probably keep them the same to save yourself some hassle.

#### Volume alias sections

Each section must define a volume_id and a mountpoint. It `lock_db` isn't defined, then it defaults to False.


Django 1.1 Note
---------------

This *should* work with django 1.1, but it's untested. The bit that will break is the database connection switching for your DATABASE_BACKUP_USER, as the internals that I had to much with there changed between 1.0.2 and 1.1 (they're much nicer in 1.1).


Also, thanks to Django-filter for letting me rip off all of their project cruft stuff :)

.. _Boto http://code.google.com/p/boto/