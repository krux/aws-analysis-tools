# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import

#
# Third party libraries
#

import flowdock

#
# Internal libraries
#

from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_group


NAME = 'flockdock-li'


def add_flowdock_listener_cli_arguments(parser):
    group = get_group(parser, NAME)

    group.add_argument(
        '--flowdock-token',
        type=str,
        help="Flowdock API token. If provided, will post to Flowdock",
        default=None,
    )


class FlowdockListener(object):

    STAT_FORMAT = 'event.{region}.{event_code}'
    MESSAGE_FORMAT = '{az}: {name} ({id}) - {description} between {start_time} and {end_time}'

    def __init__(
        self,
        flow_token,
        name=NAME,
        logger=None,
        stats=None,
    ):
        # Private variables, not to be used outside this module
        self._name = name
        self._logger = logger or get_logger(self._name)
        self._stats = stats or get_stats(prefix=self._name)

        self._flowdock = flowdock.Chat(flow_token)
        self._events = []

    def handle_event(self, instance, event):
        # Note this event
        self._stats.incr(self.STAT_FORMAT.format(region=instance.region.name, event_code=event.code))

        # Add this to events
        self._events.append(self.MESSAGE_FORMAT.format(
            az=instance.placement,
            name=instance.tags['Name'],
            id=instance.id,
            description=event.description,
            start_time=event.not_before,
            end_time=event.not_after,
        ))

    def handle_complete(self):
        if len(self._events) > 0:
            self._flowdock.post(
                "\n".join(self._events),  # content
                self._name,  # user display name
                ['#ec2_events'],  # tags
            )
