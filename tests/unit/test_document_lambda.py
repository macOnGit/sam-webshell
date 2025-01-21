import pytest
from functions.documents.app import lambda_handler, S3Resource
from botocore.exceptions import ClientError
from pathlib import Path
import json


@pytest.fixture(autouse=True)
def patched_region(monkeypatch):
    monkeypatch.setattr("functions.documents.app.REGION", "us-east-1")


def upload_to_s3_resource(
    resource: S3Resource, base_path: Path, filenames: list, prefix: str
):
    for filename in filenames:
        docx_file = base_path / "fixtures" / f"{filename}.docx"
        resource.bucket.upload_file(docx_file, f"{prefix}/{filename}.docx")


# TODO: first refactor to send context as body of request then do this
# def get_text_from_generated_document(response):
#     pass


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_valid_POST_event_returns_200_and_location(
    filenames, patched_s3_resource_templates, event, pytestconfig
):
    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 201
    assert response["headers"]["Location"] == location_url.format(
        bucket=filenames.generated_documents_bucket_name,
        region="us-east-1",
        key="documents/test.docx",
    )
    assert json.loads(response["body"]) == "OK"


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
def test_failed_upload_returns_500(
    patched_s3_resource_generated_documents,
    patched_s3_resource_templates,
    event,
    pytestconfig,
):
    def mock_upload_file(*args, **kwargs):
        raise ClientError(error_response={}, operation_name="")

    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    patched_s3_resource_generated_documents.bucket.upload_file = mock_upload_file
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "Failed to upload generated document" in response["body"]


@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
def test_valid_GET_request_lists_available_templates(
    patched_s3_resource_templates, event, pytestconfig
):
    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 200
    assert (
        json.loads(response["body"])[0] == "documents/blank_template_doc.docx"
    ), "Did not find document in bucket"


# TODO: first refactor to send context as body of request then do this
# @pytest.mark.parametrize("event", ["general_amendment"], indirect=True)
# def test_passed_in_content_appears_in_generated_document(
#     patched_s3_resource_templates, event, pytestconfig
# ):
#     upload_to_s3_resource(
#         patched_s3_resource_templates,
#         pytestconfig.rootpath,
#         ["blank_template_doc"],
#         "documents",
#     )
#     response = lambda_handler(event=event, context=None)
#     assert response["statusCode"] == 201
#     text = get_text_from_generated_document(response)
#     assert "ABC-123US01" in text
