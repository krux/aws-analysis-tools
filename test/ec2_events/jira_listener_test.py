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

from aws_analysis_tools.ec2_events.jira_listener import JiraListener


class JiraListenerTest(unittest.TestCase):
    APP_USERNAME = 'username'
    APP_PASSWORD = 'password'
    APP_BASE_URL = 'https://unit-test.jira.com/'

    def setUp(self):
        self._res = MagicMock(
            json=MagicMock(
                return_value=[{'issues': [{'key': 'FAKE-1234'}]}]
            )
        )
        self._request = MagicMock()

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener = JiraListener(
                username=self.APP_USERNAME,
                password=self.APP_PASSWORD,
                base_url=self.APP_BASE_URL,
            )

    def test_handle_event(self):
        pass

    def test_handle_complete(self):
        """
        handle_complete() method can be called
        """
        self._listener.handle_complete()
