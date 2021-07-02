# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Expose custom click classes to enable prettier help messages
from the command line.
"""
from collections import OrderedDict

from click import Command, Option


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
