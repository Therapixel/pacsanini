# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The parse module exposes DICOM tag parsing functionalities to the
command line.
"""
import json
import os
import sys

import yaml

from click import Choice, ClickException, Path, command, confirm, echo, option, prompt

from pacsanini.cli.base import GroupCommand, GroupOption
from pacsanini.errors import ConfigFormatError
from pacsanini.io import parse_dir2csv, parse_dir2json
from pacsanini.parse import DicomTagGroup


@command(name="parse", cls=GroupCommand)
@option(
    "-i",
    "--input",
    "src",
    cls=GroupOption,
    required=True,
    type=Path(exists=True, resolve_path=True),
    help_group="Input Options",
    help="The input directory to parse DICOM files.",
)
@option(
    "-f",
    "--config",
    cls=GroupOption,
    required=True,
    type=Path(exists=True, file_okay=True, resolve_path=True),
    help_group="Input Options",
    help="The DICOM tags configuration file to use.",
)
@option(
    "-o",
    "--output",
    cls=GroupOption,
    type=Path(resolve_path=True),
    default=None,
    help_group="Output Options",
    help="The output file to write results to. If unset, write to the standard output.",
)
@option(
    "--fmt",
    cls=GroupOption,
    type=Choice(["csv", "json"]),
    default="csv",
    show_default=True,
    help_group="Output Options",
    help=(
        "The destination format to write the results to."
        " Use if the -o/--output option is used."
    ),
)
@option(
    "--include-path",
    cls=GroupOption,
    is_flag=True,
    help_group="Output Options",
    help="Include DICOM file paths in the output results.",
)
@option(
    "-m",
    "--mode",
    cls=GroupOption,
    type=Choice(["w", "a"]),
    default="w",
    show_default=True,
    help_group="CSV Output Options",
    help="The file writing mode ([w]rite or [a]ppend).",
)
@option(
    "-t",
    "--threads",
    cls=GroupOption,
    type=int,
    default=1,
    show_default=True,
    help_group="Runtime options",
    help="The number of threads to use.",
)
def parse(
    src: str,
    config: str,
    output: str,
    fmt: str,
    include_path: bool,
    mode: str,
    threads: int,
):
    """Parse DICOM tags using the tags configuration file for the specified
    DICOM files and write the results to the output destination. Configuration
    files can be obtained using the parse-conf command.
    """
    ext = config.split(".")[-1].lower()
    if ext not in {"json", "yaml", "yml"}:
        err_msg = (
            "DICOM tag specification files should have 'json',"
            " 'yml', or 'yaml' extensions."
        )
        err_msg += f" Obtained: '{config}'"
        raise ClickException(err_msg)

    if ext == "json":
        parser = DicomTagGroup.from_json(config)
    else:
        parser = DicomTagGroup.from_yaml(config)

    if fmt == "csv":
        parse_dir2csv(
            src,
            parser,
            output if output else sys.stdout,
            nb_threads=threads,
            include_path=include_path,
            mode=mode if output else "w",
        )
    else:
        parse_dir2json(
            src,
            parser,
            output if output else sys.stdout,
            nb_threads=threads,
            include_path=include_path,
        )


@command(name="parse-conf")
@option(
    "-o",
    "--output",
    default="",
    help=(
        "The destination file to write the configuration to."
        " If unset, write to the standard output."
    ),
)
@option(
    "--fmt",
    type=Choice(["json", "yaml"]),
    default="json",
    show_default=True,
    help="The format to write the results in.",
)
def gen_parser(output: str, fmt: str):
    """Generate a DICOM tag parser configuration file with
    helpful prompts. With the configuration file ready, you
    will be able to use the parse command to extract DICOM
    tags from given DICOM files.
    """
    tags = []
    add_tags = True

    while add_tags:
        tag = {}
        tag_names = []
        tag_name_first = prompt(
            "Enter a tag name", default="", show_default=False
        ).strip()
        if not tag_name_first:
            raise ClickException("Tag names must be non-empty string values.")
        tag_names.append(tag_name_first)

        while True:
            tag_name = prompt(
                (
                    f"Add a fallback tag for '{tag_name_first}'?"
                    " (leave blank for no fallback)"
                ),
                default="",
                show_default=False,
            ).strip()
            if tag_name and tag_name != tag_name_first:
                tag_names.append(tag_name)
            else:
                break
        tag["tag_name"] = tag_names if len(tag_names) > 1 else tag_names[0]

        alias_name = prompt(
            f"Add an alias for '{tag_name_first}'? (leave blank for no alias)",
            default=tag_name_first,
        ).strip()
        if alias_name:
            tag["tag_alias"] = alias_name

        default_val = prompt(
            f"Add a default value for '{tag_name_first}' (leave blank for no default)",
            default="",
            show_default=False,
        ).strip()
        if default_val:
            tag["default_val"] = default_val

        tags.append(tag)
        add_tags = confirm("Add a new tag to parse?")
        if add_tags:
            echo("-" * 20)

    tags_conf = {"tags": tags}
    if output:
        if os.path.exists(output):
            load_func = json.load if fmt == "json" else yaml.load
            try:
                with open(output) as in_:
                    new_conf = load_func(in_)
            except (json.JSONDecodeError, yaml.YAMLError):
                raise ConfigFormatError(
                    f"{output} was expected to be in {fmt} format but is invalid."
                ) from None
            new_conf["tags"] = tags_conf["tags"]
        else:
            new_conf = tags_conf

        with open(output, "w") as out:
            if fmt == "json":
                json.dump(new_conf, out, indent=4)
            else:
                yaml.dump(new_conf, out, indent=4)
    else:
        if fmt == "json":
            echo(json.dumps(tags_conf, indent=4))
        else:
            echo(yaml.dump(tags_conf, indent=4, default_flow_style=False))
