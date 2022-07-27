# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

import pathlib
import socket
from os import path
from typing import Any

from OpenSSL import crypto

from ecs_files_composer.files_mgmt import File
from ecs_files_composer.input import X509CertDef


class X509Certificate(X509CertDef):
    """
    Class to wrap actions around a new X509 certificate
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.key = None
        self.cert = None
        self.key_content = None
        self.cert_content = None
        self.cert_file = None
        self.key_file = None
        self.cert_file_path = None
        self.key_file_path = None

    def init_cert_paths(self):
        self.cert_file_path = path.abspath(f"{self.dir_path}/{self.cert_file_name}")
        self.key_file_path = path.abspath(f"{self.dir_path}/{self.key_file_name}")
        print(f"Creating {self.dir_path} folder")
        dir_path = pathlib.Path(path.abspath(self.dir_path))
        dir_path.mkdir(parents=True, exist_ok=True)

    def generate_key(self):
        self.key = crypto.PKey()
        self.key.generate_key(crypto.TYPE_RSA, 4096)

    def set_common_name(self):
        if self.common_name is None:
            self.common_name = socket.gethostname()

    def generate_cert(self):
        if not self.common_name:
            self.set_common_name()
        self.cert = crypto.X509()
        self.cert.get_subject().C = self.country_name
        self.cert.get_subject().ST = self.state_or_province_name
        self.cert.get_subject().L = self.locality_name
        self.cert.get_subject().O = self.organization_name
        self.cert.get_subject().OU = self.organization_unit_name
        self.cert.get_subject().CN = self.common_name
        self.cert.get_subject().emailAddress = self.email_address
        self.cert.set_serial_number(0)
        self.cert.gmtime_adj_notBefore(0)
        self.cert.gmtime_adj_notAfter(int(self.validity_end_in_seconds))
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
        self.key_file = File().parse_obj(
            {
                "content": self.key_content,
                "path": self.key_file_path,
                "mode": "0600",
                "owner": self.owner,
                "group": self.group,
            }
        )
        self.cert_file = File().parse_obj(
            {
                "content": self.cert_content,
                "path": self.cert_file_path,
                "mode": "0600",
                "owner": self.owner,
                "group": self.group,
            }
        )


def process_x509_certs(job):
    """

    :param ecs_files_composer.input.Model job:
    :return:
    """
    if not hasattr(job.certificates, "x509") or not job.certificates.x509:
        return
    for cert_path, cert_def in job.certificates.x509.items():
        cert_obj = X509Certificate(
            **(cert_def.dict(by_alias=True)),
        )
        cert_obj.dir_path = cert_path
        cert_obj.init_cert_paths()
        cert_obj.set_cert_files()
        job.certificates.x509[cert_path] = cert_obj
        job.files[cert_obj.cert_file.path] = cert_obj.cert_file
        job.files[cert_obj.key_file_path] = cert_obj.key_file
