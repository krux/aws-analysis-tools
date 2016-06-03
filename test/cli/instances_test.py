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
        All CLI arguments are added for instances_2.py
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
        Application is instantiated and run() is called in main() for instances_2.py
        """
        app = MagicMock()
        app_class = MagicMock(return_value=app)

        with patch('aws_analysis_tools.cli.instances_2.Application', app_class):
            main()

        app_class.assert_called_once_with()
        app.run.assert_called_once_with()