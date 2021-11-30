# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Expose custom click classes to enable prettier help messages
from the command line.
"""
import os

from collections import OrderedDict
from typing import Callable

from click import UNPROCESSED, BadParameter, Command, Option, option

from pacsanini.config import DEFAULT_CONFIG_NAME, PACSANINI_CONF_ENVVAR, PacsaniniConfig
from pacsanini.utils import default_config_path


class GroupOption(Option):
    """GroupOption enables users to group command options
    by adding the "help_group" kwarg to the @click.option
    decorator. Such options should also have cls=GroupOption
    """

    def __init__(self, *args, **kwargs):
        self.help_group = kwargs.pop("help_group", None)
        super().__init__(*args, **kwargs)


class GroupCommand(Command):
    """The GroupCommand class knows how to handle GroupOption
    instances so that they may be printed together.
    """

    def format_options(self, ctx, formatter):
        """Write all the options in the formatter if they exist."""
        opts = OrderedDict()

        for param in self.get_params(ctx):
            retval = param.get_help_record(ctx)
            if retval is not None:
                if hasattr(param, "help_group") and param.help_group:
                    opts.setdefault(str(param.help_group), []).append(retval)
                else:
                    opts.setdefault("Other Options", []).append(retval)

        for name, opts_group in opts.items():
            with formatter.section(name):
                formatter.write_dl(opts_group)


def config_option(function: Callable) -> Callable:
    """Return the configuration option that is used in most commands."""

    def validate_path(ctx, param, value):
        if not value:
            value = default_config_path()
            if not value:
                msg = (
                    "No configuration file provided and no default"
                    " configuration file in the following locations:\n"
                    f" (1) Using the {PACSANINI_CONF_ENVVAR} env var,\n"
                    f" (2) Using a {DEFAULT_CONFIG_NAME} file in your current dir,\n"
                    f" (3) Using the {DEFAULT_CONFIG_NAME} file in your homedir."
                )
                raise BadParameter(msg, ctx=ctx, param=param)

        if not os.path.exists(value):
            raise BadParameter(f"'{value}' does not exist")

        ext = value.rsplit(".", 1)[-1].lower()
        load_func = (
            PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
        )
        pacsanini_config = load_func(value)
        return pacsanini_config

    function = option(
        "-f",
        "--config",
        required=False,
        type=UNPROCESSED,
        callback=validate_path,
        help=(
            "The pacsanini configuration file to use. The order of evaluation is:"
            " (1) the value you explicitely provided,\n"
            f" (2) the value provided by the {PACSANINI_CONF_ENVVAR} env var,\n"
            f" (3) a file named {DEFAULT_CONFIG_NAME} in your current directory,\n"
            f" (4) a file named {DEFAULT_CONFIG_NAME} in your home directory.\n"
        ),
    )(function)
    return function
