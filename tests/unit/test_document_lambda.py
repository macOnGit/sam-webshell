import pytest
from functions.documents.app.lambda_file import (
    lambda_handler,
    TemplateRenderError,
)
from botocore.exceptions import ClientError
import json
from docx import Document


@pytest.fixture(autouse=True)
def patched_region(monkeypatch):
    monkeypatch.setattr("functions.documents.app.lambda_file.REGION", "us-east-1")


def get_text_from_generated_document(s3resource, key, tmp_path):
    # setup
    p = tmp_path / "generated.docx"
    # download_file_to_tempfile
    s3resource.bucket.download_file(key, p)
    # read_contents to stream
    document = Document(p)
    # return contents
    return document.paragraphs[0].text


@pytest.mark.usefixtures("patched_s3_resource_output")
@pytest.mark.parametrize("event", ["general_amdt_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_template_bucket_with_templates",
    [("general_amdt_doc",)],
    indirect=True,
)
class TestHappyPath:
    def test_valid_POST_event_returns_200_and_location(
        self, filenames, event, mock_template_bucket_with_templates
    ):
        location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        response = lambda_handler(event=event, context=None)
        assert "OK" in response["body"]
        assert response["statusCode"] == 201
        assert response["headers"]["Location"] == location_url.format(
            bucket=filenames.output_bucket_name,
            region="us-east-1",
            key="documents/test.docx",
        )

    def test_passed_in_content_appears_in_generated_document(
        self,
        patched_s3_resource_output,
        mock_template_bucket_with_templates,
        event,
        tmp_path,
    ):
        event["body"] = json.dumps({"docket_number": "ABC-123US01"})
        response = lambda_handler(event=event, context=None)
        assert "OK" in response["body"]
        assert response["statusCode"] == 201
        text = get_text_from_generated_document(
            s3resource=patched_s3_resource_output,
            key="documents/test.docx",
            tmp_path=tmp_path,
        )
        assert "ABC-123US01" in text

    def test_ok_with_empty_object_body(
        self, mock_template_bucket_with_templates, event
    ):
        event["body"] = "{}"
        response = lambda_handler(event=event, context=None)
        assert "OK" in response["body"]
        assert response["statusCode"] == 201


@pytest.mark.usefixtures("patched_s3_resource_output")
@pytest.mark.parametrize("event", ["invalid_template"], indirect=True)
class TestClientErrors:
    @pytest.mark.usefixtures("patched_s3_resource_templates")
    def test_invalid_template_returns_404_not_found(self, event):
        response = lambda_handler(event=event, context=None)
        assert "Failed to get template" in response["body"]
        assert response["statusCode"] == 404

    @pytest.mark.usefixtures("patched_s3_resource_templates_with_wrong_bucket_name")
    def test_invalid_template_bucket_returns_403_forbidden(self, event):
        response = lambda_handler(event=event, context=None)
        assert "Failed to get template" in response["body"]
        assert response["statusCode"] == 403

    @pytest.mark.usefixtures("patched_s3_resource_templates")
    def test_missing_template_query_param_returns_400_bad_request(self, event: dict):
        del event["pathParameters"]["template"]
        response = lambda_handler(event=event, context=None)
        assert "Failed schema validation" in response["body"]
        assert response["statusCode"] == 400

    @pytest.mark.usefixtures("patched_s3_resource_templates")
    def test_scheme_validation_fail_with_bad_json_body(self, event: dict):
        event["body"] = "{\\}"
        response = lambda_handler(event=event, context=None)
        assert "Failed schema validation" in response["body"]
        assert response["statusCode"] == 400


@pytest.mark.parametrize("event", ["general_amdt_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_template_bucket_with_templates",
    [("general_amdt_doc",)],
    indirect=True,
)
class TestServerErrors:
    def test_failed_upload_returns_500(
        self,
        patched_s3_resource_output,
        event,
        mock_template_bucket_with_templates,
    ):
        def mock_upload_file(*args, **kwargs):
            raise ClientError(error_response={}, operation_name="")

        patched_s3_resource_output.bucket.upload_file = mock_upload_file
        response = lambda_handler(event=event, context=None)
        assert "Failed to upload generated document" in response["body"]
        assert response["statusCode"] == 500

    @pytest.mark.usefixtures("patched_s3_resource_output")
    def test_failed_render_returns_500(
        self, event, monkeypatch, mock_template_bucket_with_templates
    ):
        def mock_error(*args, **kwargs):
            raise TemplateRenderError("render fail")

        monkeypatch.setattr(
            "functions.documents.app.lambda_file.generate_document", mock_error
        )
        response = lambda_handler(event=event, context=None)
        assert "render fail" in response["body"]
        assert response["statusCode"] == 500

    @pytest.mark.usefixtures("patched_s3_resource_output")
    def test_useful_response_to_unhandled_exception(
        self, event, monkeypatch, mock_template_bucket_with_templates
    ):
        def mock_error(*args, **kwargs):
            raise Exception("Something broke")

        monkeypatch.setattr(
            "functions.documents.app.lambda_file.generate_document", mock_error
        )
        response = lambda_handler(event=event, context=None)
        assert "Something broke" in response["body"]
        assert response["statusCode"] == 500


# TODO: get generated document key name from parameter store
# See: https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/
# TODO: write recreatable content to a dynamodb table
# TODO: sns for prior art download
