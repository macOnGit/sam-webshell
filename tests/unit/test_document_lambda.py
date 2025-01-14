import pytest
from functions.documents.app import lambda_handler
from botocore.exceptions import ClientError
import json

location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"


@pytest.fixture
def patched_s3_resource_generated_documents(
    monkeypatch, mock_s3_resource_generated_documents
):
    monkeypatch.setattr(
        "functions.documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_resource_generated_documents,
    )
    return mock_s3_resource_generated_documents


@pytest.fixture
def patched_s3_resource_templates(monkeypatch, mock_s3_resource_templates):
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates,
    )
    return mock_s3_resource_templates


@pytest.fixture(autouse=True)
def patched_region(monkeypatch):
    monkeypatch.setattr("functions.documents.app.REGION", "us-east-1")


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_resource_templates_with_templates",
    [("blank_template_doc",)],
    indirect=True,
)
def test_valid_POST_event_returns_200_and_location(
    monkeypatch,
    filenames,
    mock_s3_resource_templates_with_templates,
    event,
):
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates_with_templates,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 201
    assert response["headers"]["Location"] == location_url.format(
        bucket=filenames.generated_documents_bucket_name,
        region="us-east-1",
        key="documents/test.docx",
    )
    assert response["body"] == "OK"


@pytest.mark.usefixtures(
    "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
)
@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
def test_invalid_template_returns_404_template_not_found(event):
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 404
    assert "Failed to get template" in response["body"]


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_unset_template_bucket_name_env_returns_500_error(
    patched_s3_resource_templates, event
):
    patched_s3_resource_templates.bucket_name = None
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "env TEMPLATE_BUCKET_NAME unset" in response["body"]


@pytest.mark.usefixtures("patched_s3_resource_templates")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_unset_generated_documents_bucket_name_env_returns_500_error(
    patched_s3_resource_generated_documents,
    event,
):
    patched_s3_resource_generated_documents.bucket_name = None
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "env GENERATED_DOCUMENTS_BUCKET_NAME unset" in response["body"]


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_resource_templates_with_templates",
    [("blank_template_doc",)],
    indirect=True,
)
def test_failed_upload_returns_500(
    monkeypatch,
    patched_s3_resource_generated_documents,
    mock_s3_resource_templates_with_templates,
    event,
):
    def mock_upload_file(*args, **kwargs):
        raise ClientError(error_response={}, operation_name="")

    patched_s3_resource_generated_documents.bucket.upload_file = mock_upload_file
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates_with_templates,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "Failed to upload generated document" in response["body"]


@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_resource_templates_with_templates",
    [("blank_template_doc",)],
    indirect=True,
)
def test_valid_GET_request_lists_available_templates(
    monkeypatch, mock_s3_resource_templates_with_templates, event
):
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_resource_templates_with_templates,
    )
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 200
    assert (
        json.loads(response["body"])[0] == "documents/blank_template_doc.docx"
    ), "Did not find document in bucket"
