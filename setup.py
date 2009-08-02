import os
from distutils.core import setup

f = open('README.rst')
readme = f.read()
f.close()

def find_packages(root):
    # so we don't depend on setuptools; from the Storm ORM setup.py
    packages = []
    for directory, subdirectories, files in os.walk(root):
        if '__init__.py' in files:
            packages.append(directory.replace(os.sep, '.'))
    return packages

setup(
    name = 'django-ec2tools',
    version = '0.2dev',
    description = 'Maintenance helpers for your ec2-hosted django installation',
    long_description=readme,
    author = 'Wes Winham',
    author_email = 'winhamwr@gmail.com',
    license = 'BSD',
    url = 'http://github.com/winhamwr/django-ec2tools/tree/master',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
        ],
    packages = find_packages('django_ec2tools'),
    install_requires=['boto'],
)
