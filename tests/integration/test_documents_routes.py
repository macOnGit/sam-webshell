import requests
import pytest
from docx import Document


def get_text_from_generated_document(bucket, key, tmp_path):
    # setup
    p = tmp_path / "generated.docx"
    # download_file_to_tempfile
    bucket.download_file(key, p)
    # read_contents to stream
    document = Document(p)
    # return contents
    return document.paragraphs[0].text


# TODO: rename to match other tests
class TestDocumentsDir:
    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("blank_template_doc",)], indirect=True
    )
    @pytest.mark.usefixtures("output_bucket")
    def test_post_returns_201_ok_and_location_header(
        self,
        api_gateway_url,
        templates_bucket_arn,
        output_bucket_arn,
        template_bucket_with_templates,
    ):
        location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        template = "blank_template_doc.docx"
        response = requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": "documents/test document.docx",
                "templateBucket": templates_bucket_arn,
                "outputBucket": output_bucket_arn,
            },
            json={"docket_number": "not-checked"},
        )
        assert "OK" in response.json()
        assert response.headers["Location"] == location_url.format(
            bucket=output_bucket_arn.split(":::")[1],
            region="us-east-1",
            key="documents/test document.docx",
        )
        assert response.status_code == 201

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_creates_new_doc_using_template_and_content(
        self,
        api_gateway_url,
        output_bucket,
        tmp_path,
        template_bucket_with_templates,
        templates_bucket_arn,
        output_bucket_arn,
    ):
        doc_key = "documents/test.docx"
        docket_number = "ABC-123US01"
        template = "general_amdt_doc.docx"
        requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": doc_key,
                "templateBucket": templates_bucket_arn,
                "outputBucket": output_bucket_arn,
            },
            json={"docket_number": docket_number},
        )
        text = get_text_from_generated_document(output_bucket, doc_key, tmp_path)
        assert docket_number in text

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_template_bucket_name_returns_403_error(
        self,
        api_gateway_url,
        output_bucket,
        template_bucket_with_templates,
    ):
        response = requests.post(
            f"{api_gateway_url}/documents/nope",
            params={
                "documentKey": "nope",
                "templateBucket": "arn:aws:s3:::does-not-exist",
                "outputBucket": "arn:aws:s3:::not-checked",
            },
            json={"docket_number": "not-checked"},
        )
        assert "Failed to get template" in response.json()
        assert response.status_code == 403, "Did not return 403"

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_template_name_returns_404_error(
        self,
        api_gateway_url,
        output_bucket,
        template_bucket_with_templates,
        templates_bucket_arn,
    ):
        response = requests.post(
            f"{api_gateway_url}/documents/does-not-exist",
            params={
                "documentKey": "arn:aws:s3:::not-checked",
                "templateBucket": templates_bucket_arn,
                "outputBucket": "arn:aws:s3:::not-checked",
            },
            json={"docket_number": "nope"},
        )
        assert "Failed to get template" in response.json()
        assert response.status_code == 404, "Did not return 404"

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_output_bucket_name_returns_500_error(
        self,
        api_gateway_url,
        output_bucket,
        template_bucket_with_templates,
        templates_bucket_arn,
    ):
        template = "general_amdt_doc.docx"
        response = requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": "documents/test document.docx",
                "templateBucket": templates_bucket_arn,
                "outputBucket": "arn:aws:s3:::does-not-exist",
            },
            json={"docket_number": "not-checked"},
        )
        assert "Failed to upload generated document" in response.json()
        assert response.status_code == 500
