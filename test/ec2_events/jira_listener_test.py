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

from mock import MagicMock, patch, call
from DateTime import DateTime

#
# Internal libraries
#

from aws_analysis_tools.ec2_events.jira_listener import JiraListener


class JiraListenerTest(unittest.TestCase):
    APP_USERNAME = 'username'
    APP_PASSWORD = 'password'
    APP_BASE_URL = 'https://unit-test.example.com/'
    APP_SEARCH_URL = '/rest/api/2/search'
    APP_COMMENT_URL = '/rest/api/2/issue/{issue}/comment'
    INSTANCE_NAME = 'unit-test.krxd.net'
    INSTANCE_ID = 'i-a1b2c3d4'
    ISSUE_KEY = 'FAKE-1234'

    JQL_TEMPLATE = 'description ~ "{instance_id}" AND type = "Maintenance Task" AND createdDate >= "{yesterday}"'
    COMMENT_TEMPLATE = '{instance_name}\r\n\r\nPlease schedule Icinga downtime from {start_time} to {end_time}.'

    def setUp(self):
        self._issues = [{'key': self.ISSUE_KEY}]
        self._comments = []
        self._res = MagicMock(
            status_code=200,
            json=MagicMock(
                side_effect=[
                    {'issues': self._issues},
                    {'comments': self._comments},
                    {},
                ]
            ),
        )
        self._request = MagicMock(
            return_value=self._res,
        )

        self._logger = MagicMock()

        self._listener = JiraListener(
            username=self.APP_USERNAME,
            password=self.APP_PASSWORD,
            base_url=self.APP_BASE_URL,
            logger=self._logger,
        )

        self._instance = MagicMock(
            id=self.INSTANCE_ID,
            tags={'Name': self.INSTANCE_NAME},
        )

        self._event = MagicMock(
            not_before=DateTime().ISO8601(),
            not_after=DateTime().ISO8601(),
        )

    @classmethod
    def _generate_request_call(cls, **kwargs):
        kwargs['url'] = cls.APP_BASE_URL + kwargs['url']
        return call(
            auth=(cls.APP_USERNAME, cls.APP_PASSWORD),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            **kwargs
        )

    def test_handle_event_no_issue(self):
        del self._issues[:]

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        yesterday_str = (DateTime() - 1).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=self.INSTANCE_ID, yesterday=yesterday_str)

        self._logger.debug.assert_called_once_with('Found %s issues that matches the JQL search: %s', len(self._issues), jql_search)

        request_calls = [self._generate_request_call(
            method='POST',
            url=self.APP_SEARCH_URL,
            json={
                'jql': jql_search,
                'fields': [],
            },
        )]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_issue_with_comments(self):
        self._comments.append({'body': self.INSTANCE_NAME})

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        yesterday_str = (DateTime() - 1).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=self.INSTANCE_ID, yesterday=yesterday_str)

        self._logger.debug.assert_called_once_with('Found %s issues that matches the JQL search: %s', len(self._issues), jql_search)

        request_calls = [
            self._generate_request_call(
                method='POST',
                url=self.APP_SEARCH_URL,
                json={
                    'jql': jql_search,
                    'fields': [],
                },
            ),
            self._generate_request_call(
                method='GET',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
            )
        ]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_issue_with_other_comments(self):
        self._comments.append({'body': 'Some random comment'})

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        yesterday_str = (DateTime() - 1).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=self.INSTANCE_ID, yesterday=yesterday_str)

        debug_calls = [
            call('Found %s issues that matches the JQL search: %s', len(self._issues), jql_search),
            call('Determined issue %s needs a comment', self.ISSUE_KEY),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        start_time = DateTime(self._event.not_before)
        end_time = DateTime(self._event.not_after)
        body = self.COMMENT_TEMPLATE.format(
            instance_name=self.INSTANCE_NAME,
            # GOTCHA: Change the time to Pacific time for easier calculation
            # This should handle Daylight Savings Time graciously on its own
            start_time=str(start_time.toZone('US/Pacific')),
            end_time=str(end_time.toZone('US/Pacific')),
        )

        self._logger.info.assert_called_once_with('Added comment to issue %s: %s', self.ISSUE_KEY, body)

        request_calls = [
            self._generate_request_call(
                method='POST',
                url=self.APP_SEARCH_URL,
                json={
                    'jql': jql_search,
                    'fields': [],
                },
            ),
            self._generate_request_call(
                method='GET',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
            ),
            self._generate_request_call(
                method='POST',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
                json={
                    'body': body
                },
            )
        ]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_pass(self):
        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        yesterday_str = (DateTime() - 1).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=self.INSTANCE_ID, yesterday=yesterday_str)

        debug_calls = [
            call('Found %s issues that matches the JQL search: %s', len(self._issues), jql_search),
            call('Determined issue %s needs a comment', self.ISSUE_KEY),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        start_time = DateTime(self._event.not_before)
        end_time = DateTime(self._event.not_after)
        body = self.COMMENT_TEMPLATE.format(
            instance_name=self.INSTANCE_NAME,
            # GOTCHA: Change the time to Pacific time for easier calculation
            # This should handle Daylight Savings Time graciously on its own
            start_time=str(start_time.toZone('US/Pacific')),
            end_time=str(end_time.toZone('US/Pacific')),
        )

        self._logger.info.assert_called_once_with('Added comment to issue %s: %s', self.ISSUE_KEY, body)

        request_calls = [
            self._generate_request_call(
                method='POST',
                url=self.APP_SEARCH_URL,
                json={
                    'jql': jql_search,
                    'fields': [],
                },
            ),
            self._generate_request_call(
                method='GET',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
            ),
            self._generate_request_call(
                method='POST',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
                json={
                    'body': body
                },
            )
        ]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_complete(self):
        """
        handle_complete() method can be called
        """
        self._listener.handle_complete()
