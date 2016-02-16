# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import base64

#
# Third party libraries
#

from requests import request
from DateTime import DateTime

#
# Internal libraries
#

from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_group


NAME = 'jira-listener'


def add_jira_listener_cli_argumemts(parser):
    group = get_group(parser, NAME)

    group.add_argument(
        '--jira-username',
        type=str,
        help='Username to login to Jira. If provided, will add a comment to Jira tickets',
        default=None,
    )

    group.add_argument(
        '--jira-password',
        type=str,
        help='Password for the Jira user.',
        default=None,
    )


class JiraListener(object):

    BASE_URL_TEMPLATE = 'https://'
    JQL_TEMPLATE = 'description ~ "{instance_id}" AND type = "Maintenance Task" AND createdDate >= "{yesterday}"'
    JIRA_COMMENT_TEMPLATE = '{instance_name}\r\n\r\nPlease schedule Icinga downtime from {start_time} to {end_time}.'

    def __init__(
        self,
        username,
        password,
        name=NAME,
        logger=None,
        stats=None,
    ):
        # Private variables, not to be used outside this module
        self._name = NAME
        self._logger = logger or get_logger(self._name)
        self._stats = stats or get_stats(prefix=self._name)

        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        self._auth = (username, password)

    def handle_event(self, instance, event):
        print self._find_issues(instance)

    def _find_issues(self, instance):
        yesterday_str = (DateTime() - 30).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=instance.id, yesterday=yesterday_str)

        res = request(
            method='POST',
            url='https://kruxdigital.jira.com/rest/api/2/search',
            headers=self._headers,
            auth=self._auth,
            json={
                'jql': jql_search,
                'fields': [],
            },
        )

        if res.status_code > 299 or res.status_code < 200:
            raise ValueError(
                'Something went wrong. {status_code} {reason} was returned. Body: {body}'
                .format(status_code=res.status_code, reason=res.reason, body=res.content)
            )

        issues = res.json()['issues']
        self._logger.debug('Found %s issues that matches the JQL search: %s', len(issues), jql_search)

        return issues

    def handle_complete(self):
        pass
