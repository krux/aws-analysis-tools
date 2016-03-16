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
        # Set up a mock boto object
        self._boto = MagicMock(
            ec2=EC2EventCheckerTest._get_ec2(),
            connect_ec2=MagicMock(
                return_value=self._get_connection()
            ),
        )

        # Set up a mock logger. This is used to verify code execution
        self._logger = MagicMock()

        # Set up the checker to be tested
        self._checker = EC2EventChecker(
            boto=self._boto,
            logger=self._logger,
        )

        # Set up couple fake listeners
        self._listeners = [MagicMock(), MagicMock()]
        for listener in self._listeners:
            self._checker.add_listener(listener)

    @staticmethod
    def _get_ec2(regions=GOOD_REGIONS):
        """
        Returns a mock boto.ec2 object with the given regions
        """
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
        """
        Returns a mock boto.ec2.connection object that returns status with the given events and an instance with the given name
        """
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
        """
        notify_event() correctly calls the handler for all listeners with an instance and an event
        """
        self._checker.notify_event(self._instance, self._events[0])

        for listener in self._listeners:
            listener.handle_event.assert_called_once_with(self._instance, self._events[0])

    def test_notify_complete(self):
        """
        notify_complete() correctly calls the handler for all listeners without any parameters
        """
        self._checker.notify_complete()

        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_regions(self):
        """
        Invalid regions are properly getting filtered out
        """
        # Override the boto.ec2 to return invalid regions
        self._boto.ec2=EC2EventCheckerTest._get_ec2(regions=self.BAD_REGIONS)

        self._checker.check()

        # There can't be any log because the first for loop will filter everything out
        self.assertEqual([], self._logger.debug.call_args_list)

        # Complete handler should be called for all listeners
        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_event_call(self):
        """
        A boto error on getting status is handled correctly with an error log
        """
        # Override boto.ec2.connection.get_all_instance_status to return an error
        err = EC2ResponseError(500, 'Unit test', 'This error was intentionally generated for unit test.')
        self._boto.connect_ec2.return_value.get_all_instance_status.side_effect=err

        self._checker.check()

        # The region check log would be present
        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        # The error should be logged
        error_calls = [(('Unable to query region %r due to %r', region, err),) for region in self.GOOD_REGIONS]
        self.assertEqual(error_calls, self._logger.error.call_args_list)

        # Complete handler should be called for all listeners
        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_no_events(self):
        """
        Statuses without any events are correctly filtered out
        """
        # Override boto.ec2.connection.get_all_instance_status to return no events
        self._boto.connect_ec2.return_value = self._get_connection(event_descs=[])

        self._checker.check()

        # The region check log would be present
        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        # Complete handler should be called for all listeners
        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_bad_events(self):
        """
        Status events with invalid descriptions are correctly filtered out
        """
        # Override boto.ec2.connection.get_all_instance_status to return events with invalid descriptions
        self._boto.connect_ec2.return_value = self._get_connection(event_descs=self.BAD_DESCRIPTIONS)

        self._checker.check()

        # The region check log would be present
        debug_calls = [(('Checking region: %s', region),) for region in self.GOOD_REGIONS]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        # Complete handler should be called for all listeners
        for listener in self._listeners:
            listener.handle_complete.assert_called_once_with()

    def test_check_pass(self):
        """
        check() method correctly checks and notifies listeners
        """
        self._checker.check()

        debug_calls = []
        event_calls = []
        for region in self.GOOD_REGIONS:
            # The region check log should be present for all regions
            debug_calls.append((('Checking region: %s', region),))

            for desc in self.GOOD_DESCRIPTIONS:
                # The event log should be present for all events
                debug_calls.append((('Found following event: %s => %s', self.INSTANCE_NAME, desc),))

            for event in self._events:
                # Event handler should be called for all events
                event_calls.append(((self._instance, event),))

        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        for listener in self._listeners:
            self.assertEqual(event_calls, listener.handle_event.call_args_list)
            # Complete handler should be called for all listeners
            listener.handle_complete.assert_called_once_with()
