# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The errors module outlines the different package specific
errors that can be raised.
"""


class PacsaniniError(Exception):
    """The PacsaniniError error is the base error that all other
    package-specific errors inherit from.
    """


class ConfigFormatError(PacsaniniError):
    """Raised when a config file is expected to be in a particular
    format but is another one.
    """


class InvalidConfigError(PacsaniniError):
    """Raised when the configuration file does not have sufficient
    information for performing certain operations.
    """


class InvalidResourceFile(PacsaniniError):
    """Raised when an input does not contain the expected formatting."""
