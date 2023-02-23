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
    from .input import Model, CertbotAwsStoreCertificate

from os import makedirs, path

import jks as pyjks
from certbot_aws_store.certificate import AcmeCertificate
from OpenSSL import crypto

from ecs_files_composer.common import LOG


def create_jks_config(
    certificate_name: str, certificate_job: CertbotAwsStoreCertificate
):
    with open(
        f"{certificate_job.storage_path}/{AcmeCertificate.full_chain_file_name}"
    ) as full_chain_fd:
        full_chain = crypto.load_certificate(crypto.FILETYPE_PEM, full_chain_fd.read())
    with open(
        f"{certificate_job.storage_path}/{AcmeCertificate.private_key_file_name}"
    ) as priv_key_fd:
        private_key = priv_key_fd.read()

    jks_path = path.abspath(
        f"{certificate_job.storage_path}/{certificate_job.jks_config.file_name}"
    )
    pkey = pyjks.jks.PrivateKeyEntry.new(
        certificate_name,
        certs=[crypto.dump_certificate(crypto.FILETYPE_ASN1, full_chain)],
        key=private_key,
        key_format="rsa_raw",
    )
    pkey.encrypt(certificate_job.jks_config.passphrase)
    keystore = pyjks.KeyStore.new("jks", [pkey])
    keystore.save(jks_path, certificate_job.jks_config.passphrase)


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
        if _definition.jks_config:
            create_jks_config(_hostname, _definition)
