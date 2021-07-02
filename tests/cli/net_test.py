# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the config functionalities of the pacsanini package
can be correctly accessed from the command line.
"""
import socket

from threading import Thread
from time import sleep

import pytest

from click.testing import CliRunner

from pacsanini.cli.net import echo_cli, server_cli


@pytest.mark.cli
@pytest.mark.net
def test_config_stdout(test_config_path):
    """Test that the net commands work well."""
    runner = CliRunner()

    result_yaml = runner.invoke(echo_cli, ["--config", test_config_path, "--debug"])
    assert result_yaml.exit_code == 0
    assert result_yaml.output


@pytest.mark.cli
class TestStorescpCli:
    """Test that a storescp server can be instantiated from the command line."""

    def setup(self):
        """Get a hold of the server thread."""
        self.server_thread: Thread = None

    def teardown(self):
        """Make sure that the server thread will be stopped."""
        if self.server_thread is not None and self.server_thread.is_alive():
            self.server_thread.join(1)

    def test_server(self, test_config_path):
        """Test that a storescp server can be started from the
        command line.
        """

        def run_server():
            runner = CliRunner()
            result = runner.invoke(
                server_cli, ["--config", test_config_path, "--debug"]
            )
            assert result.output

        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        sleep(3)  # give time for the server to start
        with pytest.raises(socket.error):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", 104))
