# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
Manages certbot certificates download from certbot-aws-store
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .input import Model

from certbot_aws_store.certificate import AcmeCertificate

from ecs_files_composer.common import LOG


def handle_certbot_store_certificates(job: Model) -> None:
    if not job.certbot_store:
        return
    for _hostname, _definition in job.certbot_store.items():
        certificate = AcmeCertificate(
            _hostname,
            None,
            table_name=_definition.table_name if _definition.table_name else None,
            region_name=_definition.table_region_name
            if _definition.table_region_name
            else None,
        )
        try:
            certificate.pull(_definition.storage_path)
            LOG.info("Successfully pulled certificates for %s", _hostname)
        except Exception as error:
            print(error)
            print("Failed to download certificate from certbot-aws-store", _hostname)
