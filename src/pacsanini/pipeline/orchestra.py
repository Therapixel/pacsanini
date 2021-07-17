# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The orchestra pipeline provides access to an all inclusive method
for finding, moving, and parsing DICOM resources.
"""
from typing import Union, cast

import luigi

from loguru import logger

from pacsanini.config import PacsaniniConfig
from pacsanini.errors import InvalidConfigError
from pacsanini.io import parse_dir2csv
from pacsanini.models import QueryLevel
from pacsanini.net.c_find import patient_find2csv, study_find2csv
from pacsanini.net.c_move import move_patients, move_studies
from pacsanini.utils import read_resources


# pylint: disable=no-member


class FindDICOMResources(luigi.Task):
    """This defines the task that should be performed to find the
    DICOM resources that are stored in the PACS.
    """

    config: PacsaniniConfig = luigi.Parameter()

    def output(self):
        """The find task should output results to the specified
        resources file specified in the configuration.
        """
        return luigi.LocalTarget(self.config.storage.resources)

    def run(self):
        """Run the task and find the resources."""
        args = (
            self.config.net.local_node,
            self.config.net.called_node,
            self.config.storage.resources,
        )
        kwargs = dict(
            dicom_fields=self.config.find.search_fields,
            start_date=self.config.find.start_date,
            end_date=self.config.find.end_date,
            modality=self.config.find.modality,
        )
        if self.config.find.query_level == QueryLevel.PATIENT:
            patient_find2csv(*args, **kwargs)
        else:
            study_find2csv(*args, **kwargs)


class MoveDICOMResources(luigi.Task):
    """This defines the task that should be performed to move the resources
    stored in the PACS that were previously found.
    """

    config: PacsaniniConfig = luigi.Parameter()

    def output(self):
        """At the minimum, the DICOM directory should be present."""
        return luigi.LocalTarget(self.config.storage.directory)

    def requires(self):
        """Find before moving."""
        return FindDICOMResources()

    def run(self):
        """Perform the move."""
        resources = read_resources(
            self.config.storage.resources, self.config.move.query_level
        )
        if self.config.move.query_level == QueryLevel.STUDY:
            yield from move_studies(
                self.config.net.local_node,
                self.config.net.called_node,
                study_uids=resources,
                dest_node=self.config.net.dest_node,
                sort_by=self.config.storage.sort_by,
                start_time=self.config.move.start_time,
                end_time=self.config.move.end_time,
            )
        else:
            yield from move_patients(
                self.config.net.local_node,
                self.config.net.called_node,
                patient_ids=resources,
                dest_node=self.config.net.dest_node,
                sort_by=self.config.storage.sort_by,
                start_time=self.config.move.start_time,
                end_time=self.config.move.end_time,
            )


class ParseDICOMResources(luigi.Task):
    """This defines the task of parsing DICOM files and structure
    tags.
    """

    config: PacsaniniConfig = luigi.Parameter()

    def output(self):
        """The resources meta file should be found."""
        return luigi.LocalTarget(self.config.storage.resources_meta)

    def requires(self):
        """Parse only when the moved DICOM files are present."""
        return MoveDICOMResources()

    def run(self):
        """Parse the DICOM tags."""
        parse_dir2csv(
            self.config.storage.directory,
            self.config.get_tags(),
            self.config.storage.resources_meta,
            nb_threads=4,
            include_path=True,
        )


def run_pacsanini_pipeline(config: Union[str, PacsaniniConfig]):
    """Run the complete collection and curation pipeline using the
    specified configuration.

    Parameters
    ----------
    config : Union[str, PacsaniniConfig]
        The configuration file or object to use for the collection process.

    Raises
    ------
    InvalidConfigError
        An error is raised if the given configuration does not allow for
        finding, moving, or parsing.
    """
    if isinstance(config, str):
        ext = config.rsplit(".", 1)[-1].lower()
        load_func = (
            PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
        )
        config = cast(PacsaniniConfig, load_func(config))

    if not config.can_find():
        raise InvalidConfigError("Missing find configuration.")
    if not config.can_move():
        raise InvalidConfigError("Missing move configuration.")
    if not config.can_parse():
        raise InvalidConfigError("Missing parse configuration.")

    run_result = luigi.build(
        [
            FindDICOMResources(config=config),
            MoveDICOMResources(config=config),
            ParseDICOMResources(config=config),
        ],
        detailed_summary=True,
    )

    logger.info(f"Pipeline status: {run_result.status.value}")
    logger.info(f"Summary text: {run_result.summary_text}")
