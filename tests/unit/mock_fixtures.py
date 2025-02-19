import os
import pytest
import boto3
from moto import mock_aws
from functions.documents.app.lambda_file import (
    S3ResourceTemplates,
    S3ResoureOutput,
)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    # NOTE: fixtures cannot use usefixture
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def mock_s3_client(aws_credentials):
    """Return a mocked S3 client"""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_resource(aws_credentials):
    """Return a mocked S3 resource"""
    with mock_aws():
        yield boto3.resource("s3")


@pytest.fixture
def mock_templates_bucket(filenames, mock_s3_client) -> str:
    mock_s3_client.create_bucket(Bucket=filenames.template_bucket_name)
    return filenames.template_bucket_name


@pytest.fixture
def mock_output_bucket(filenames, mock_s3_client) -> str:
    mock_s3_client.create_bucket(Bucket=filenames.output_bucket_name)
    return filenames.output_bucket_name


@pytest.fixture
def mock_s3_resource_templates(mock_templates_bucket, mock_s3_resource):
    return S3ResourceTemplates(
        {
            "resource": mock_s3_resource,
            "bucket_name": mock_templates_bucket,
        }
    )


@pytest.fixture
def mock_s3_resource_templates_with_wrong_bucket_name(
    mock_templates_bucket, mock_s3_resource
):
    return S3ResourceTemplates(
        {
            "resource": mock_s3_resource,
            "bucket_name": "wrong-name",
        }
    )


@pytest.fixture
def mock_s3_resource_output(mock_output_bucket, mock_s3_resource):
    return S3ResoureOutput(
        {
            "resource": mock_s3_resource,
            "bucket_name": mock_output_bucket,
        }
    )


@pytest.fixture
def patched_s3_resource_output(monkeypatch, mock_s3_resource_output):
    monkeypatch.setattr(
        "functions.documents.app.lambda_file.S3ResoureOutput",
        lambda _: mock_s3_resource_output,
    )
    return mock_s3_resource_output


@pytest.fixture
def patched_s3_resource_templates(monkeypatch, mock_s3_resource_templates):
    monkeypatch.setattr(
        "functions.documents.app.lambda_file.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates,
    )
    return mock_s3_resource_templates


@pytest.fixture
def patched_s3_resource_templates_with_wrong_bucket_name(
    monkeypatch, mock_s3_resource_templates_with_wrong_bucket_name
):
    monkeypatch.setattr(
        "functions.documents.app.lambda_file.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates_with_wrong_bucket_name,
    )
    return mock_s3_resource_templates_with_wrong_bucket_name
