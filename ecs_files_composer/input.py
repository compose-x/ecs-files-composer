# generated by datamodel-codegen:
#   filename:  ecs-files-input.json

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

S3Uri = str


ComposeXUri = str


class Encoding(str, Enum):
    base64 = "base64"
    plain = "plain"


class Context(str, Enum):
    plain = "plain"
    jinja2 = "jinja2"


@dataclass
class IgnoreFailureItem:
    commands: Optional[bool] = False
    mode: Optional[bool] = False
    owner: Optional[bool] = False
    source_download: Optional[bool] = False


@dataclass
class UrlDef:
    Url: Optional[str] = None
    Username: Optional[str] = None
    Password: Optional[str] = None


@dataclass
class IamOverrideDef:
    """
    When source points to AWS, allows to indicate if another role should be used
    """

    RoleArn: Optional[str] = None
    SessionName: Optional[str] = "S3File@EcsConfigComposer"
    ExternalId: Optional[str] = None
    RegionName: Optional[str] = None
    AccessKeyId: Optional[str] = None
    SecretAccessKey: Optional[str] = None
    SessionToken: Optional[str] = None


@dataclass
class CommandsDefItem:
    """
    Command to run with options
    """

    command: Optional[str] = None
    display_output: Optional[bool] = False
    ignore_error: Optional[bool] = False


CommandsDef = List[Union[str, CommandsDefItem]]


@dataclass
class X509CertDef:
    keyFileName: str
    certFileName: str
    dir_path: Optional[str] = None
    emailAddress: Optional[str] = "files-composer@compose-x.tld"
    commonName: Optional[str] = None
    countryName: Optional[str] = "ZZ"
    localityName: Optional[str] = "Anywhere"
    stateOrProvinceName: Optional[str] = "Shire"
    organizationName: Optional[str] = "NoOne"
    organizationUnitName: Optional[str] = "Automation"
    validityEndInSeconds: Optional[float] = 8035200
    group: Optional[str] = "root"
    owner: Optional[str] = "root"


@dataclass
class Certificates:
    x509: Optional[Dict[str, X509CertDef]] = None


@dataclass
class Commands:
    post: Optional[CommandsDef] = None
    pre: Optional[CommandsDef] = None


@dataclass
class SsmDef:
    ParameterName: Optional[str] = None
    IamOverride: Optional[IamOverrideDef] = None


@dataclass
class SecretDef:
    SecretId: str
    VersionId: Optional[str] = None
    VersionStage: Optional[str] = None
    JsonKey: Optional[str] = None
    IamOverride: Optional[IamOverrideDef] = None


@dataclass
class S3Def:
    S3Uri: Optional[S3Uri] = None
    ComposeXUri: Optional[ComposeXUri] = None
    BucketName: Optional[str] = None
    BucketRegion: Optional[str] = None
    Key: Optional[str] = None
    IamOverride: Optional[IamOverrideDef] = None


@dataclass
class SourceDef:
    Url: Optional[UrlDef] = None
    Ssm: Optional[SsmDef] = None
    S3: Optional[S3Def] = None
    Secret: Optional[SecretDef] = None


@dataclass
class FileDef:
    path: Optional[str] = None
    content: Optional[str] = None
    source: Optional[SourceDef] = None
    encoding: Optional[Encoding] = "plain"
    group: Optional[str] = "root"
    owner: Optional[str] = "root"
    mode: Optional[str] = "0644"
    context: Optional[Context] = "plain"
    ignore_failure: Optional[Union[IgnoreFailureItem, bool]] = None
    commands: Optional[Commands] = None


@dataclass
class Model:
    """
    Configuration input definition for ECS Files Composer
    """

    files: Optional[Dict[str, FileDef]] = None
    certificates: Optional[Certificates] = None
    IamOverride: Optional[IamOverrideDef] = None
