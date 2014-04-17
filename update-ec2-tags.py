### -*- coding: utf-8 -*-
###
### © 2014 Krux Digital, Inc.
### Author: Jeff Pierce <jeff.pierce@krux.com>
###

"""
Updates EC2 tags using a new scheme to get around the 255 character limit that
AWS imposes on tags, and emits stats via krux.cli fanciness.
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import
import yaml
from pprint import pprint

######################
### Krux Libraries ###
######################

import krux.cli

#############################
### Third Party Libraries ###
#############################

import boto.ec2


### Collectd alert email and other convenience constants
ALERT_EMAIL      = 'ops@krux.com'
TAG_STARTS_WITH  = 's_'
IGNORE_TAG       = 'params'
PUPPET_YAML_FILE = '/mnt/tmp/facts.yaml'
IGNORE_SYNC      = 'sync'
IGNORE_UPLOAD	 = '_upload'
IGNORE_TO_S3	 = 'to_s3'


class Application(krux.cli.Application):
    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'update_ec2_tags')


    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        group.add_argument(
            '--yaml-file',
            default = PUPPET_YAML_FILE,
            help    = "Specify a YAML file to read the class tags from. (default: %(default)s)"
        )
        group.add_argument(
            '--test',
            action  = "store_true",
            default = False,
            help    = "Prints out the tag dictionary for testing purposes rather than updating the tags on AWS. (default: %(default)s)"
        )


    def update_tags(self, yaml_file):
        """
        Gathers classes together into tags and updates EC2 with them.
        """
        metadata  = boto.utils.get_instance_metadata()
        region    = metadata['placement']['availability-zone'].strip().lower()[:-1]
        inst_id   = metadata['instance-id']
        ec2       = boto.ec2.connect_to_region(region)

        ### Grab classes from facts.yaml or other specified file.
        with open(yaml_file, 'r') as yamlfile:
            puppet = yaml.safe_load(yamlfile)

        ### Tag dictionary to fill using the recursion functions
        tags_dict = {
                'environment':  puppet['environment'],
                'cluster_name': puppet['cluster_name'],
        }

        ### Grab only krux_classes that start with s_ and don't end with params
        ### or sync.
        s_classes = [str(classes) for classes in puppet['krux_classes'].split()
                        if classes.startswith(TAG_STARTS_WITH) and not
                        classes.endswith(IGNORE_TAG) and not
                        classes.endswith(IGNORE_SYNC) and not
                        classes.endswith(IGNORE_UPLOAD) and not
                        classes.endswith(IGNORE_TO_S3)]

        ### Add s_classes to tag dictionary

        tags_dict['s_classes'] = ",".join(s_classes)

        ### Print the dictionary we'd be sending to AWS if we're testing,
        ### otherwise, update EC2 with the new tags.
        if self.args.test:
            pprint(tags_dict)
        else:
            ec2.create_tags([inst_id], tags_dict)


def main():
    app = Application()
    app.update_tags(app.args.yaml_file)


if __name__ == '__main__':
    main()

