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

from aws_analysis_tools.ec2_events.jira_listener import JiraListener


class JiraListenerTest(unittest.TestCase):
    APP_USERNAME = 'username'
    APP_PASSWORD = 'password'
    APP_BASE_URL = 'https://unit-test.example.com/'
    INSTANCE_NAME = 'unit-test.krxd.net'
    INSTANCE_ID = 'i-a1b2c3d4'

    def setUp(self):
        self._res = MagicMock(
            status_code=200,
            json=MagicMock(
                side_effect=[
                    {'issues': [{'key': 'FAKE-1234'}]},
                    {'comments': [{'body': ''}]},
                    {},
                ]
            )
        )

        self._listener = JiraListener(
            username=self.APP_USERNAME,
            password=self.APP_PASSWORD,
            base_url=self.APP_BASE_URL,
        )

    def test_handle_event(self):
        instance = MagicMock(
            id=self.INSTANCE_ID,
            tags={'Name': self.INSTANCE_NAME},
        )
        event = MagicMock(
            not_before=datetime.now(),
            not_after=datetime.now(),
        )

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', return_value=self._res):
            self._listener.handle_event(instance, event)

    def test_handle_complete(self):
        """
        handle_complete() method can be called
        """
        self._listener.handle_complete()
