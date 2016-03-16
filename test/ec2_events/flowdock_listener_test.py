# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest
from logging import Logger

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from aws_analysis_tools.ec2_events.ec2_event_checker import EC2EventChecker


class FlowdockListenerTest(unittest.TestCase):

    def setUp(self):
        self._boto = MagicMock(
            ec2=EC2EventCheckerTest._get_ec2(),
            connect_ec2=MagicMock(
                return_value=self._get_connection()
            ),
        )

        self._logger = MagicMock(
            spec=Logger,
            autospec=True,
        )

        self._checker = EC2EventChecker(
            boto=self._boto,
            logger=self._logger,
        )

        self._listeners = [MagicMock(), MagicMock()]
        for listener in self._listeners:
            self._checker.add_listener(listener)
