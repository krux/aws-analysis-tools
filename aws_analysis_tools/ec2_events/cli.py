# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import

#
# Internal libraries
#

import krux_boto
from aws_analysis_tools.ec2_events.ec2_event_checker import EC2EventChecker, add_ec2_event_checker_cli_arguments
from aws_analysis_tools.ec2_events.flowdock_listener import FlowdockListener, add_flowdock_listener_cli_arguments


NAME = 'ec2-events'


class Application(krux_boto.Application):

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        self._checker = EC2EventChecker(
            boto=self.boto,
            name=name,
            logger=self.logger,
            stats=self.stats,
        )

        if self.args.flowdock_token is not None:
            self._checker.add_listener(FlowdockListener(
                flow_token=self.args.flowdock_token,
                name=name,
                logger=self.logger,
                stats=self.stats,
            ))

    def add_cli_arguments(self, parser):
        # Call to the superclass first
        super(Application, self).add_cli_arguments(parser)

        add_ec2_event_checker_cli_arguments(parser)
        add_flowdock_listener_cli_arguments(parser)

    def run(self):
        self._checker.check()


def main():
    app = Application()
    # with app.context():
    app.run()


if __name__ == '__main__':
    main()
