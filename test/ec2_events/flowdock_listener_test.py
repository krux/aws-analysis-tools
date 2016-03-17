# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest
from datetime import datetime

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from aws_analysis_tools.ec2_events.flowdock_listener import FlowdockListener


class FlowdockListenerTest(unittest.TestCase):
    APP_NAME = 'fake-unit-test-application'
    FLOW_TOKEN = 'fake-flow-token'
    INSTANCE_NAME = 'unit-test.krxd.net'
    INSTANCE_REGION = 'test-region-1'
    INSTANCE_ZONE = INSTANCE_REGION + 'a'
    INSTANCE_ID = 'i-a1b2c3d4'
    EVENT_CODE = 'system-maintenance'
    EVENT_DESCRIPTION = 'Your instance will experience a loss of network connectivity.'
    EVENT_COUNT = 1
    EVENT_SEPARATOR = '\n'
    FLOW_TAG = ['#ec2_events']

    STAT_FORMAT = 'event.{region}.{event_code}'
    MESSAGE_FORMAT = '{az}: {name} ({id}) - {description} between {start_time} and {end_time}'

    def setUp(self):
        self._stats = MagicMock()

        self._flowdock = MagicMock()
        self._flowdock_lib = MagicMock(
            Chat=MagicMock(
                return_value=self._flowdock
            )
        )

        with patch('aws_analysis_tools.ec2_events.flowdock_listener.flowdock', self._flowdock_lib):
            self._listener = FlowdockListener(
                flow_token = self.FLOW_TOKEN,
                name = self.APP_NAME,
                stats = self._stats,
            )

    @classmethod
    def _get_event_params(cls):
        """
        Returns a mock instance and status event
        """
        region = MagicMock()
        region.name = cls.INSTANCE_REGION
        instance = MagicMock(
            placement=cls.INSTANCE_ZONE,
            tags={'Name': cls.INSTANCE_NAME},
            id=cls.INSTANCE_ID,
            region=region,
        )
        event = MagicMock(
            code=cls.EVENT_CODE,
            description=cls.EVENT_DESCRIPTION,
            not_before=datetime.now(),
            not_after=datetime.now()
        )

        return {
            'instance': instance,
            'event': event,
        }

    def test_init(self):
        """
        Flowdock object is created with passed in token
        """
        self._flowdock_lib.Chat.assert_called_once_with(self.FLOW_TOKEN)

    def test_handle_event(self):
        """
        handle_event() correctly increment the stats for the given event type and region
        """
        self._listener.handle_event(**FlowdockListenerTest._get_event_params())

        self._stats.incr.assert_called_once_with(self.STAT_FORMAT.format(region=self.INSTANCE_REGION, event_code=self.EVENT_CODE))

    def test_handle_complete_no_events(self):
        """
        handle_complete() correctly exits without any action when no event was added
        """
        self._listener.handle_complete()

        self.assertFalse(self._flowdock.post.called)

    def test_handle_complete(self):
        """
        handle_complete() correctly post a message with all events
        """
        # Generate 10 fake events
        events = []
        for i in xrange(self.EVENT_COUNT):
            params = FlowdockListenerTest._get_event_params()
            events.append(self.MESSAGE_FORMAT.format(
                az=params['instance'].placement,
                name=params['instance'].tags['Name'],
                id=params['instance'].id,
                description=params['event'].description,
                start_time=params['event'].not_before,
                end_time=params['event'].not_after,
            ))
            self._listener.handle_event(**params)

        self._listener.handle_complete()

        # Check the events are posted to Flowdock
        self._flowdock.post.assert_called_once_with(
            self.EVENT_SEPARATOR.join(events),
            self.APP_NAME,
            self.FLOW_TAG,
        )
