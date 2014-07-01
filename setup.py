# -*- coding: utf-8 -*-
#
# © 2014 Krux Digital, Inc.
#
"""
Package setup for aws-analysis-tools
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from setuptools import setup, find_packages
from pip.req    import parse_requirements

import os

# We use the version to construct the DOWNLOAD_URL.
VERSION      = '0.0.3'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/aws-analysis-tools'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

# We want to install all the dependencies of the library as well, but we
# don't want to duplicate the dependencies both here and in
# requirements.pip. Instead we parse requirements.pip to pull in our
# dependencies.
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(BASE_DIR, 'requirements.pip')

# A requirement file can contain comments (#) and can include some other
# files (--requirement or -r), so we need to use pip's parser to get the
# final list of dependencies.
ALL_DEPENDENCIES = set([unicode(package.req)
                    for package in parse_requirements(REQUIREMENTS)])


setup(
    name             = 'aws-analysis-tools',
    version          = VERSION,
    author           = 'Jos Boumans',
    author_email     = 'jos@krux.com',
    description      = 'Scripts for interacting with AWS/EC2',
    url              = REPO_URL,
    download_url     = DOWNLOAD_URL,
    license          = 'All Rights Reserved.',
    packages         = find_packages(),
    install_requires = ALL_DEPENDENCIES,
    entry_points     = {
        'console_scripts': [
            'krux-search-ec2-tags = search_ec2_tags:main',
            'krux-update-ec2-tags = update_ec2_tags:main',
            'krux-ec2-volumes     = volumes:list_volumes',
            'krux-ec2-instances   = instances:list_instances',
            'krux-ec2-pssh        = pssh:main',
        ],
    },
)
