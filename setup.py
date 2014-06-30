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

import os

# We use the version to construct the DOWNLOAD_URL.
VERSION      = '0.0.1'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/aws-analysis-tools'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

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
    install_requires = [
        'krux-stdlib',
        'krux-boto',
        'pyyaml',
        'texttable',
    ],
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
