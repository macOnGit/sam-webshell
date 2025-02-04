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
    resource: S3Resource, base_path: Path, prefix: str, filenames: list
):
    for filename in filenames:
        docx_file = base_path / "fixtures" / f"{filename}.docx"
        resource.bucket.upload_file(docx_file, f"{prefix}/{filename}.docx")


def get_text_from_generated_document(s3resource, key, tmp_path):
    # setup
    p = tmp_path / "generated.docx"
    # download_file_to_tempfile
    s3resource.bucket.download_file(key, p)
    # read_contents to stream
    document = Document(p)
    # return contents
    return document.paragraphs[0].text


class TestHappyPath:
    @pytest.mark.usefixtures("patched_s3_resource_generated_documents")
    @pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
    def test_valid_POST_event_returns_200_and_location(
        self, filenames, patched_s3_resource_templates, event, pytestconfig
    ):
        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        response = lambda_handler(event=event, context=None)
        assert "OK" in response["body"]
        assert response["statusCode"] == 201
        assert response["headers"]["Location"] == location_url.format(
            bucket=filenames.generated_documents_bucket_name,
            region="us-east-1",
            key="documents/test.docx",
        )

    @pytest.mark.usefixtures("patched_s3_resource_generated_documents")
    @pytest.mark.parametrize("event", ["general_amdt_doc"], indirect=True)
    def test_passed_in_content_appears_in_generated_document(
        self,
        patched_s3_resource_generated_documents,
        patched_s3_resource_templates,
        event,
        pytestconfig,
        tmp_path,
    ):
        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["general_amdt_doc"],
        )
        event["body"] = json.dumps({"docket_number": "ABC-123US01"})
        response = lambda_handler(event=event, context=None)
        assert response["statusCode"] == 201
        text = get_text_from_generated_document(
            s3resource=patched_s3_resource_generated_documents,
            key="documents/test.docx",
            tmp_path=tmp_path,
        )
        assert "ABC-123US01" in text

    @pytest.mark.usefixtures("patched_s3_resource_generated_documents")
    @pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
    def test_ok_with_empty_object_body(
        self, patched_s3_resource_templates, event, pytestconfig
    ):
        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        event["body"] = "{}"
        response = lambda_handler(event=event, context=None)
        assert "OK" in response["body"]
        assert response["statusCode"] == 201


class TestClientErrors:
    @pytest.mark.usefixtures(
        "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
    )
    @pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
    def test_invalid_template_returns_404_template_not_found(self, event):
        response = lambda_handler(event=event, context=None)
        assert "Failed to get template" in response["body"]
        assert response["statusCode"] == 404

    @pytest.mark.usefixtures(
        "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
    )
    @pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
    def test_template_query_param_returns_400_bad_request(self, event: dict):
        del event["queryStringParameters"]["template"]
        response = lambda_handler(event=event, context=None)
        assert "Failed schema validation" in response["body"]
        assert response["statusCode"] == 400

    @pytest.mark.usefixtures(
        "patched_s3_resource_generated_documents", "patched_s3_resource_templates"
    )
    @pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
    def test_scheme_validation_fail_with_bad_json_body(self, event: dict):
        event["body"] = "{\\}"
        response = lambda_handler(event=event, context=None)
        assert "Failed schema validation" in response["body"]
        assert response["statusCode"] == 400


class TestServerErrors:
    @pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
    def test_failed_upload_returns_500(
        self,
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
            "documents",
            ["blank_template_doc"],
        )
        patched_s3_resource_generated_documents.bucket.upload_file = mock_upload_file
        response = lambda_handler(event=event, context=None)
        assert "Failed to upload generated document" in response["body"]
        assert response["statusCode"] == 500

    @pytest.mark.usefixtures("patched_s3_resource_generated_documents")
    @pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
    def test_failed_render_returns_500(
        self, patched_s3_resource_templates, event, monkeypatch, pytestconfig
    ):
        def mock_error(*args, **kwargs):
            raise TemplateRenderError("render fail")

        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        monkeypatch.setattr("functions.documents.app.generate_document", mock_error)
        response = lambda_handler(event=event, context=None)
        assert "render fail" in response["body"]
        assert response["statusCode"] == 500

    @pytest.mark.usefixtures("patched_s3_resource_generated_documents")
    @pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
    def test_useful_response_to_unhandled_exception(
        self, patched_s3_resource_templates, event, monkeypatch, pytestconfig
    ):
        def mock_error(*args, **kwargs):
            raise Exception("Something broke")

        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        monkeypatch.setattr("functions.documents.app.generate_document", mock_error)
        response = lambda_handler(event=event, context=None)
        assert "Something broke" in response["body"]
        assert response["statusCode"] == 500


@pytest.mark.skip("TODO: move GET to seperate lambda")
@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
def test_valid_GET_request_lists_available_templates(
    patched_s3_resource_templates, event, pytestconfig
):
    upload_to_s3_resource(
        patched_s3_resource_templates,
        pytestconfig.rootpath,
        "documents",
        ["blank_template_doc"],
    )
    response = lambda_handler(event=event, context=None)
    assert len(json.loads(response["body"])) == 1
    assert (
        "documents/blank_template_doc.docx" in response["body"]
    ), "Did not find document in bucket"
    assert response["statusCode"] == 200


# TODO: get generated document key name from parameter store
# See: https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/

# TODO: write recreatable content to a dynamodb table
# TODO: sns for prior art download
