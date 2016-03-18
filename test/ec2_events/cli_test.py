# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
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

from aws_analysis_tools.ec2_events.cli import Application, NAME


class CLItest(unittest.TestCase):
    JIRA_USERNAME = 'username'
    JIRA_PASSWORD = 'password'
    JIRA_BASE_URL = 'https://unit-test.example.com/'
    FLOW_TOKEN = 'fake-flow-token'

    @patch.object(sys, 'argv', ['prog', '--jira-username', JIRA_USERNAME, '--jira-password', JIRA_PASSWORD, '--jira-base-url', JIRA_BASE_URL, '--flowdock-token', FLOW_TOKEN])
    @patch('aws_analysis_tools.ec2_events.cli.EC2EventChecker')
    @patch('aws_analysis_tools.ec2_events.cli.FlowdockListener')
    @patch('aws_analysis_tools.ec2_events.cli.JiraListener')
    def setUp(self, mock_jira, mock_flowdock, mock_checker):
        self._jira = mock_jira
        self._flowdock = mock_flowdock
        self._checker = mock_checker

        self._app = Application()

    @patch('aws_analysis_tools.ec2_events.cli.EC2EventChecker')
    @patch('aws_analysis_tools.ec2_events.cli.FlowdockListener')
    @patch('aws_analysis_tools.ec2_events.cli.JiraListener')
    def test_init_all_none(self, mock_jira, mock_flowdock, mock_checker):
        """
        Application is only created with the checker when no CLI arguments are passed
        """
        app = Application()

        mock_checker.assert_called_once_with(
            boto=app.boto,
            name=NAME,
            logger=app.logger,
            stats=app.stats
        )
        self.assertFalse(mock_flowdock.called)
        self.assertFalse(mock_jira.called)

    def test_init_all_set(self):
        """
        Flowdock and JIRA listeners are created correctly when all CLI arguments are passed
        """
        self._checker.assert_called_once_with(
            boto=self._app.boto,
            name=NAME,
            logger=self._app.logger,
            stats=self._app.stats
        )
        self._flowdock.assert_called_once_with(
            flow_token=self.FLOW_TOKEN,
            name=NAME,
            logger=self._app.logger,
            stats=self._app.stats
        )
        self._jira.assert_called_once_with(
            username=self.JIRA_USERNAME,
            password=self.JIRA_PASSWORD,
            base_url=self.JIRA_BASE_URL,
            name=NAME,
            logger=self._app.logger,
            stats=self._app.stats
        )

    def test_add_cli_arguments(self):
        pass

    def test_run(self):
        pass

    def test_main(self):
        pass
