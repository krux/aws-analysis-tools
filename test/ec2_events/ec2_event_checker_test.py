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


class EC2EventCheckerTest(unittest.TestCase):
    REGIONS = ['test-region-1', 'cn-test-region-2', 'test-gov-region-3']
    DESCRIPTIONS = ['scheduled reboot', '[Completed]', '[Canceled]']
    INSTANCE_NAME = 'unit-test.krxd.net'

    def setUp(self):
        regions = []
        for region in self.REGIONS:
            mock = MagicMock()
            mock.name = region
            regions.append(mock)

        ec2 = MagicMock(
            regions=MagicMock(
                return_value=regions,
            ),
        )

        connection = MagicMock(
            get_all_instance_status=MagicMock(
                return_value=[MagicMock(events=[
                    MagicMock(description=d) for d in self.DESCRIPTIONS
                ])]
            ),
            get_only_instances=MagicMock(
                return_value=[MagicMock(tags={'Name': self.INSTANCE_NAME})]
            )
        )
        self._boto = MagicMock(
            ec2=ec2,
            connect_ec2=MagicMock(
                return_value=connection
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

    def test_add_listener(self):
        pass

    def test_notify_event(self):
        pass

    def test_notify_complete(self):
        pass

    def test_check(self):
        self._checker.check()

        debug_calls = [
            (('Checking region: %s', self.REGIONS[0]),),
            (('Found following event: %s => %s', self.INSTANCE_NAME, self.DESCRIPTIONS[0]),),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)
