# CLI Reference

!!! note
    This regards all pacsanini sub-commands that have an optional `-f/--config` option.
    If unset, `pacsanini` will search for the following files in the provided order:

    1. A file specified by the `PACSANINI_CONFIG` environment variable;
    2. A file named `pacsaninirc.yaml` in your current directory.
    3. A file named `pacsaninirc.yaml` in your home directory.

    If none of these options correspond to an existing file and the `-f/--config` option is unset, an error will be raised.

!!! note
    Refer to the [command configuration](../user_guide/configuration.md#command-configuration)
    section to see which configuration file settings need to be specified to run particular
    commands.

::: mkdocs-click
    :module: pacsanini.cli
    :command: entry_point
    :depth: 1
