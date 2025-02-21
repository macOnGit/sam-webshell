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


class TestHappyPath:
    @pytest.mark.parametrize("event", ["list_docs"], indirect=True)
    def test_valid_GET_request_lists_available_templates(
        self,
        patched_s3_resource_templates,
        patched_s3_resource_output,
        event,
        pytestconfig,
        monkeypatch,
    ):
        # TODO: test with bad envvars
        monkeypatch.setenv("TEMPLATES_BUCKET", "doesnt-matter")
        monkeypatch.setenv("OUTPUT_BUCKET", "doesnt-matter")
        upload_to_s3_resource(
            patched_s3_resource_templates,
            pytestconfig.rootpath,
            "documents",
            ["blank_template_doc"],
        )
        response = lambda_handler(event=event, context=None)
        assert (
            "documents/blank_template_doc.docx" in response["body"]
        ), "Did not find document in bucket"
        assert response["statusCode"] == 200

    # TODO: test gives list of already generated documents in output bucket
