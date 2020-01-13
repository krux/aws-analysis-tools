# -*- coding: utf-8 -*-
#
# © 2014 Krux Digital, Inc.
# © 2018 Salesforce.com, Inc.
#
"""
Package setup for aws-analysis-tools
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from setuptools import setup, find_packages

# We use the version to construct the DOWNLOAD_URL.
VERSION      = '0.6.5'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/aws-analysis-tools'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

REQUIREMENTS = ['docopt', 'eventlet', 'reversefold.util', 'texttable']

### XXX these all need to be in sub dirs, or it won't work :(
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
    # dependencies are named in requirements.pip
    install_requires = REQUIREMENTS,
    entry_points     = {
        'console_scripts': [
            'krux-search-ec2-tags    = aws_analysis_tools.cli.search_ec2_tags:main',
            'krux-update-ec2-tags    = aws_analysis_tools.cli.update_ec2_tags:main',
            'krux-ec2-volumes        = aws_analysis_tools.cli.volumes:list_volumes',
            'krux-ec2-instances      = aws_analysis_tools.cli.instances:main',
            'krux-ec2-pssh           = aws_analysis_tools.cli.pssh:main',
            'krux-ec2-pssh2          = aws_analysis_tools.cli.pssh2:main',
            'krux-ec2-events         = aws_analysis_tools.ec2_events.cli:main',
            'krux-ec2-test-provision = aws_analysis_tools.cli.test_provision:main',
            'krux-ec2-ip             = aws_analysis_tools.cli.convert_ip:main',
        ],
    },
)
