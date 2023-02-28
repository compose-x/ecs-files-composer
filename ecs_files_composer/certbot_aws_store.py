# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
Manages certbot certificates download from certbot-aws-store
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from boto3.session import Session

if TYPE_CHECKING:
    from .input import Model

from os import makedirs, path

from certbot_aws_store.certificate import AcmeCertificate

from ecs_files_composer.common import LOG


def process_certbot_aws_store_certificates(job: Model) -> None:
    """
    Pulls certificates from certbot-aws-store to local filesystem
    If the path does not exist, creates a new directory for download.
    """
    if not job.certbot_store:
        return
    default_table_name = job.certbot_store.certificates_registry_table_name
    if job.certbot_store.certificates_registry_table_region:
        default_table_region = job.certbot_store.certificates_registry_table_region
    else:
        default_table_region = os.getenv("AWS_DEFAULT_REGION", Session().region_name)
    for _hostname, _definition in job.certbot_store.certificates.items():
        certificate = AcmeCertificate(
            _hostname,
            None,
            table_name=_definition.certificates_registry_table_name
            if _definition.certificates_registry_table_name
            else default_table_name,
            region_name=_definition.certificates_registry_table_region
            if _definition.certificates_registry_table_region
            else default_table_region,
        )
        if not path.exists(_definition.storage_path):
            makedirs(_definition.storage_path, exist_ok=True)
        try:
            certificate.pull(_definition.storage_path)
            LOG.info("Successfully pulled certificates for %s", _hostname)
        except Exception as error:
            LOG.exception(error)
            LOG.error(
                "Failed to download certificate from certbot-aws-store", _hostname
            )
