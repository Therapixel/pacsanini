# CLI Reference

!!! note
    This regards all pacsanini sub-commands that have an optional `-f/--config` option.
    If unset, `pacsanini` will search for a file path specified by the `PACSANINI_CONFIG`
    environment variable or a file in your home directory named `pacsaninirc.yaml`.

!!! note
    Refer to the [command configuration](../user_guide/configuration.md#command-configuration)
    section to see which configuration file settings need to be specified to run particular
    commands.

::: mkdocs-click
    :module: pacsanini.cli
    :command: entry_point
    :depth: 1
