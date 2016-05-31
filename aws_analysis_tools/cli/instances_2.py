# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import

#
# Third party libraries
#

import re
from texttable  import Texttable

#
# Internal libraries
#

import krux_boto
import krux_ec2
import krux.cli
from krux_ec2.ec2 import add_ec2_cli_arguments, get_ec2, NAME
from krux_ec2.filter import Filter

NAME = 'instances'


class Application(krux_boto.Application):

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        ###################
        ### Regexes
        ###################

        # self.regexes = {}
        # for opt in [ 'group', 'exclude_group', 'name', 'exclude_name',
        #      'type',  'exclude_type',  'zone', 'exclude_zone',
        #      'state', 'exclude_state' ]:

        #     ### we have a regex we should build
        #     options = vars( self.args )
        #     if options.get( opt, None ):
        #         self.regexes[ opt ] = options.get( opt )
        #         # self.regexes[ opt ] = re.compile( options.get( opt ), re.IGNORECASE )

        # print(options)

        # REMOVE LATER!!!
        self.ec2 = get_ec2(self.args, self.logger, self.stats)

        self.options = vars( self.args )
        self.args.boto_region = self.args.region
        self.filters = None

        self.convert_args()

        # if options.verbose: self.args.log_level = logging.DEBUG
        # else:               self.args.log_level = logging.INFO


    def convert_args(self):
        cli_to_aws = { 'group' : 'group-name', 
                        'name' : 'tag:Name', 
                        'type' : 'instance-type', 
                        'zone' : 'availability-zone', 
                        'state' : 'instance-state-name' }

        include = [ 'group', 'name', 'type', 'zone', 'state' ]


        self.filters = {}

        for opt in include:
            if self.options[ opt ]:
                aws_opt = cli_to_aws[ opt ]
                self.filters[ aws_opt ] = self.options[ opt ] 

        # for opt in include:
        #     exclude_str = 'exclude_' + opt
        #     if self.options[ exclude_str ]:
        #         aws_opt = cli_to_aws[ opt ]
        #         filters[ aws_opt ]

    def add_cli_arguments(self, parser):
        # Call to the superclass first
        super(Application, self).add_cli_arguments(parser)

        parser.add_argument(  "-v", "--verbose",      default=None, action="store_true",
                    help="enable debug output" )
        parser.add_argument(  "-H", "--no-header",    default=None, action="store_true",
                            help="suppress table header" )
        parser.add_argument(  "-r", "--region",       default='us-east-1',
                            help="ec2 region to connect to" )
        parser.add_argument(  "-g", "--group",        default=None,
                            help="Include instances from these groups only (regex)" )
        parser.add_argument(  "-G", "--exclude-group",default=None,
                            help="Exclude instances from these groups (regex)" )
        parser.add_argument(  "-n", "--name",         default=None,
                            help="Include instances with these names only (regex)" )
        parser.add_argument(  "-N", "--exclude-name", default=None,
                            help="Exclude instances with these names (regex)" )
        parser.add_argument(  "-t", "--type",         default=None,
                            help="Include instances with these types only (regex)" )
        parser.add_argument(  "-T", "--exclude-type", default=None,
                            help="Exclude instances with these types (regex)" )
        parser.add_argument(  "-z", "--zone",         default=None,
                            help="Include instances with these zones only (regex)" )
        parser.add_argument(  "-Z", "--exclude-zone", default=None,
                            help="Exclude instances with these zones (regex)" )
        parser.add_argument(  "-s", "--state",        default=None,
                            help="Include instances with these states only (regex)" )
        parser.add_argument(  "-S", "--exclude-state",default=None,
                            help="Exclude instances with these states (regex)" )


    def run(self):
        f = Filter(self.filters)

        print self.ec2.find_instances(f)

        # instances   = [ i for r in self.conn.get_all_instances()
        #             for i in r.instances ]

        # rv          = [];
        # for i in instances:

        #     ### we will assume this node is one of the nodes we want
        #     ### to operate on, and we will unset this flag if any of
        #     ### the criteria fail
        #     wanted_node = True

        #     for re_name, regex in self.regexes.iteritems():

        #         ### What's the value we will be testing against?
        #         if re.search( 'group', re_name ):
        #             value = i.groups[0].name
        #         elif re.search( 'name', re_name ):
        #             value = i.tags.get( 'Name', '' )
        #         elif re.search( 'type', re_name ):
        #             value = i.instance_type
        #         elif re.search( 'state', re_name ):
        #             value = i.state
        #         elif re.search( 'zone', re_name ):
        #             ### i.region is an object. i._placement is a string.
        #             value = str(i._placement)

        #         else:
        #             logging.error( "Don't know what to do with: %s" % re_name )
        #             continue

        #         #PP.pprint( "name = %s value = %s pattern = %s" % ( re_name, value, regex.pattern ) )

        #         ### Should the regex match or not match?
        #         if re.search( 'exclude', re_name ):
        #             rv_value = None
        #         else:
        #             rv_value = True

        #         ### if the match is not what we expect, then clearly we
        #         ### don't care about the node
        #         result = regex.search( value )

        #         ### we expected to get no results, excellent
        #         if result == None and rv_value == None:
        #             pass

        #         ### we expected to get some match, excellent
        #         elif result is not None and rv_value is not None:
        #             pass

        #         ### we don't care about this node
        #         else:
        #             wanted_node = False
        #             break

        #     if wanted_node:
        #         rv.append( i )

        # table       = Texttable( max_width=0 )

        # table.set_deco( Texttable.HEADER )
        # table.set_cols_dtype( [ 't', 't', 't', 't', 't', 't', 't', 't' ] )
        # table.set_cols_align( [ 'l', 'l', 'l', 'l', 'l', 'l', 'l', 't' ] )

        # if not self.args.no_header:
        #     ### using add_row, so the headers aren't being centered, for easier grepping
        #     table.add_row(
        #         [ '# id', 'Name', 'Type', 'Zone', 'Group', 'State', 'Root', 'Volumes' ] )


        # # instances = rv
        # for i in instances:

        #     ### XXX there's a bug where you can't get the size of the volumes, it's
        #     ### always reported as None :(
        #     volumes = ", ".join( [ ebs.volume_id for ebs in i.block_device_mapping.values()
        #                             if ebs.delete_on_termination == False ] )

        #     ### you can use i.region instead of i._placement, but it pretty
        #     ### prints to RegionInfo:us-east-1. For now, use the private version
        #     ### XXX EVERY column in this output had better have a non-zero length
        #     ### or texttable blows up with 'width must be greater than 0' error
        #     table.add_row( [ i.id, i.tags.get( 'Name', ' ' ), i.instance_type,
        #                      i._placement , i.groups[0].name, i.state,
        #                      i.root_device_type, volumes or '-' ] )

        #     #PP.pprint( i.__dict__ )

        # ### table.draw() blows up if there is nothing to print
        # if instances or not self.args.no_header:
        #     print table.draw()


def main():
    app = Application()
    # with app.context():
    app.run()


if __name__ == '__main__':
    main()
