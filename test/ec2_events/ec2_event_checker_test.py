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
from boto.exception import EC2ResponseError

#
# Internal libraries
#

from aws_analysis_tools.ec2_events.ec2_event_checker import EC2EventChecker


class EC2EventCheckerTest(unittest.TestCase):
    GOOD_REGIONS = ['test-region-1', 'test-region-2']
    BAD_REGIONS = ['cn-test-region-3', 'test-gov-region-4']
    GOOD_DESCRIPTIONS = ['scheduled reboot', 'Your instance will experience a loss of network connectivity.']
    BAD_DESCRIPTIONS = ['[Completed]', '[Canceled]']
    INSTANCE_NAME = 'unit-test.krxd.net'

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

    @staticmethod
    def _get_ec2(regions=GOOD_REGIONS):
        mock_regions = []
        for region in regions:
            mock_region = MagicMock()
            mock_region.name = region
            mock_regions.append(mock_region)

        return MagicMock(
            regions=MagicMock(
                return_value=mock_regions,
            ),
        )

    def _get_connection(self, event_descs=GOOD_DESCRIPTIONS, instance_name=INSTANCE_NAME):
        self._instance = MagicMock(tags={'Name': instance_name})
        self._events = [MagicMock(description=desc) for desc in event_descs]

        return MagicMock(
            get_all_instance_status=MagicMock(
                return_value=[MagicMock(events=self._events)]
            ),
            get_only_instances=MagicMock(
                return_value=[self._instance]
            )
        )

    def test_notify_event(self):
        self._checker.notify_event(self._instance, self._events[0])

        for listener in self._listeners:
            listener.handle_event.assert_called_once_with(self._instance, self._events[0])

    def test_notify_complete(self):
        self._checker.notify_complete()

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_regions(self):
        self._boto.ec2=EC2EventCheckerTest._get_ec2(regions=self.BAD_REGIONS)

        self._checker.check()

        self.assertEqual([], self._logger.debug.call_args_list)

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_event_call(self):
        err = EC2ResponseError(500, 'Unit test', 'This error was intentionally generated for unit test.')
        self._boto.connect_ec2.return_value.get_all_instance_status.side_effect=err

        self._checker.check()

        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        error_calls = [(('Unable to query region %r due to %r', region, err),) for region in self.GOOD_REGIONS]
        self.assertEqual(error_calls, self._logger.error.call_args_list)

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_no_events(self):
        self._boto.connect_ec2.return_value.get_all_instance_status.return_value = [
            MagicMock(events=[])
        ]

        self._checker.check()

        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_events(self):
        self._boto.connect_ec2.return_value = self._get_connection(event_descs=self.BAD_DESCRIPTIONS)

        self._checker.check()

        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_pass(self):
        self._checker.check()

        debug_calls = []
        event_calls = []
        for region in self.GOOD_REGIONS:
            debug_calls.append((('Checking region: %s', region),))

            for desc in self.GOOD_DESCRIPTIONS:
                debug_calls.append((('Found following event: %s => %s', self.INSTANCE_NAME, desc),))

            for event in self._events:
                event_calls.append(((self._instance, event),))

        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        for listener in self._listeners:
            self.assertEqual(event_calls, listener.handle_event.call_args_list)
            listener.handle_complete.assert_called_once_with()
