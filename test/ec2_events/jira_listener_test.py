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
    EXCEPTION_STATUS = 400
    EXCEPTION_REASON = 'Bad Request'
    EXCEPTION_CONTENT = 'Unit test failure'

    JQL_TEMPLATE = 'description ~ "{instance_id}" AND type = "Maintenance Task" AND createdDate >= "{yesterday}"'
    COMMENT_TEMPLATE = '{instance_name}\r\n\r\nPlease schedule Icinga downtime from {start_time} to {end_time}.'
    EXCEPTION_TEMPLATE = 'Something went wrong. {status_code} {reason} was returned. Body: {body}'

    def setUp(self):
        # Set up a mock request object
        self._issues = [{'key': self.ISSUE_KEY}]
        self._comments = []
        self._res = MagicMock(
            status_code=200,
            json=MagicMock(
                # GOTCHA: res.json() is called 3 times total to get the data from HTTP call.
                # return_vale cannot return different values based on the order, so use side_effect.
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

        # Set up a mock logger. This is used to verify code execution
        self._logger = MagicMock()

        # Set up the listener to be tested
        self._listener = JiraListener(
            username=self.APP_USERNAME,
            password=self.APP_PASSWORD,
            base_url=self.APP_BASE_URL,
            logger=self._logger,
        )

        # Set up a mock instance that is having a maintenance
        self._instance = MagicMock(
            id=self.INSTANCE_ID,
            tags={'Name': self.INSTANCE_NAME},
        )

        # Set up a mock maintenance event
        self._event = MagicMock(
            not_before=DateTime().ISO8601(),
            not_after=DateTime().ISO8601(),
        )

    @classmethod
    def _generate_request_call(cls, **kwargs):
        """
        Fill out all the basic data that is shared amongst all the request calls
        This verifies that every call is using the correct HTTP header
        """
        kwargs['url'] = cls.APP_BASE_URL + kwargs['url']
        return call(
            auth=(cls.APP_USERNAME, cls.APP_PASSWORD),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            **kwargs
        )

    def _get_jql_search(self):
        """
        Returns a tuple of logger call and request call regarding JQL search
        """
        yesterday_str = (DateTime() - 1).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=self.INSTANCE_ID, yesterday=yesterday_str)
        return (
            call(
                'Found %s issues that matches the JQL search: %s',
                len(self._issues),
                jql_search,
            ),
            self._generate_request_call(
                method='POST',
                url=self.APP_SEARCH_URL,
                json={
                    'jql': jql_search,
                    'fields': [],
                },
            )
        )

    def _get_retrieve_comment_request_call(self):
        return self._generate_request_call(
            method='GET',
            url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
        )

    def _get_comment_body(self, end_time):
        start_time = DateTime(self._event.not_before)
        return self.COMMENT_TEMPLATE.format(
            instance_name=self.INSTANCE_NAME,
            # GOTCHA: Change the time to Pacific time for easier calculation
            # This should handle Daylight Savings Time graciously on its own
            start_time=str(start_time.toZone('US/Pacific')),
            end_time=str(end_time.toZone('US/Pacific')),
        )

    def _verify_full_execution(self, end_time):
        """
        Calls handle_event(), assumes that the whole method is getting executed, and verifies accordingly
        end_time is required to check the body of the comment
        """
        # Calls handle_event()
        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        jql_search_log_call, jql_search_requst_call = self._get_jql_search()

        # Checks the debug log is correct
        debug_calls = [
            jql_search_log_call,
            call('Determined issue %s needs a comment', self.ISSUE_KEY),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        # Generates the correct comment using the end time
        comment = self._get_comment_body(end_time)

        # Checks the body of the comment is getting logged as info
        self._logger.info.assert_called_once_with('Added comment to issue %s: %s', self.ISSUE_KEY, comment)

        # Checks the request is called 3 times with correct parameters
        request_calls = [
            jql_search_requst_call,
            self._get_retrieve_comment_request_call(),
            self._generate_request_call(
                method='POST',
                url=self.APP_COMMENT_URL.format(issue=self.ISSUE_KEY),
                json={
                    'body': comment
                },
            ),
        ]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_no_issue(self):
        """
        handle_event() is correctly omitted if there is no JIRA issue for the given instance
        """
        del self._issues[:]

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        jql_search_log_call, jql_search_requst_call = self._get_jql_search()

        debug_calls = [jql_search_log_call]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        request_calls = [jql_search_requst_call]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_issue_with_comments(self):
        """
        Duplicate comment is not posted
        """
        self._comments.append({'body': self.INSTANCE_NAME})

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            self._listener.handle_event(self._instance, self._event)

        jql_search_log_call, jql_search_requst_call = self._get_jql_search()

        debug_calls = [jql_search_log_call]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

        request_calls = [
            jql_search_requst_call,
            self._get_retrieve_comment_request_call(),
        ]
        self.assertEqual(request_calls, self._request.call_args_list)

    def test_handle_event_issue_with_other_comments(self):
        """
        handle_event() correctly posts a comment even though there are other comments
        """
        self._comments.append({'body': 'Some random comment'})

        self._verify_full_execution(end_time=DateTime(self._event.not_after))

    def test_handle_event_no_end_time(self):
        """
        handle_event() correctly handles the event with no end time
        """
        self._event.not_after = None

        self._verify_full_execution(end_time=DateTime(9999, 12, 31))

    def test_handle_event_pass(self):
        """
        handle_event() corrects posts a comment if there is no other comment
        """
        self._verify_full_execution(end_time=DateTime(self._event.not_after))

    def test_request_fail(self):
        """
        Exception is thrown with the body of the HTTP response if a request call fails
        """
        self._res.status_code = self.EXCEPTION_STATUS
        self._res.reason = self.EXCEPTION_REASON
        self._res.content = self.EXCEPTION_CONTENT

        with patch('aws_analysis_tools.ec2_events.jira_listener.request', self._request):
            with self.assertRaises(ValueError) as e:
                self._listener.handle_event(self._instance, self._event)

        self.assertEqual(self.EXCEPTION_TEMPLATE.format(status_code=self.EXCEPTION_STATUS, reason=self.EXCEPTION_REASON, body=self.EXCEPTION_CONTENT), e.exception.message)

    def test_handle_complete(self):
        """
        handle_complete() method can be called
        """
        self._listener.handle_complete()
