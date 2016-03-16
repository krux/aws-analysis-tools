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
    GOOD_REGION = 'test-region-1'
    BAD_REGIONS = ['cn-test-region-2', 'test-gov-region-3']
    GOOD_DESCRIPTION = 'scheduled reboot'
    BAD_DESCRIPTIONS = ['[Completed]', '[Canceled]']
    INSTANCE_NAME = 'unit-test.krxd.net'

    def setUp(self):
        self._boto = MagicMock(
            ec2=EC2EventCheckerTest._get_ec2(),
            connect_ec2=MagicMock(
                return_value=EC2EventCheckerTest._get_connection()
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

    @staticmethod
    def _get_ec2(region=GOOD_REGION):
        mock_region = MagicMock()
        mock_region.name = region

        return MagicMock(
            regions=MagicMock(
                return_value=[mock_region],
            ),
        )

    @staticmethod
    def _get_connection(event_desc=GOOD_DESCRIPTION, instance_name=INSTANCE_NAME):
        return MagicMock(
            get_all_instance_status=MagicMock(
                return_value=[MagicMock(events=[MagicMock(description=event_desc)])]
            ),
            get_only_instances=MagicMock(
                return_value=[MagicMock(tags={'Name': instance_name})]
            )
        )

    def test_add_listener(self):
        pass

    def test_notify_event(self):
        pass

    def test_notify_complete(self):
        pass

    def test_check_pass(self):
        self._checker.check()

        debug_calls = [
            (('Checking region: %s', self.GOOD_REGION),),
            (('Found following event: %s => %s', self.INSTANCE_NAME, self.GOOD_DESCRIPTION),),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)
