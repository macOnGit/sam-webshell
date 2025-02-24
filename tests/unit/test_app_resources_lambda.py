import pytest
from pathlib import Path
import json
from functions.app_resources.app.lambda_file import (
    lambda_handler,
    S3Resource,
)


# TODO: dupe from test_document_lambda
def upload_to_s3_resource(
    resource: S3Resource, base_path: Path, prefix: str, filenames: list
):
    for filename in filenames:
        docx_file = base_path / "fixtures" / f"{filename}.docx"
        resource.bucket.upload_file(docx_file, f"{prefix}/{filename}.docx")


@pytest.mark.parametrize("event", ["list_docs"], indirect=True)
class TestHappyPath:
    def test_valid_GET_request_lists_available_templates(
        self,
        patched_s3_resource_templates,
        patched_s3_resource_output,
        event,
        pytestconfig,
        monkeypatch,
    ):
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            "documents/blank_template_doc.docx"
            in json_response["template_buckets"][0]["templates"]
        ), "Did not find document in bucket"
        assert response["statusCode"] == 200

    def test_valid_GET_request_lists_generated_documents(
        self,
        patched_s3_resource_templates,
        patched_s3_resource_output,
        event,
        pytestconfig,
        monkeypatch,
    ):
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        upload_to_s3_resource(
            patched_s3_resource_output,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        response = lambda_handler(event=event, context=None)
        json_response = json.loads(response["body"])
        assert (
            "documents/blank_template_doc.docx"
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
