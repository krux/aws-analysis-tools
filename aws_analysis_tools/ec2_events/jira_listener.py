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

    URL_TEMPLATES = {
        'base': 'https://kruxdigital.jira.com/{url}',
        'search': '/rest/api/2/search',
        'comment': '/rest/api/2/issue/{issue}/comment',
    }
    JQL_TEMPLATE = 'description ~ "{instance_id}" AND type = "Maintenance Task" AND createdDate >= "{yesterday}"'
    COMMENT_TEMPLATE = '{instance_name}\r\n\r\nPlease schedule Icinga downtime from {start_time} to {end_time}.'

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

    def _request(self, **kwarg):
        kwarg['headers'] = self._headers
        kwarg['auth'] = self._auth
        kwarg['url'] = self.URL_TEMPLATES['base'].format(url=kwarg['url'])

        res = request(**kwarg)

        if res.status_code > 299 or res.status_code < 200:
            raise ValueError(
                'Something went wrong. {status_code} {reason} was returned. Body: {body}'
                .format(status_code=res.status_code, reason=res.reason, body=res.content)
            )

        return res.json()

    def handle_event(self, instance, event):
        issues = self._find_issues(instance)

        for issue in issues:
            self._comment_issue(issue, instance.tags['Name'], event)

    def _find_issues(self, instance):
        yesterday_str = (DateTime() - 30).Date()
        jql_search = self.JQL_TEMPLATE.format(instance_id=instance.id, yesterday=yesterday_str)

        res = self._request(
            method='POST',
            url=self.URL_TEMPLATES['search'],
            json={
                'jql': jql_search,
                'fields': [],
            },
        )

        issues = res['issues']
        self._logger.debug('Found %s issues that matches the JQL search: %s', len(issues), jql_search)

        return issues

    def _comment_issue(self, issue, instance_name, event):
        # GOTCHA: This is kinda dumb, but Jira does not return the comments when issues are searched
        # Thus, the comments for each issue have to be pulled separately
        comments_res = self._request(
            method='GET',
            url=self.URL_TEMPLATES['comment'].format(issue=issue['key'])
        )
        comments = comments_res['comments']

        if len([c for c in comments if instance_name in c['body']]) < 100:
            self._logger.debug('Determined issue %s needs a comment', issue['key'])

            start_time = DateTime(event.not_before)
            end_time = DateTime(event.not_after) if event.not_after is not None else DateTime(9999, 12, 31)
            body = self.COMMENT_TEMPLATE.format(
                instance_name=instance_name,
                # GOTCHA: Change the time to PST for easier calculation
                start_time=str(start_time.toZone('PST')),
                end_time=str(end_time.toZone('PST')),
            )

            #self._jira.add_comment(issue=issue.id, body=body)

            self._logger.info('Added comment to issue %s: %s', issue['key'], body)

    def handle_complete(self):
        pass
