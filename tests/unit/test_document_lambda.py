import pytest
from functions.documents.app import lambda_handler, S3Resource, TemplateRenderError
from botocore.exceptions import ClientError
from pathlib import Path
import json
from docx import Document


@pytest.fixture(autouse=True)
def patched_region(monkeypatch):
    monkeypatch.setattr("functions.documents.app.REGION", "us-east-1")


def upload_to_s3_resource(
    resource: S3Resource, base_path: Path, filenames: list, prefix: str
):
    for filename in filenames:
        docx_file = base_path / "fixtures" / f"{filename}.docx"
        resource.bucket.upload_file(docx_file, f"{prefix}/{filename}.docx")


def get_text_from_generated_document(s3resource, prefix, key, tmp_path):
    # setup
    filename = f"{prefix}/{key}"
    p = tmp_path / "generated.docx"
    # download_file_to_tempfile
    s3resource.bucket.download_file(filename, p)
    # read_contents to stream
    document = Document(p)
    # return contents
    return document.paragraphs[0].text


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
    assert "OK" in response["body"]


@pytest.mark.usefixtures(
    "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
)
@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
def test_invalid_template_returns_404_template_not_found(event):
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 404
    assert "Failed to get template" in response["body"]


@pytest.mark.usefixtures(
    "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
)
@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
def test_template_query_param_returns_400_bad_request(event: dict):
    del event["queryStringParameters"]["template"]
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 400
    assert "Failed schema validation" in response["body"]


@pytest.mark.usefixtures(
    "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
)
@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
def test_scheme_validation_fail_with_bad_json_body(event: dict):
    event["body"] = "{\\}"
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 400
    assert "Failed schema validation" in response["body"]


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_ok_with_empty_object_body(patched_s3_resource_templates, event, pytestconfig):
    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    event["body"] = "{}"
    response = lambda_handler(event=event, context=None)
    assert "OK" in response["body"]
    assert response["statusCode"] == 201


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


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_failed_render_returns_500(
    patched_s3_resource_templates, event, monkeypatch, pytestconfig
):
    def mock_error(*args, **kwargs):
        raise TemplateRenderError("render fail")

    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    monkeypatch.setattr("functions.documents.app.generate_document", mock_error)
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "render fail" in response["body"]


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
def test_useful_response_to_unhandled_exception(
    patched_s3_resource_templates, event, monkeypatch, pytestconfig
):
    def mock_error(*args, **kwargs):
        raise Exception("Something broke")

    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["blank_template_doc"],
        "documents",
    )
    monkeypatch.setattr("functions.documents.app.generate_document", mock_error)
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 500
    assert "Something broke" in response["body"]


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
    assert len(json.loads(response["body"])) == 1
    assert (
        "documents/blank_template_doc.docx" in response["body"]
    ), "Did not find document in bucket"


@pytest.mark.usefixtures("patched_s3_resource_generated_documents")
@pytest.mark.parametrize("event", ["general_amdt_doc"], indirect=True)
def test_passed_in_content_appears_in_generated_document(
    patched_s3_resource_generated_documents,
    patched_s3_resource_templates,
    event,
    pytestconfig,
    tmp_path,
):
    # TODO: code smell
    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        ["general_amdt_doc"],
        "documents",
    )
    event["body"] = json.dumps({"docket_number": "ABC-123US01"})
    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 201
    text = get_text_from_generated_document(
        s3resource=patched_s3_resource_generated_documents,
        prefix="documents",
        key="test.docx",
        tmp_path=tmp_path,
    )
    assert "ABC-123US01" in text
