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
from DateTime import DateTime

#
# Internal libraries
#

from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_group


NAME = 'flockdock-listener'


def add_flowdock_listener_cli_arguments(parser):
    group = get_group(parser, NAME)

    group.add_argument(
        '--flowdock-token',
        type=str,
        help="Flowdock API token. If provided, will post to Flowdock. (default: %(default)s)",
        default=None,
    )

    group.add_argument(
        '--urgent',
        type=int,
        help="If the event is closer than this number of hours, send an @team notification. (default: %(default)s)",
        default=FlowdockListener.DEFAULT_URGENT_THRESHOLD_HOURS
    )


class FlowdockListener(object):

    STAT_FORMAT = 'event.{region}.{event_code}'
    MESSAGE_FORMAT = '{az}: {name} ({id}) - {description} between {start_time} and {end_time}'
    URGENT_EVENTS_MESSAGE_FORMAT = '@team, the following events will happen within the next {hours} hours:\n{events}'
    DEFAULT_URGENT_THRESHOLD_HOURS = 5 * 24  # 5 days

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
        self._regular_events = []
        self._urgent_events = []
        self.urgent_threshold = self.DEFAULT_URGENT_THRESHOLD_HOURS

    def handle_event(self, instance, event):
        # Note this event
        self._stats.incr(self.STAT_FORMAT.format(region=instance.region.name, event_code=event.code))

        # GOTCHA: DateTime arithmatics are done in days. Convert hours into days.
        threshold_time = DateTime(event.not_before) - (float(self.urgent_threshold) / 24)
        msg = self.MESSAGE_FORMAT.format(
            az=instance.placement,
            name=instance.tags['Name'],
            id=instance.id,
            description=event.description,
            start_time=event.not_before,
            end_time=event.not_after,
        )
        if threshold_time.isFuture():
            # The event will happen after the threshold time.
            # Just regular notification will suffice.
            self._logger.debug('This event is not urgent yet: %s', msg)
            self._regular_events.append(msg)
        else:
            # The event will happen within the next threshold time.
            # Highlight this event.
            self._logger.debug('This event is urgent: %s', msg)
            self._urgent_events.append(msg)

    def handle_complete(self):
        if len(self._regular_events) > 0:
            self._logger.debug('Found %s regular events', len(self._regular_events))
            self._flowdock.post(
                "\n".join(self._regular_events),  # content
                self._name,  # user display name
                ['#ec2_events'],  # tags
            )

        if len(self._urgent_events) > 0:
            self._logger.debug('Found %s urgent events', len(self._urgent_events))
            self._flowdock.post(
                self.URGENT_EVENTS_MESSAGE_FORMAT.format(hours=self.urgent_threshold, events='\n'.join(self._urgent_events)),  # content
                self._name,  # user display name
                ['#ec2_events'],  # tags
            )
