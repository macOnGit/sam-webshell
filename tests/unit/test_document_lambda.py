import pytest
from functions.documents.app import lambda_handler
from botocore.exceptions import ClientError

location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_templates_with_template", ["blank_template_doc"], indirect=True
)
def test_valid_event_returns_200_and_location(
    monkeypatch,
    filenames,
    mock_s3_generated_documents,
    mock_s3_templates_with_template,
    event,
):
    monkeypatch.setattr(
        "functions.documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_generated_documents,
    )
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_templates_with_template,
    )
    monkeypatch.setattr("functions.documents.app.REGION", "us-east-1")

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 201
    assert response["headers"]["Location"] == location_url.format(
        bucket=filenames.generated_documents_bucket_name,
        region="us-east-1",
        key="documents/test.docx",
    )
    assert response["body"] == "OK"


@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
def test_invalid_template_returns_404_template_not_found(
    monkeypatch,
    mock_s3_generated_documents,
    mock_s3_templates,
    event,
):
    monkeypatch.setattr(
        "functions.documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_generated_documents,
    )
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_templates,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 404
    assert "Failed to get template" in response["body"]


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_unset_template_bucket_name_env_returns_500_error(
    monkeypatch, mock_s3_templates, event
):
    mock_s3_templates.bucket_name = None
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_templates,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "env TEMPLATE_BUCKET_NAME unset" in response["body"]


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_unset_generated_documents_bucket_name_env_returns_500_error(
    monkeypatch, mock_s3_templates, mock_s3_generated_documents, event
):
    mock_s3_generated_documents.bucket_name = None
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_templates,
    )
    monkeypatch.setattr(
        "functions.documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_generated_documents,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "env GENERATED_DOCUMENTS_BUCKET_NAME unset" in response["body"]


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_templates_with_template", ["blank_template_doc"], indirect=True
)
def test_failed_upload_returns_500(
    monkeypatch,
    mock_s3_generated_documents,
    mock_s3_templates_with_template,
    event,
):
    def mock_upload_file(*args, **kwargs):
        raise ClientError(error_response={}, operation_name="")

    mock_s3_generated_documents.bucket.upload_file = mock_upload_file
    monkeypatch.setattr(
        "functions.documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_generated_documents,
    )
    monkeypatch.setattr(
        "functions.documents.app.S3ResourceTemplates",
        lambda _: mock_s3_templates_with_template,
    )

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "Failed to upload generated document" in response["body"]


# TODO: test_get_list_of_available_documents
