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

from texttable import Texttable

#
# Internal libraries
#

import krux_boto
import krux_ec2.cli
from krux_ec2.filter import Filter

NAME = 'instances'


class Application(krux_ec2.cli.Application):

    # A dict with key=CLI options and value=AWS filters
    _CLI_TO_AWS = {
        'group': 'group-name',
        'name': 'tag:Name',
        'type': 'instance-type',
        'zone': 'availability-zone',
        'state': 'instance-state-name'
    }

    # List of all options
    _OPTS = ['group', 'name', 'type', 'zone', 'state']

    # A dict with key=CLI options and value=instance attribute
    _INSTANCE_ATTR = {
        'group': lambda i, attr: next((g.name for g in i.groups if attr in g.name), None),
        'name': lambda i, attr: i.tags.get('Name'),
        'type': lambda i, attr: i.instance_type,
        'zone': lambda i, attr: str(i._placement),
        'state': lambda i, attr: i.state
    }

    _EC2_FILTER_VALUE_TEMPLATE = '*{value}*'

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        # Change self.args into a dict so you can fetch values using
        # keys instead of attributes
        self.options = vars(self.args)

    def add_cli_arguments(self, parser):
        # Call to the superclass first
        super(Application, self).add_cli_arguments(parser)

        group = krux_ec2.cli.get_group(parser, self.name)

        group.add_argument(
            "-H", "--no-header",
            default=None,
            action="store_true",
            help="suppress table header",
        )

        group.add_argument(
            "-g", "--group",
            default=None,
            help="Include instances from these groups only (regex)",
        )

        group.add_argument(
            "-G", "--exclude-group",
            default=None,
            help="Exclude instances from these groups (regex)",
        )

        group.add_argument(
            "-n", "--name",
            default=None,
            help="Include instances with these names only (regex)",
        )

        group.add_argument(
            "-N", "--exclude-name",
            default=None,
            help="Exclude instances with these names (regex)",
        )

        group.add_argument(
            "-t", "--type",
            default=None,
            help="Include instances with these types only (regex)",
        )

        group.add_argument(
            "-T", "--exclude-type",
            default=None,
            help="Exclude instances with these types (regex)",
        )

        group.add_argument(
            "-z", "--zone",
            default=None,
            help="Include instances with these zones only (regex)",
        )

        group.add_argument(
            "-Z", "--exclude-zone",
            default=None,
            help="Exclude instances with these zones (regex)",
        )

        group.add_argument(
            "-s", "--state",
            default=None,
            help="Include instances with these states only (regex)",
        )

        group.add_argument(
            "-S", "--exclude-state",
            default=None,
            help="Exclude instances with these states (regex)",
        )

    def convert_args(self):
        """
        Convert options dictionary to use AWS filters as keys instead of CLI options.
        """

        # Dictionary of options and values to put in the Filter
        filter_dict = {}

        # Add entries to filter_dict with key=AWS filters and value=option
        # values for options that filter on inclusion
        for opt in Application._OPTS:
            if self.options[opt]:
                aws_filter = Application._CLI_TO_AWS[opt]
                filter_dict[aws_filter] = self._EC2_FILTER_VALUE_TEMPLATE.format(value=self.options[opt])

        return filter_dict

    def filter_args(self, filter_dict):
        """
        Use filter_dict to filter instances based on inclusion/exclusion options
        """
        f = Filter(filter_dict)

        # Filter/find instances based on inclusion filters
        instances = self.ec2.find_instances(f)

        # Iterate through found instances and filter based on exclude options
        for opt in Application._OPTS:
            exclude_str = 'exclude_' + opt

            if self.options[exclude_str]:
                attribute = self.options[exclude_str]
            else:
                continue

            # Exclude instances if they have an attribute that is excluded
            instances = [
                            i for i in instances
                            if Application._INSTANCE_ATTR[opt](i, attribute) is None or
                            attribute not in Application._INSTANCE_ATTR[opt](i, attribute)
                        ]

        return instances

    def output_table(self, instances):
        """
        Outputs filtered instances as a table
        """
        table       = Texttable( max_width=0 )

        table.set_deco( Texttable.HEADER )
        table.set_cols_dtype( [ 't', 't', 't', 't', 't', 't', 't', 't' ] )
        table.set_cols_align( [ 'l', 'l', 'l', 'l', 'l', 'l', 'l', 't' ] )

        if not self.args.no_header:
            # using add_row, so the headers aren't being centered, for easier grepping
            table.add_row(
                [ '# id', 'Name', 'Type', 'Zone', 'Group', 'State', 'Root', 'Volumes' ] )

        for i in instances:

            # XXX there's a bug where you can't get the size of the volumes, it's
            # always reported as None :(
            volumes = ", ".join( [ ebs.volume_id for ebs in i.block_device_mapping.values()
                                    if ebs.delete_on_termination == False ] )

            # you can use i.region instead of i._placement, but it pretty
            # prints to RegionInfo:us-east-1. For now, use the private version
            # XXX EVERY column in this output had better have a non-zero length
            # or texttable blows up with 'width must be greater than 0' error
            table.add_row( [ i.id, i.tags.get( 'Name', ' ' ), i.instance_type,
                             i._placement , i.groups[0].name, i.state,
                             i.root_device_type, volumes or '-' ] )


        # table.draw() blows up if there is nothing to print
        if instances or not self.args.no_header:
            print table.draw()

    def run(self):
        filter_dict = self.convert_args()
        instances = self.filter_args(filter_dict)
        self.output_table(instances)


def main():
    app = Application()
    # with app.context():
    app.run()


if __name__ == '__main__':
    main()
