import os
from pathlib import Path
import pytest
import boto3
from moto import mock_aws
from functions.documents.app import S3ResourceTemplates, S3ResoureGeneratedDocuments


base_path = Path(__file__).parents[2]


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
def mock_generated_documents_bucket(filenames, mock_s3_client) -> str:
    mock_s3_client.create_bucket(Bucket=filenames.generated_documents_bucket_name)
    return filenames.generated_documents_bucket_name


@pytest.fixture
def mock_s3_resource_templates(mock_templates_bucket, mock_s3_resource):
    return S3ResourceTemplates(
        {"resource": mock_s3_resource, "bucket_name": mock_templates_bucket}
    )


@pytest.fixture
def mock_s3_resource_generated_documents(
    mock_generated_documents_bucket, mock_s3_resource
):
    return S3ResoureGeneratedDocuments(
        {
            "resource": mock_s3_resource,
            "bucket_name": mock_generated_documents_bucket,
        }
    )


@pytest.fixture
def mock_s3_resource_templates_with_templates(request, mock_s3_resource_templates):
    templates = request.param
    for template in templates:
        docx_file = base_path / "fixtures" / f"{template}.docx"
        mock_s3_resource_templates.bucket.upload_file(
            docx_file, f"documents/{template}.docx"
        )
    return mock_s3_resource_templates
