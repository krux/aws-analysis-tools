# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from aws_analysis_tools.ec2_events.flowdock_listener import FlowdockListener


class FlowdockListenerTest(unittest.TestCase):
    NAME = 'fake-unit-test-application'
    FLOW_TOKEN = 'fake-flow-token'

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
                name = self.NAME,
                stats = self._stats,
            )

    def test_init(self):
        """
        Flowdock object is created with passed in token
        """
        self._flowdock_lib.Chat.assert_called_once_with(self.FLOW_TOKEN)

    def test_handle_event(self):
        pass

    def test_handle_complete(self):
        pass
