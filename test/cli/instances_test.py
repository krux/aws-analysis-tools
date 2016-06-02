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

from aws_analysis_tools.cli.instances_2 import Application,  main


class InstancesTest(unittest.TestCase):

    def test_add_cli_arguments(self):
        """
        All cli arguments are getting added for instances
        """
        app = Application()

        self.assertIn('no_header', app.args)
        self.assertIn('group', app.args)
        self.assertIn('exclude_group', app.args)
        self.assertIn('name', app.args)
        self.assertIn('exclude_name', app.args)
        self.assertIn('type', app.args)
        self.assertIn('exclude_type', app.args)
        self.assertIn('zone', app.args)
        self.assertIn('exclude_zone', app.args)
        self.assertIn('state', app.args)
        self.assertIn('exclude_state', app.args)

    def test_main(self):
        """
        Application is instantiated and run() is called in main() for instances
        """
        app = MagicMock()
        app_class = MagicMock(return_value=app)

        with patch('aws_analysis_tools.cli.instances_2.Application', app_class):
            main()

        app_class.assert_called_once_with()
        app.run.assert_called_once_with()

    # def test_convert_args(self):



    # def test_get_messages(self):
    #     """
    #     SQS messages are received and converted into dictionary correctly
    #     """
    #     # TODO: This test needs to be improved using mock and stuff. But for the interest of time,
    #     # let's leave it at this minimal state.
    #     messages = self._sqs.get_messages(self.TEST_QUEUE_NAME)
    #     self.assertIsInstance(messages, list)

    #     for msg in messages:
    #         self.assertIn('ReceiptHandle', msg)
    #         self.assertIsInstance(msg['ReceiptHandle'], str)
    #         self.assertIn('MessageId', msg)
    #         self.assertIsInstance(msg['MessageId'], str)
    #         self.assertIn('Body', msg)
    #         self.assertIsInstance(msg['Body'], dict)
    #         self.assertIn('Message', msg['Body'])
    #         self.assertIsInstance(msg['Body']['Message'], dict)
    #         self.assertIn('MessageAttributes', msg)
    #         self.assertIn('QueueUrl', msg)
    #         self.assertIn('Attributes', msg)

    # def test_delete_messages(self):
    #     """
    #     SQS messages can be deleted correctly
    #     """
    #     # TODO: This test needs to be improved using mock and stuff. But for the interest of time,
    #     # let's leave it at this minimal state.
    #     messages = self._sqs.get_messages(self.TEST_QUEUE_NAME)
    #     self._sqs.delete_messages(self.TEST_QUEUE_NAME, messages)

    # def test_send_message(self):
    #     """
    #     SQS messages can be sent correctly
    #     """
    #     # TODO: This test needs to be improved using mock and stuff. But for the interest of time,
    #     # let's leave it at this minimal state.
    #     messages = [{'foo': 'bar'}, 'baz']
    #     self._sqs.send_messages(self.TEST_QUEUE_NAME, messages)