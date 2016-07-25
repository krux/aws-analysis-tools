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
from pprint import pformat

#
# Third party libraries
#

from mock import MagicMock, patch, call

#
# Internal libraries
#

from aws_analysis_tools.cli.convert_ip import Application, NAME, main
from krux.stats import DummyStatsClient

class ConvertIPtest(unittest.TestCase):

    LOG_LEVEL = 'info'
    IP = 'ip-address'
    PRIVATE_IP = 'private-ip-address'
    IP_ADDRESS = '123.456.789'
    INSTANCES_LIST = ['1', '2', '3']
    INSTANCE_DNS = 'instance_dns'

    @patch('sys.argv', ['krux-ec2-ip', IP_ADDRESS])
    def setUp(self):
        self.app = Application()

    def test_init_ip(self):
        """
        Application is instantiated with a normal ip address
        """
        # There are not much we can test except all the objects are under the correct name
        self.assertEqual(NAME, self.app.name)
        self.assertEqual(NAME, self.app.parser.description)
        # The dummy stats client has no awareness of the name. Just check the class.
        self.assertIsInstance(self.app.stats, DummyStatsClient)
        self.assertEqual(NAME, self.app.logger.name)

        self.assertEqual(self.app.filter_arg, self.IP)

    @patch('sys.argv', ['krux-ec2-ip', IP_ADDRESS, '--private'])
    def test_init_private_ip(self):
        """
        Application is instantiated with a private ip address
        """
        app = Application()

        self.assertEqual(app.filter_arg, self.PRIVATE_IP)

    @patch('aws_analysis_tools.cli.convert_ip.Filter')
    def test_find_instances(self, mock_filter):
        """
        Filter is created correctly and find_instances is called on it
        """
        self.app.ec2.find_instances = MagicMock()

        self.app.find_instances(self.IP, self.IP_ADDRESS)

        mock_filter.assert_called_once_with()
        mock_filter.return_value.add_filter.assert_called_once_with(name=self.IP, value=self.IP_ADDRESS)

        self.app.ec2.find_instances.assert_called_once_with(mock_filter.return_value)

    def test_output_info(self):
        """
        Output info called with instances outputs the desired information
        """
        self.app.logger = MagicMock()
        instances = [MagicMock(), MagicMock(), MagicMock()]

        index = 0
        for i in instances:
            i.tags.get.return_value = 'instances' + str(index)
            i.ip_address = self.IP_ADDRESS
            i.private_ip_address = self.IP_ADDRESS
            i.dns_name = self.INSTANCE_DNS

            index += 1

        self.app.logger.info = MagicMock()
        self.app.output_info(instances, self.IP, self.IP_ADDRESS)

        calls = []
        for i in instances:
            ip_info = {
                'Instance Name': str(i.tags.get('Name', '')),
                'IP Address': str(i.ip_address),
                'Private IP Address': str(i.private_ip_address),
                'DNS Name': str(i.dns_name),
            }
            calls.append(call('\n' + pformat(ip_info)))

        self.app.logger.info.assert_has_calls(calls)

    def test_output_info_no_instances(self):
        """
        Output info called with no instances logs the error
        """
        self.app.logger = MagicMock()

        self.app.output_info([], self.IP, self.IP_ADDRESS)

        msg = 'No instance with {0}: {1} was found.'.format(self.IP, self.IP_ADDRESS)
        self.app.logger.error.assert_called_once_with(msg)


    def test_add_cli_arguments(self):
        """
        All convert_ip options are present in the args
        """
        self.assertEqual(self.app.parser._defaults['log_level'], self.LOG_LEVEL)

        self.assertIn('ip_address', self.app.args)
        self.assertIn('private', self.app.args)

    @patch('aws_analysis_tools.cli.convert_ip.Application.find_instances')
    @patch('aws_analysis_tools.cli.convert_ip.Application.output_info')
    def test_run(self, mock_output, mock_find):
        """
        find_instances and output_info are correctly called in run
        """
        mock_find.return_value = self.INSTANCES_LIST

        self.app.run()

        mock_find.assert_called_once_with(self.IP, self.IP_ADDRESS)
        mock_output.assert_called_once_with(self.INSTANCES_LIST, self.IP, self.IP_ADDRESS)

    def test_main(self):
        """
        Application convert_ip is instantiated and run() is called in main()
        """
        app = MagicMock()
        app_class = MagicMock(return_value=app)

        with patch('aws_analysis_tools.cli.convert_ip.Application', app_class):
            main()

        app_class.assert_called_once_with()
        app.run.assert_called_once_with()
