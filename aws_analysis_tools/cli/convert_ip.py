# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
from pprint import pformat

#
# Internal libraries
#

import krux_ec2.cli
from krux_ec2.filter import Filter

NAME = 'convert_ip'


class Application(krux_ec2.cli.Application):

    _IP = 'ip-address'
    _PRIVATE_IP = 'private-ip-address'

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        # Set what AWS arg to filter based on
        self.filter_arg = Application._PRIVATE_IP if self.args.private else Application._IP

    def add_cli_arguments(self, parser):
        # Call to the superclass first
        super(Application, self).add_cli_arguments(parser)

        parser.set_defaults(log_level='info')

        group = krux_ec2.cli.get_group(parser, self.name)

        group.add_argument(
            "ip_address",
            help="IP address to be converted",
        )

        group.add_argument(
            "-p", "--private",
            action='store_true',
            default=False,
            help="True if the given IP address is private. (default: %(default)s)",
        )

    def find_instances(self, filter_arg, address):
        """
        Searches for AWS instance based on given filter argument and ip address (private or normal).
        """
        f = Filter()
        f.add_filter(
            name=filter_arg,
            value=address
        )
        return self.ec2.find_instances(f)

    def output_info(self, instances, filter_arg, address):
        """
        Given a list of instances, prints out each instance's name, IP address, private IP address,
        and DNS name in a dictionary.
        """
        if len(instances) != 0:
            for i in instances:
                ip_info = {
                    'Instance Name': str(i.tags.get('Name', '')),
                    'IP Address': str(i.ip_address),
                    'Private IP Address': str(i.private_ip_address),
                    'DNS Name': str(i.dns_name),
                }
                self.logger.info('\n' + pformat(ip_info))

        else:
            self.logger.info('No instance with ' + filter_arg + ': ' + address + ' was found.')

    def run(self):
        instances = self.find_instances(self.filter_arg, self.args.ip_address)
        self.output_info(instances, self.filter_arg, self.args.ip_address)


def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
