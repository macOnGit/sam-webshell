import pytest
import json
from functions.app_resources.app.lambda_file import lambda_handler


@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
class TestHappyPath:

    @pytest.mark.usefixtures("patched_s3_resource_output")
    @pytest.mark.parametrize(
        "mock_template_bucket_with_templates",
        [("general_amdt_doc",)],
        indirect=True,
    )
    def test_valid_GET_request_lists_available_templates(
        self,
        event,
        monkeypatch,
        mock_template_bucket_with_templates,
    ):
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            "documents/general_amdt_doc.docx"
            in json_response["template_buckets"][0]["templates"]
        ), "Did not find document in bucket"
        assert response["statusCode"] == 200

    @pytest.mark.parametrize(
        "mock_output_bucket_with_documents",
        [("general_amdt_doc",)],
        indirect=True,
    )
    def test_valid_GET_request_lists_generated_documents(
        self,
        patched_s3_resource_templates,
        mock_output_bucket_with_documents,
        event,
        monkeypatch,
    ):
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            "documents/general_amdt_doc.docx"
            in json_response["output_buckets"][0]["documents"]
        ), "Did not find document in bucket"
        assert response["statusCode"] == 200


@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
class TestServerErrors:
    def test_unset_templates_bucket_env(self, event, monkeypatch):
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            json_response == "Missing env TEMPLATES_BUCKET"
        ), "Did not find document in bucket"
        assert response["statusCode"] == 500

    def test_unset_output_bucket_env(self, event, monkeypatch):
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            json_response == "Missing env OUTPUT_BUCKET"
        ), "Did not find document in bucket"
        assert response["statusCode"] == 500
