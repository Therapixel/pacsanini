# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Expose configuration functionalities to the command line."""
import json
import os

from datetime import datetime

import click
import yaml

from pacsanini.config import PacsaniniConfig
from pacsanini.convert import datetime2str
from pacsanini.parse import DicomTag
from pacsanini.utils import default_config_path


def _datetime_encoder(val):
    if isinstance(val, datetime):
        return datetime2str(val)
    return val


@click.command("config")
@click.argument("conf", required=False, default=default_config_path())
@click.option(
    "--fmt",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    show_default=True,
    help="The format to output the configuration in.",
)
@click.option(
    "--edit",
    is_flag=True,
    help="If set, indicate that you want to edit the configuration file.",
)
def config_cli(conf: str, fmt: str, edit: bool):
    """Generate a default configuration file to the specified
    output file CONF. If unset, the configuration will be written
    to the default configuration file path (PACSANINI_CONFIG or
    ~/pacsaninirc.yaml)
    """
    if edit:  # pragma: no cover
        if not conf or not os.path.exists(conf):
            msg = (
                "When using --edit, you must also provide an"
                " existing file path with -o/--output."
            )
            raise click.ClickException(msg)
        click.launch(conf)
        return

    config = PacsaniniConfig(
        move={"start_time": None, "end_time": None, "query_level": "PATIENT"},
        net={
            "local_node": {"aetitle": "pacsanini_config"},
            "called_node": {
                "aetitle": "pacsanini_config",
                "ip": "localhost",
                "port": 11112,
            },
        },
        find={
            "query_level": "PATIENT",
            "search_fields": ["PatientName", "StudyInstanceUID"],
            "start_date": datetime.now().strftime("%Y%m%d"),
            "end_date": datetime.now().strftime("%Y%m%d"),
            "modality": "",
        },
        storage={
            "resources": os.path.join(os.getcwd(), "resources.csv"),
            "resources_meta": os.path.join(os.getcwd(), "resources_meta.csv"),
            "directory": os.getcwd(),
            "sort_by": "PATIENT",
        },
        tags=[
            DicomTag(tag_name=["SOPInstanceUID"], tag_alias="image_uid"),
            DicomTag(
                tag_name=["Laterality", "ImageLaterality"], tag_alias="laterality"
            ),
        ],
    )
    config_dict = config.dict(
        exclude={
            "net": {
                "local_node": {"has_net_info"},
                "called_node": {"has_net_info"},
                "dest_node": {"has_net_info"},
            }
        }
    )
    for node in config_dict["net"].values():
        node["aetitle"] = node["aetitle"].decode()

    if fmt == "json":
        with open(conf, "w") as out:
            json.dump(config_dict, out, indent=4, default=_datetime_encoder)
    else:
        with open(conf, "w") as out:
            yaml.safe_dump(config_dict, out)
