### -*- coding: utf-8 -*-
###
### © 2014 Krux Digital, Inc.
### Author: Jeff Pierce <jeff.pierce@krux.com>
###

"""
Searches EC2 tags and returns a list of servers that match the query terms.
Use double colons (::) rather than single colons like the previous version.
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import

######################
### Krux Libraries ###
######################

import krux.cli

#############################
### Third Party Libraries ###
#############################

import boto.ec2


def parse_query(query_to_parse):
    """
    Converts comma-separated string of query terms into a list to use as filters.
    """
    return query_to_parse.split(',')

def search_tags(query_terms,passed_regions=False):
    """
    Searches EC2 instances based on search terms.
    """
    regions    = boto.ec2.regions()
    filters    = []
    query      = {}
    inst_names = []

    ### Set filters
    if passed_regions:
        ### lambda:  if we've specified a region, only pick regions that
        ### match the provided regions
        filters.extend([lambda r: r.name in passed_regions.split(',')])

    ### lambdas:  remove govcloud and China to improve search speed
    filters.extend([
        lambda r: '-gov-' not in r.name,
        lambda r: not r.name.startswith('cn-')
    ])

    ### Filter out unneeded regions from our regions list.
    for some_filter in filters:
        regions = filter(some_filter, regions)

    ### Populate query dictionary to send to AWS
    for search_param in query_terms:
        ### Split the last term from the query, as the new tagging system
        ### will create keys for each step of the way up to last one, which
        ### will be a value.
        ###
        ### Examples:
        ###     Name::period* searches for tag Name and value period*
        ###     s_periodic::components::s2s::zanox_sync searches for
        ###         tag s_periodic::components::s2s and value zanox_sync.
        search_term = search_param.rsplit('::',1)

        ### If there's nothing to split, like with a query for s_periodic,
        ### add it to the value search.
        if len(search_term) == 1:
            if "tag-value" not in query:
                query.update({"tag-value": ['*' + search_term[0] + '*']})
            else:
                query["tag-value"] = query.get('tag-value') + ['*' + search_term[0] + '*']
        ### But, if there is something that was split (like s_classes::s_periodic),
        ### add the first value to tag-key and the second value to tag-value.
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

    ### Search each region for matching tags/values and return them as a list.
    for region in regions:
        ec2 = region.connect()

        for res in ec2.get_all_instances(filters=query):
            instance = res.instances[0]
            inst_names.append(instance.tags.get('Name'))

    return inst_names

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


def main():
    app = Application()

    parsed_query = parse_query(app.args.query)
    print ', '.join(search_tags(parsed_query, app.args.regions))


if __name__ == '__main__':
    main()

