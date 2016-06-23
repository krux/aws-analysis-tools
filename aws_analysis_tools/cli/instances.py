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
            action="append",
            default=[],
            help="Include instances from groups whose name include these characters only",
        )

        group.add_argument(
            "-G", "--exclude-group",
            action="append",
            default=[],
            help="Exclude instances from groups whose name include these characters ",
        )

        group.add_argument(
            "-n", "--name",
            action="append",
            default=[],
            help="Include instances whose name include these characters only",
        )

        group.add_argument(
            "-N", "--exclude-name",
            action="append",
            default=[],
            help="Exclude instances whose name include these characters",
        )

        group.add_argument(
            "--no-name",
            action="store_true",
            default=[],
            help="Exclude all instances with Name tag specificed",
        )

        group.add_argument(
            "-t", "--type",
            action="append",
            default=[],
            help="Include instances with types whose name include these characters only",
        )

        group.add_argument(
            "-T", "--exclude-type",
            action="append",
            default=[],
            help="Exclude instances with types whose name include these characters",
        )

        group.add_argument(
            "-z", "--zone",
            action="append",
            default=[],
            help="Include instances with zones whose name include these characters only",
        )

        group.add_argument(
            "-Z", "--exclude-zone",
            action="append",
            default=[],
            help="Exclude instances with zones whose name include these characters",
        )

        group.add_argument(
            "-s", "--state",
            action="append",
            default=[],
            help="Include instances with states whose name include these characters only",
        )

        group.add_argument(
            "-S", "--exclude-state",
            action="append",
            default=[],
            help="Exclude instances with states whose name include these characters",
        )

    def convert_args(self):
        """
        Convert options dictionary to use AWS filters as keys instead of CLI options.
        """

        # Dictionary of options and values to put in the Filter
        include_filter = Filter()

        # Add entries to include_filter with key=AWS filters and value=option
        # values for options that filter on inclusion
        for opt_name in Application._OPTS:
            for opt_value in self.options[opt_name]:
                include_filter.add_filter(
                    name=Application._CLI_TO_AWS[opt_name],
                    value=self._EC2_FILTER_VALUE_TEMPLATE.format(value=opt_value)
                )

        return include_filter

    def filter_args(self, include_filter):
        """
        Use include_filter to filter instances based on inclusion/exclusion options
        """

        # Filter/find instances based on inclusion filters
        instances = self.ec2.find_instances(include_filter)

        if self.options.get('no_name', False):
            self.logger.debug(
                'Excluding instances from the list of %s instances based on filter (%s)',
                len(instances), 'no_name'
            )
            instances = [i for i in instances if 'Name' not in i.tags]

        # Iterate through found instances and filter based on exclude options
        for opt in Application._OPTS:
            opt_name = 'exclude_' + opt
            opt_values = self.options[opt_name]

            self.logger.debug(
                'Excluding instances from the list of %s instances based on filter (%s: %s)',
                len(instances), opt_name, opt_values,
            )
            for opt_value in opt_values:
                # Exclude instances if they have an attribute that is excluded
                instances = [
                                i for i in instances
                                if Application._INSTANCE_ATTR[opt](i, opt_value) is None or
                                opt_value not in Application._INSTANCE_ATTR[opt](i, opt_value)
                            ]

        return instances

    def output_table(self, instances):
        """
        Outputs filtered instances as a table
        """
        table = Texttable(max_width=0)

        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't', 't', 't', 't', 't'])
        table.set_cols_align(['l', 'l', 'l', 'l', 'l', 'l', 'l', 't'])

        if not self.args.no_header:
            # using add_row, so the headers aren't being centered, for easier grepping
            table.add_row(
                ['# id', 'Name', 'Type', 'Zone', 'Group', 'State', 'Root', 'Volumes']
            )

        for i in instances:

            # XXX there's a bug where you can't get the size of the volumes, it's
            # always reported as None :(
            volumes = ", ".join([
                ebs.volume_id for ebs in i.block_device_mapping.values()
                if not ebs.delete_on_termination
            ])

            # you can use i.region instead of i._placement, but it pretty
            # prints to RegionInfo:us-east-1. For now, use the private version
            # XXX EVERY column in this output had better have a non-zero length
            # or texttable blows up with 'width must be greater than 0' error
            table.add_row([
                i.id,
                i.tags.get('Name', ' '),
                i.instance_type,
                i._placement,
                i.groups[0].name,
                i.state,
                i.root_device_type,
                volumes or '-'
            ])

        # table.draw() blows up if there is nothing to print
        if instances or not self.args.no_header:
            print table.draw()

    def run(self):
        self.logger.debug('Parsed arguments: %s', self.args)

        include_filter = self.convert_args()
        instances = self.filter_args(include_filter)
        self.output_table(instances)


def main():
    app = Application()
    # with app.context():
    app.run()


if __name__ == '__main__':
    main()
