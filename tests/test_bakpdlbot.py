#!/usr/bin/env python

"""Tests for `bakpdlbot` package."""


import unittest
from click.testing import CliRunner

from bakpdlbot import bakpdlbot
from bakpdlbot import cli
from bakpdlbot.googledocs.ttt_sheet import findteam
from bakpdlbot.googledocs.zrl import ZrlSignups


class TestBakpdlbot(unittest.TestCase):
    """Tests for `bakpdlbot` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'bakpdlbot.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output

    def test_ttt(self):
        tname='BAKPDL 1'
        message = findteam(teamname=tname)
        #message = 'Showing all Backpedal TTT team signups' + '\n'.join([team for team in teams])
        print(message)

    def test_zrlvalues(self):
        values = ZrlSignups()
        print(values)
