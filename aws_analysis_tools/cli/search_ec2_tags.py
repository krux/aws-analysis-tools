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
import krux.logging

#############################
### Third Party Libraries ###
#############################

import boto.ec2
import boto.exception
import json


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

    return parsed_query, parsed_regions


def search_tags(query_terms, passed_regions=None, log=None):
    """
    Searches EC2 instances based on parsed search terms returned by parse_query()
    Skips GovCloud and China regions, and can be further filtered by region.
    """
    regions    = boto.ec2.regions()
    filters    = []
    query      = {}
    inst_names = []

    if log is None:
        log = krux.logging.get_logger(
            'search_tags', level='error'
        )

    ### Set filters
    if passed_regions is not None and passed_regions:
        ### lambda:  if we've specified a region, only pick regions that
        ### match the provided regions
        if isinstance(passed_regions, list):
            filters.extend([lambda r: r.name in passed_regions])
        else:
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
        try:
            ec2 = region.connect()

            for res in ec2.get_all_instances(filters=query):
                instance = res.instances[0]
                inst_names.append(instance.tags.get('Name'))
        except boto.exception.EC2ResponseError, e:
            log.error('Unable to query region %r due to %r', region, e)
            continue


    return sorted(inst_names)


class Application(krux.cli.Application):
    SUPPORTED_OUTPUT_FORMATS = [ 'legacy', 'json', 'unix' ]

    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'search-ec2-tags')

        self.output_format = self.args.output_format


    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        group.add_argument(
            '--regions',
            nargs   = 1,
            help    = "Defines the EC2 region to search under.  Provide a comma separated string to search multiple regions.",
            default = False
        )

        group.add_argument(
            '--output-format', '-f',
            default = 'legacy',
            choices = self.SUPPORTED_OUTPUT_FORMATS,
            help    = 'Output format.  Default: %(default)s',
        )

        parser.add_argument(
            'query',
            nargs   = "+",
            help    = "Defines the search terms to use.  Terms can be "
            "separated by a comma or a space, but not both."
        )

    def render(self, results):
        """
        Render RESULTS using the output format specified by the CLI args.
        """
        renderer_name = 'render_{0}'.format(self.output_format)
        renderer = getattr(self, renderer_name, self.render_default)
        return renderer(results)

    def render_default(results):
        """
        Default result renderer. Returns the RESULTS as a UTF8 encoded
        string. Should generally never be used, but is here in case this
        gets used as a library.
        """
        return unicode(results).encode('utf-8')

    def render_legacy(self, results):
        """
        Legacy renderer. Returns a largely-useless string of the form "Matched
        the following hosts: host1, host2, host3". Kept for
        backwards-compatibility.
        """
        return 'Matched the following hosts: {0}'.format(', '.join(results))

    def render_json(self, results):
        """
        Render the results in JSON format.
        """
        return json.dumps(results)

    def render_unix(self, results):
        """
        Render the results in "unix" format, i.e. newline-separated values.
        """
        return '\n'.join(results)


def main():
    app = Application()

    ### Since we can't require positional arguments using the required flag
    ### when defining the add_argument for query, we check to see if the length
    ### of apps.args.query (which is a list) is greater than 0.  If it is,
    ### proceed normally, otherwise, print a simple usage statement and exit
    ### with status 1.
    parsed_query, regions = parse_query(app.args.query)
    print app.render(search_tags(parsed_query, app.args.regions))


if __name__ == '__main__':
    main()
