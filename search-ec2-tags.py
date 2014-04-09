### -*- coding: utf-8 -*-
###
### © 2014 Krux Digital, Inc.
### Author: Jeff Pierce <jeff.pierce@krux.com>
###

"""
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import
from pprint import pprint

######################
### Krux Libraries ###
######################

import krux.cli

#############################
### Third Party Libraries ###
#############################

import boto.ec2


class Application(krux.cli.Application):
    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'search_ec2_tags')

    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        group.add_argument(
            '--regions',
            help    = "Defines the EC2 region to search under.  Provide a comma separated string to search multiple regions.",
            default = False
        )
        group.add_argument(
            '--query',
            default = '*',
            help    = "Defines the search terms to use.  Provide a comma separated list to use multiple terms. Defaults to a query that will return all instances."
        )

    def search_tags(self):
        regions = boto.ec2.regions()
        filters = []
        query   = {}

        if self.args.regions:
            filters.extend([lambda r: r.name in group.args.regions.split(',')])
        filters.extend([
            lambda r: '-gov-' not in r.name,
            lambda r: not r.name.startswith('cn-')
        ])

        for some_filter in filters:
            regions = filter(some_filter, regions)

        query_terms = self.args.query.split(',')

        for search_param in query_terms:
            search_term = search_param.rsplit('::',1)
            if len(search_term) == 1:
                if "tag-value" not in query:
                    query.update({"tag-value": ['*' + search_term[0] + '*']})
                else:
                    query["tag-value"] = query.get('tag-value') + ['*' + search_term[0] + '*']
            else:
                tag, val = search_term
                if 'tag-key' not in query:
                    query.update({'tag-key': ['*' + tag + '*']})
                else:
                    query['tag-key'] = query.get('tag-key') + ['*' + tag + '*']
                if 'tag-value' not in query:
                    query.update({"tag-value": ['*' + val +'*']})
                else:
                    query['tag-value'] = query.get('tag-value') + ['*' + val + '*']

        for region in regions:
            ec2 = region.connect()

            for res in ec2.get_all_instances(filters=query):
                instance = res.instances[0]
                print instance.tags.get('Name')

def main():
    app = Application()
    app.search_tags()


if __name__ == '__main__':
    main()

