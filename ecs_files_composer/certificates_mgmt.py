# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs_files_composer.input import Model as Job

import pathlib
import socket
from dataclasses import asdict
from os import path
from typing import Any

from compose_x_common.compose_x_common import keyisset
from dacite import from_dict
from OpenSSL import crypto

from ecs_files_composer.files_mgmt import File
from ecs_files_composer.input import X509CertDef


class X509Certificate(X509CertDef):
    """
    Class to wrap actions around a new X509 certificate
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.key: crypto.PKey = None
        self.cert = None
        self.key_content = None
        self.cert_content = None
        self.cert_file = None
        self.key_file = None
        self.cert_file_path = None
        self.key_file_path = None
        self.keystore = None

    def init_cert_paths(self):
        self.cert_file_path = path.abspath(f"{self.dir_path}/{self.certFileName}")
        self.key_file_path = path.abspath(f"{self.dir_path}/{self.keyFileName}")
        print(f"Creating {self.dir_path} folder")
        dir_path = pathlib.Path(path.abspath(self.dir_path))
        dir_path.mkdir(parents=True, exist_ok=True)

    def generate_key(self):
        self.key = crypto.PKey()
        self.key.generate_key(crypto.TYPE_RSA, 4096)

    def set_common_name(self):
        if self.commonName is None:
            self.commonName = socket.gethostname()

    def generate_cert(self):
        if not self.commonName:
            self.set_common_name()
        self.cert = crypto.X509()
        self.cert.get_subject().C = self.countryName
        self.cert.get_subject().ST = self.stateOrProvinceName
        self.cert.get_subject().L = self.localityName
        self.cert.get_subject().O = self.organizationName
        self.cert.get_subject().OU = self.organizationUnitName
        self.cert.get_subject().CN = self.commonName
        self.cert.get_subject().emailAddress = self.emailAddress
        self.cert.set_serial_number(0)
        self.cert.gmtime_adj_notBefore(0)
        self.cert.gmtime_adj_notAfter(int(self.validityEndInSeconds))
        self.cert.set_issuer(self.cert.get_subject())
        self.cert.set_pubkey(self.key)
        self.cert.sign(self.key, "sha512")

    def generate_cert_content(self):
        if not self.key:
            self.generate_key()
        if not self.cert:
            self.generate_cert()
        self.cert_content = crypto.dump_certificate(
            crypto.FILETYPE_PEM, self.cert
        ).decode("utf-8")
        self.key_content = crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key).decode(
            "utf-8"
        )

    def set_cert_files(self):
        if not self.cert_content or not self.key_content:
            self.generate_cert_content()
        self.key_file = from_dict(
            data_class=File,
            data={
                "content": self.key_content,
                "path": self.key_file_path,
                "mode": "0600",
                "owner": self.owner,
                "group": self.group,
            },
        )

        self.cert_file = from_dict(
            data_class=File,
            data={
                "content": self.cert_content,
                "path": self.cert_file_path,
                "mode": "0600",
                "owner": self.owner,
                "group": self.group,
            },
        )


def process_x509_certs(job):
    """Processes x509 certificates"""
    if not job.certificates or not job.certificates.x509:
        return
    for cert_path, cert_def in job.certificates.x509.items():
        cert_obj = X509Certificate(
            **asdict(cert_def),
        )
        cert_obj.dir_path = cert_path
        cert_obj.init_cert_paths()
        cert_obj.set_cert_files()
        job.certificates.x509[cert_path] = cert_obj
        if not job.files:
            job.files = {}
        job.files[cert_obj.cert_file.path] = cert_obj.cert_file
        job.files[cert_obj.key_file_path] = cert_obj.key_file
