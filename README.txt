django-ec2tools
==============

Django ec2tools is a set of management commands designed to help running Django on an Amazon EC2 instance using EBS and all of that good stuff. Right now, that pretty much just consists of a management command for taking snapshots of your EBS volumes for backup purposes.

Installation
------------

 * Install the [Boto](http://code.google.com/p/boto/) AWS library
 * Put django-ec2tools on your python path (you're using virtualenv, so that's easy, right?). Until I figure out how to use setuptools, that's a manual process.
 * Put django_ec2tools in your INSTALLED_APPS list

Optionally:
 * Add AWS access and secret keys to your settings file as EC2_AWS_ACCESS_KEY and EC2_AWS_SECRET_KEY respectively. This makes it possible to run commands without including that information on the command line.
 * If you need database locking, either give your normal database user RELOAD priveleges on *.* in your database or provide DATABASE_BACKUP_USER and DATABASE_BACKUP_PASSWORD settings to a user that does have those privs (so they can FLUSH and LOCK all tables to ensure data integrity for MyISAM tables)

Usage
-----

### Taking a Snapshot of your mounted EBS volume

Take a snapshot of the XFS-formatted EBS volume containing your database (locking the database to ensure data integrity for your MyISAM tables).
    manage.py ec2_take_snapshot vol-fooobarr /vol/mount/point --lock-db --access-key aaa --secret-key aaa

Django 1.1 Note
---------------

This *should* work with django 1.1, but it's untested. The bit that will break is the database connection switching for your DATABASE_BACKUP_USER, as the internals that I had to much with there changed between 1.0.2 and 1.1 (they're much nicer in 1.1).


Also, thanks to Django-filter for letting me rip off all of their project cruft stuff :)
