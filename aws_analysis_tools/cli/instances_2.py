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

from texttable  import Texttable

#
# Internal libraries
#

import krux_boto
import krux_ec2.cli
from krux_ec2.ec2 import add_ec2_cli_arguments, get_ec2, NAME
from krux_ec2.filter import Filter

NAME = 'instances'


class Application(krux_ec2.cli.Application):

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        self.options = vars( self.args )

        # if options.verbose: self.args.log_level = logging.DEBUG
        # else:               self.args.log_level = logging.INFO


    def filter_args(self):
        # A dict with key=CLI options and value=AWS filters
        cli_to_aws = { 'group' : 'group-name', 
                        'name' : 'tag:Name', 
                        'type' : 'instance-type', 
                        'zone' : 'availability-zone', 
                        'state' : 'instance-state-name' }

        # List of all options
        opts = [ 'group', 'name', 'type', 'zone', 'state' ]

        # Dictionary of options and values to put in the Filter
        filter_dict = {}

        # Add entries to filter_dict with key=AWS filters and value=option values
        # for options that filter on inclusion
        for opt in opts:
            if self.options[ opt ]:
                aws_filter = cli_to_aws[ opt ]
                filter_dict[ aws_filter ] = self.options[ opt ] 

        f = Filter(filter_dict)

        # Filter/find instances based on inclusion filters
        instances = self.ec2.find_instances(f)
        instances_copy = list(instances)

        # Iterate through the found instances and filter based on exclude options
        for opt in opts:
            exclude_str = 'exclude_' + opt

            if self.options[ exclude_str ]:
                attribute = self.options[ exclude_str ]
            else:
                continue

            for i in instances_copy:
                # If the instance should be excluded based on an attribute, remove it
                if self.get_instance_attribute(i, opt) == attribute:
                    instances.remove(i)

        return instances

    # Given an AWS instance and a CLI opt returns the corresponding instance attribute
    def get_instance_attribute(self, instance, opt):
        if opt == 'group':
            return instance.group_name

        if opt == 'tag:Name':
            if instance.tags:
                return instance.tags['Name']
            return None
        
        if opt == 'type':
            return instance.instance_type

        if opt == 'zone':
            return instance._placement

        if opt == 'state':
            return instance.state

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
        with open('out2', 'w') as f:

            table       = Texttable( max_width=0 )

            table.set_deco( Texttable.HEADER )
            table.set_cols_dtype( [ 't', 't', 't', 't', 't', 't', 't', 't' ] )
            table.set_cols_align( [ 'l', 'l', 'l', 'l', 'l', 'l', 'l', 't' ] )

            if not self.args.no_header:
                ### using add_row, so the headers aren't being centered, for easier grepping
                table.add_row(
                    [ '# id', 'Name', 'Type', 'Zone', 'Group', 'State', 'Root', 'Volumes' ] )


            instances = self.filter_args()
            for i in instances:

                ### XXX there's a bug where you can't get the size of the volumes, it's
                ### always reported as None :(
                volumes = ", ".join( [ ebs.volume_id for ebs in i.block_device_mapping.values()
                                        if ebs.delete_on_termination == False ] )

                ### you can use i.region instead of i._placement, but it pretty
                ### prints to RegionInfo:us-east-1. For now, use the private version
                ### XXX EVERY column in this output had better have a non-zero length
                ### or texttable blows up with 'width must be greater than 0' error
                table.add_row( [ i.id, i.tags.get( 'Name', ' ' ), i.instance_type,
                                 i._placement , i.groups[0].name, i.state,
                                 i.root_device_type, volumes or '-' ] )


            ### table.draw() blows up if there is nothing to print
            if instances or not self.args.no_header:
                f.write(table.draw())
                # print table.draw()


def main():
    app = Application()
    # with app.context():
    app.run()


if __name__ == '__main__':
    main()
