#!/usr/bin/env kaws-python

### -*- coding: utf-8 -*-
###
### (c) 2014 Krux Digital, Inc.
### Author: Jos Boumans <jos@krux.com>
###

"""
Report instance maintance to STDOUT and/or Flowdock
"""

##########################
### Standard Libraries ###
##########################

from __future__ import absolute_import
import sys

from pprint import pprint, pformat

######################
### Krux Libraries ###
######################

import krux.cli
import krux_boto

#############################
### Third Party Libraries ###
#############################

import boto.exception
import flowdock
from jira import JIRA
from DateTime import DateTime


class Application(krux_boto.Application):
    COMPLETED = 'Completed'
    CANCELED  = 'Canceled'

    JQL_TEMPLATE = 'description ~ "{instance_id}" AND type = "Maintenance Task" AND createdDate >= "{yesterday}"'
    JIRA_COMMENT_TEMPLATE = '{instance_name}\r\n\r\nPlease schedule Icinga downtime from {start_time} to {end_time}.'

    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'ec2-events')

        ### Integrate with flowdock?
        self._flowdock = flowdock.Chat(self.args.flowdock) if self.args.flowdock else None

        ### Integrate with Jira?
        self._jira = JIRA('https://kruxdigital.jira.com')

    def add_cli_arguments(self, parser):

        ### krux_boto.Application's cli arguments.
        super(Application, self).add_cli_arguments(parser)

        ### this apps cli arguments
        group = krux.cli.get_group(parser, self.name)

        group.add_argument(
            '--flowdock',
            type    = str,
            help    = "Flowdock API token. If provided, will post to Flowdock",
            default = None
        )

    def run(self):
        log    = self.logger
        stats  = self.stats

        region = self.boto.ec2.get_region(self.boto.cli_region)
        ec2    = self.boto.connect_ec2(region = region)

        ### Have to start with a connection just to get a list
        ### of all regions, then connect to all the regions to
        ### get their status.
        log.debug('Connected to region: %s', region.name)

        events = [ ]
        for r in ec2.get_all_regions():

            log.debug('Checking region: %s', r.name)
            try:
                conn = self.boto.connect_ec2(region = r)

                ### Get the status of all instances
                all_status = conn.get_all_instance_status()
            except boto.exception.EC2ResponseError, e:
                log.error('Unable to query region %r due to %r', r.name, e)
                continue
            for status in all_status:

                ### are there events?
                if status.events:
                    for event in status.events:

                        ### And they're not yet completed?
                        if self.COMPLETED in event.description:
                            continue

                        ### Or skipped?
                        if self.CANCELED in event.description:
                            continue

                        ### This is a real event we care about
                        instance = self._get_instance_by_id(conn, status.id)
                        message  = self._format_event(instance, status, event)

                        ### print to console now
                        log.info(message)

                        ### and log them here so we can send them elsewhere too
                        events.append(message)

                        self._add_jira_comment(instance, status, event)

        ### post to flowdock as well?
        if len(events) and self._flowdock:
            self._flowdock.post(
                "\n".join(events),  # content
                self.name,          # user display name
                ['#ec2_events'],    # tags
            )

        return True

    def _format_event(self, instance, status, event):
        log    = self.logger
        stats  = self.stats

        ### remove the letter designation
        region = instance.placement[:-1]

        ### note that this happened
        stats.incr('event.%s.%s' % (region, event.code))

        # us-east-1a: bar001.krxd.net (i-...) - system reboot between $now and $then
        message = "%s: %s (%s) - %s between %s and %s" % (
                        instance.placement,
                        instance.tags.get( 'Name', '' ),
                        instance.id,
                        event.description,
                        event.not_before,
                        event.not_after,
                    )

        return message

    def _add_jira_comment(self, instance, status, event):
        log   = self.logger
        stats = self.stats

        yesterday_str = (DateTime() - 1).Date()
        issues = self._jira.search_issues(self.JQL_TEMPLATE.format(instance_id=instance.id, yesterday=yesterday_str))

        for issue in issues:
            # GOTCHA: This is kinda dumb, but Jira does not return the comments when issues are searched
            # Thus, the comments for each issue have to be pulled separately
            comments = self._jira.comments(issue)

            if len([c for c in comments if instance.tags['Name'] in c.body]) < 1:
                start_time = DateTime(event.not_before)
                end_time = DateTime(event.not_after)
                self._jira.add_comment(
                    issue=issue.id,
                    body=self.JIRA_COMMENT_TEMPLATE.format(
                        instance_name=instance.tags['Name'],
                        # GOTCHA: Change the time to PST for easier calculation
                        start_time=str(start_time.toZone('PST')),
                        end_time=str(end_time.toZone('PST'))
                    )
                )

    def _get_instance_by_id(self, ec2, id):
        """
        Boto/AWS are silly, and you have to jump through this hoop
        to get an instance object
        """
        return ec2.get_only_instances(instance_ids = [id])[0]

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
