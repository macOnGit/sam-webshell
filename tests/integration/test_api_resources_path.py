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


class TestDocumentsDir:
    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("blank_template_doc",)], indirect=True
    )
    @pytest.mark.usefixtures("generated_documents_bucket")
    def test_post_returns_201_ok_and_location_header(
        self,
        api_gateway_url,
        templates_bucket_arn,
        generated_documents_bucket_arn,
        template_bucket_with_templates,
    ):
        location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        template = "blank_template_doc.docx"
        response = requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": "documents/test document.docx",
                "templateBucket": templates_bucket_arn.split(":::")[1],
                # TODO: rename generated_documents to this
                "outputBucket": generated_documents_bucket_arn.split(":::")[1],
            },
            json={"docket_number": "foo"},
        )
        assert "OK" in response.json()
        assert response.headers["Location"] == location_url.format(
            bucket=generated_documents_bucket_arn.split(":::")[1],
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
        generated_documents_bucket,
        tmp_path,
        template_bucket_with_templates,
        templates_bucket_arn,
        generated_documents_bucket_arn,
    ):
        doc_key = "documents/test.docx"
        docket_number = "ABC-123US01"
        template = "general_amdt_doc.docx"
        requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": doc_key,
                "templateBucket": templates_bucket_arn.split(":::")[1],
                # TODO: rename generated_documents to this
                "outputBucket": generated_documents_bucket_arn.split(":::")[1],
            },
            json={"docket_number": docket_number},
        )
        text = get_text_from_generated_document(
            generated_documents_bucket, doc_key, tmp_path
        )
        assert docket_number in text

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_template_bucket_name_returns_403_error(
        self,
        api_gateway_url,
        generated_documents_bucket,
        template_bucket_with_templates,
    ):
        response = requests.post(
            f"{api_gateway_url}/documents/nope",
            params={
                # TODO: rename outDocumentKey
                "documentKey": "nope",
                "templateBucket": "does-not-exist",
                "outputBucket": "nope",
            },
            json={"docket_number": "nope"},
        )
        assert "Failed to get template" in response.json()
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_template_name_returns_404_error(
        self,
        api_gateway_url,
        generated_documents_bucket,
        template_bucket_with_templates,
        templates_bucket_arn,
    ):
        response = requests.post(
            f"{api_gateway_url}/documents/does-not-exist",
            params={
                "documentKey": "nope",
                "templateBucket": templates_bucket_arn.split(":::")[1],
                "outputBucket": "nope",
            },
            json={"docket_number": "nope"},
        )
        assert "Failed to get template" in response.json()
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("general_amdt_doc",)], indirect=True
    )
    def test_bad_generated_documents_bucket_name_returns_500_error(
        self,
        api_gateway_url,
        generated_documents_bucket,
        template_bucket_with_templates,
        templates_bucket_arn,
    ):
        template = "general_amdt_doc.docx"
        response = requests.post(
            f"{api_gateway_url}/documents/{template}",
            params={
                "documentKey": "documents/test document.docx",
                "templateBucket": templates_bucket_arn.split(":::")[1],
                # TODO: rename generated_documents to this
                "outputBucket": "does-not-exist",
            },
            json={"docket_number": "foo"},
        )
        assert "Failed to upload generated document" in response.json()
        assert response.status_code == 500


class TestEmailsDir:
    # TODO
    pass


class TestQuestionnaires:
    # TODO
    pass


# @pytest.mark.skip("TODO: move GET to seperate lambda")
# @pytest.mark.parametrize(
#     "template_bucket_with_templates",
#     [("blank_template_doc", "general_amdt_doc")],
#     indirect=True,
# )
# def test_get_list_of_available_documents(
#     self, api_gateway_url, template_bucket_with_templates
# ):
#     response = requests.get(f"{api_gateway_url}/documents")

#     assert response.status_code == 200
#     assert len(response.json()) == 2, "Did not find documents in bucket"
