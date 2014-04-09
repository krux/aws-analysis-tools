### -*- coding: utf-8 -*-
###
### © 2014 Krux Digital, Inc.
### Authors: Jeff Pierce <jeff.pierce@krux.com> and Paul Lathrop <paul@krux.com>
###

"""
Updates EC2 tags using a new scheme to get around the 255 character limit that
AWS imposes on tags, and emits stats via krux.cli fanciness.
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import
from collections import defaultdict
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


def build_dict(puppet_class, some_dict):
    """
    Converts a list of puppet classes into a nested dictionary and merges
    duplicate keys.
    """
    parts = puppet_class.split('::', 1)
    if len(parts) == 1:
        if parts[0] not in some_dict:
            some_dict[parts[0]] = None
    else:
        key, the_rest = parts
        if key not in some_dict:
            some_dict[key] = {}
        build_dict(the_rest, some_dict[key])

def parse_tags(tagdata, prefix=''):
    """
    Parses build_dict()'s dict into EC2 tags.
    """
    parsed = []
    values = defaultdict(list)

    for key, value in tagdata.iteritems():
        name = '::'.join(filter(None, (prefix, key)))
        if value is None:
            values[prefix].append(key)
        elif isinstance(value, (str, unicode)):
            parsed.append((name, value))
        elif isinstance(value, dict):
            parsed.extend(parse_tags(value, prefix=name))

    for key, value in values.iteritems():
        parsed.append((key, ','.join(value)))

    return parsed

def chunk_tags(tag_string, split_val=249):
    split_tags = []
    numsplits = 0
    for start in range(0, len(tag_string), split_val):
        split_tags.append(tag_string[start:start+split_val])
        numsplits += 1

    return split_tags, numsplits

class Application(krux.cli.Application):
    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'update_ec2_tags')

    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        group.add_argument(
            '--yaml-file',
            default = PUPPET_YAML_FILE,
            help    = "Specify a YAML file to read from. (default: %(default)s)"
        )
        group.add_argument(
            '--test',
            action  = "store_true",
            default = False,
            help    = "Prints out the tag dictionary for testing purposes rather than updating the tags on AWS. (default: %(default)s)"
        )

    def update_tags(self):
        """
        Gathers classes together into tags and updates EC2 with them.
        """
        metadata  = boto.utils.get_instance_metadata()
        region    = metadata['placement']['availability-zone'].strip().lower()[:-1]
        inst_id   = metadata['instance-id']
        ec2       = boto.ec2.connect_to_region(region)

        with open(self.args.yaml_file, 'r') as yamlfile:
            puppet = yaml.safe_load(yamlfile)

        tags_dict = {}

        dict_classes = {}

        s_classes = [str(classes) for classes in puppet['krux_classes'].split()
                        if classes.startswith(TAG_STARTS_WITH) and not
                        classes.endswith(IGNORE_TAG)]

        for s_class in s_classes:
            build_dict(s_class, dict_classes)

        tags = dict(parse_tags(dict_classes))

        for key, value in tags.iteritems():
            if len(value) < 254:
                tags_dict[key] = value
            else:
                split_tags, numsplit = chunk_tags(value)
                tags_dict[key] = 'split,' + str(numsplit)
                for splitnum in range(len(split_tags)):
                    if splitnum < len(split_tags) - 1:
                        split_tag = split_tags[splitnum].rsplit(',',1)
                        if len(split_tag) > 1:
                            split_tags[splitnum + 1] = split_tag[1] + split_tags[splitnum + 1]
                            tags_dict[key + str(splitnum)] = split_tag[0]
                    else:
                        tags_dict[key + str(splitnum)] = split_tags[splitnum]

        tags_dict['s_classes']    = ','.join(tags_dict.keys())
        tags_dict['environment']  = puppet['environment']
        tags_dict['cluster_name'] = puppet['cluster_name']

        if self.args.test:
            pprint(tags_dict)
        else:
            ec2.create_tags([inst_id], tags_dict)

def main():
    app = Application()
    app.update_tags()

if __name__ == '__main__':
    main()

