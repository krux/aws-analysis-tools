# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import re

#
# Third party libraries
#

import boto

#
# Internal libraries
#

import krux_boto
from krux.logging import get_logger
from krux.stats import get_stats


NAME = 'ec2-event-checker'


class EC2EventChecker(object):

    FORBIDDEN_REGIONS = re.compile('^(cn-.+|.+-gov-.+)$')
    NOT_APPLICABLE_EVENT = re.compile('^(\[Completed\]|\[Canceled\])')

    def __init__(
        self,
        boto,
        logger=None,
        stats=None,
    ):
        # Private variables, not to be used outside this module
        self._name = NAME
        self._logger = logger or get_logger(self._name)
        self._stats = stats or get_stats(prefix=self._name)

        self._boto = boto
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def notify_event(self, instance, event):
        for listener in self._listeners:
            listener.handle_event(instance, event)

    def notify_complete(self):
        for listener in self._listeners:
            listener.handle_complete()

    def check(self):
        # Filter out unavailable regions like China or US-gov't-only
        for region in [r for r in self._boto.ec2.regions() if not self.FORBIDDEN_REGIONS.match(r.name)]:
            self._logger.debug('Checking region: %s', region.name)

            try:
                # Get the status of all instances
                conn = self._boto.connect_ec2(region=region)
                all_status = conn.get_all_instance_status()
            except boto.exception.EC2ResponseError, e:
                self._logger.error('Unable to query region %r due to %r', region.name, e)
                continue

            # Get all status that have events
            for status in [s for s in all_status if s.events]:

                # Filter out the events that are either completed or canceled
                for event in [e for e in status.events if not self.NOT_APPLICABLE_EVENT.match(e.description)]:
                    instance = conn.get_only_instances(instance_ids=[status.id])[0]

                    # Log this event
                    self._logger.debug('Found following event: %s => %s', instance.tags['Name'], event.description)

                    # Notify the listeners
                    self.notify_event(instance, event)

        self.notify_complete()
