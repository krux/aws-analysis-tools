# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest
import sys

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from aws_analysis_tools.cli.convert_ip import Application, NAME, main
from krux.stats import DummyStatsClient

class ConvertIPtest(unittest.TestCase):

    def setUp(self):
        self.app = Application()

    def test_init_(self):
        """
        Application is only created with the checker when no CLI arguments are passed
        """
        self.app.args.private = None

        # There are not much we can test except all the objects are under the correct name
        self.assertEqual(NAME, self.app.name)
        self.assertEqual(NAME, self.app.parser.description)
        # The dummy stats client has no awareness of the name. Just check the class.
        self.assertIsInstance(self.app.stats, DummyStatsClient)
        self.assertEqual(NAME, self.app.logger.name)

        self.assertEqual(self.app.filter_arg, self._IP)

    # @patch.object(sys, 'argv', ['prog', '--jira-username', JIRA_USERNAME, '--jira-password', JIRA_PASSWORD, '--jira-base-url', JIRA_BASE_URL, '--flowdock-token', FLOW_TOKEN, '--urgent', FLOW_URGENT])
    # @patch('aws_analysis_tools.ec2_events.cli.EC2EventChecker')
    # @patch('aws_analysis_tools.ec2_events.cli.FlowdockListener')
    # @patch('aws_analysis_tools.ec2_events.cli.JiraListener')
    # def test_init_all_set(self, mock_jira, mock_flowdock, mock_checker):
    #     """
    #     Flowdock and JIRA listeners are created correctly when all CLI arguments are passed
    #     """
    #     app = Application()

    #     mock_checker.assert_called_once_with(
    #         boto=app.boto,
    #         name=NAME,
    #         logger=app.logger,
    #         stats=app.stats
    #     )
    #     mock_flowdock.assert_called_once_with(
    #         flow_token=self.FLOW_TOKEN,
    #         name=NAME,
    #         logger=app.logger,
    #         stats=app.stats
    #     )
    #     self.assertEqual(mock_flowdock.return_value.urgent_threshold, int(self.FLOW_URGENT))
    #     mock_jira.assert_called_once_with(
    #         username=self.JIRA_USERNAME,
    #         password=self.JIRA_PASSWORD,
    #         base_url=self.JIRA_BASE_URL,
    #         name=NAME,
    #         logger=app.logger,
    #         stats=app.stats
    #     )

    # def test_add_cli_arguments(self):
    #     """
    #     All arguments from the checkers and listeners are present in the args
    #     """
    #     app = Application()

    #     self.assertIn('flowdock_token', app.args)
    #     self.assertIn('jira_username', app.args)
    #     self.assertIn('jira_password', app.args)
    #     self.assertIn('jira_base_url', app.args)

    # def test_run(self):
    #     """
    #     Checker's check() method is correctly called in app.run()
    #     """
    #     checker = MagicMock()

    #     with patch('aws_analysis_tools.ec2_events.cli.EC2EventChecker', return_value=checker):
    #         app = Application()
    #         app.run()

    #     checker.check.assert_called_once_with()

    # def test_main(self):
    #     """
    #     Application is instantiated and run() is called in main()
    #     """
    #     app = MagicMock()
    #     app_class = MagicMock(return_value=app)

    #     with patch('aws_analysis_tools.ec2_events.cli.Application', app_class):
    #         main()

    #     app_class.assert_called_once_with()
    #     app.run.assert_called_once_with()