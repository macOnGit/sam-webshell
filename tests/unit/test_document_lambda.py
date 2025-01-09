import pytest
from documents.app import lambda_handler

location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"


@pytest.mark.parametrize("event", ["blank_template_doc"], indirect=True)
@pytest.mark.parametrize(
    "mock_s3_templates_with_template", ["blank_template_doc"], indirect=True
)
def test_lambda_handler_valid_event_returns_200(
    monkeypatch,
    filenames,
    mock_s3_generated_documents,
    mock_s3_templates_with_template,
    event,
):
    monkeypatch.setattr(
        "documents.app.S3ResoureGeneratedDocuments",
        lambda _: mock_s3_generated_documents,
    )
    monkeypatch.setattr(
        "documents.app.S3ResourceTemplates", lambda _: mock_s3_templates_with_template
    )
    monkeypatch.setattr("documents.app.REGION", "us-east-1")

    response = lambda_handler(event=event, context=None)
    assert response["statusCode"] == 201
    assert response["headers"]["Location"] == location_url.format(
        bucket=filenames.generated_documents_bucket_name,
        region="us-east-1",
        key="documents/test.docx",
    )
