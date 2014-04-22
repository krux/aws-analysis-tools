#!/usr/bin/env kaws-python

### -*- coding: utf-8 -*-
###
### (c) 2014 Krux Digital, Inc.
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
    Converts a comma or space-separated string of query terms into a list to use
    as filters.  The use of positional arguments on the CLI provides lists (which
    we join and resplit to avoid any formatting issues), while strings passed
    from pssh.py just get split since those should never come over as a list.
    """
    if isinstance(query_to_parse, list):
        _query = ','.join(query_to_parse)
    else:
        _query = query_to_parse.replace(' ',',')
    split_query = _query.split(',')

    ### Pick up passed --region query from pssh.py
    parsed_query = [x for x in split_query if not x.startswith('--region=')]
    region_query = [x for x in split_query if x.startswith('--region')]
    parsed_regions = ','.join([x.split('=')[1] for x in region_query])
    print parsed_query, parsed_regions

    return parsed_query, parsed_regions


def search_tags(query_terms,passed_regions=None):
    """
    Searches EC2 instances based on parsed search terms returned by parse_query()
    Skips GovCloud and China regions, and can be further filtered by region.
    """
    regions    = boto.ec2.regions()
    filters    = []
    query      = {}
    inst_names = []

    ### Set filters
    if passed_regions is not None:
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
        ### Splits the query at : if it's a tag:value search parameter and adds
        ### those to the query dictionary (or appends the value to an existing
        ### tag), otherwise it creates a key of tag-value (if it doesn't already
        ### exist) with the search term as the value and performs a value only
        ### search.
        ###
        ### Examples:
        ###     Name:period searches for tag Name and value *period*
        ###     s_periodic searches for value matching *s_periodic*.
        ###     Name:period*,Name:webapp* searches for tag Name with values
        ###         *period* and *webapp* as an OR search.

        ### Check to see if we're searching for an s_class where the split
        ### would cause a problem
        if search_param.startswith('s_') and not search_param.startswith('s_classes'):
            search_term = [search_param]
        else:
            search_term = search_param.split(':',1)

        ### If the query contains just a value, like with a query for s_periodic,
        ### add it to the value search, len(search_term) will be 1 and gets added
        ### to tag value.  We always search to ensure that the key for the dictionary
        ### hasn't already been made before adding it, otherwise, we append the
        ### value to the already existing key.  This goes for a tag:value query
        ### as well.
        if len(search_term) == 1:
            if "tag-value" not in query:
                query.update({"tag-value": ['*' + search_term[0] + '*']})
            else:
                query["tag-value"] = query.get('tag-value') + ['*' + search_term[0] + '*']

        ### But, if the query is in tag:value format (like s_classes:s_periodic),
        ### len(search_term) will be 2, and if the query was s_classes:s_periodic,
        ### search_term would be [ 's_classes', 's_periodic' ], so we assign
        ### search_term[0] to the tag variable, and search_term[1] to the val
        ### variable.
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
            help    = "Defines the search terms to use.  Terms can be separated by a comma or a space, but not both."
        )


def main():
    app = Application()

    ### Since we can't require positional arguments using the required flag
    ### when defining the add_argument for query, we check to see if the length
    ### of apps.args.query (which is a list) is greater than 0.  If it is,
    ### proceed normally, otherwise, print a simple usage statement and exit
    ### with status 1.
    if len(app.args.query) > 0:
        parsed_query = parse_query(app.args.query)
        print "Matched the following hosts: " + ', '.join(search_tags(parsed_query, app.args.regions))
    else:
        print 'search-ec2-tags.py requires a search term.  Please run it with one.'
        sys.exit(1)


if __name__ == '__main__':
    main()

