### -*- coding: utf-8 -*-
###
### © 2014 Krux Digital, Inc.
### Author: Jeff Pierce <jeff.pierce@krux.com>
###

"""
Searches EC2 tags and returns a list of servers that match the query terms.
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import
import sys

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
    if isinstance(query_to_parse, list):
        _query = ','.join(query_to_parse)
    else:
        _query = query_to_parse
    return _query.split(',')


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

    ### lambdas:  remove govcloud and China to improve search speed since
    ### we don't have access to them.
    filters.extend([
        lambda r: '-gov-' not in r.name,
        lambda r: not r.name.startswith('cn-')
    ])

    ### Filter out unneeded regions from our regions list.
    for some_filter in filters:
        regions = filter(some_filter, regions)

    ### Populate query dictionary to send to AWS
    for search_param in query_terms:
        ### Splits the query at : if it's there, as the new tagging system
        ### will create keys for each step of the way up to last one, which
        ### will be a value.
        ###
        ### Examples:
        ###     Name:period* searches for tag Name and value period*
        ###     searches for value matching *s_periodic*.

        ### Check to see if we're searching for an s_class where the split
        ### would cause a problem
        if search_param.startswith('s_') and not search_param.startswith('s_classes'):
            search_term = [search_param]
        else:
            search_term = search_param.split(':',1)

        ### If there's nothing to split, like with a query for s_periodic,
        ### add it to the value search.
        if len(search_term) == 1:
            if "tag-value" not in query:
                query.update({"tag-value": ['*' + search_term[0] + '*']})
            else:
                query["tag-value"] = query.get('tag-value') + ['*' + search_term[0] + '*']
        ### But, if there is something that was split (like s_classes:s_periodic),
        ### add the first value to tag-key and the second value to tag-value.
        else:
            tag, val = search_term
            if 'tag:%s' % tag not in query:
                query.update({"tag:%s" % tag: ['*' + val + '*']})
            else:
                query["tag:%s" % tag] = query.get("tag:%s" % tag) + ['*' + val + '*']

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
        super(Application, self).__init__(name = 'search-ec2-tags')


    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        group.add_argument(
            '--regions',
            nargs   = 1,
            help    = "Defines the EC2 region to search under.  Provide a comma separated string to search multiple regions.",
            default = False
        )
        parser.add_argument(
            'query',
            nargs   = "*",
            default = None,
            help    = "Defines the search terms to use.  Provide a comma separated list to use multiple terms."
        )


def main():
    app = Application()

    if len(app.args.query) > 0:
        parsed_query = parse_query(app.args.query)
        print "Matched the following hosts: " + ', '.join(search_tags(parsed_query, app.args.regions))
    else:
        print 'search-ec2-tags.py requires a search term.  Please run it with one.'
        sys.exit(1)


if __name__ == '__main__':
    main()

