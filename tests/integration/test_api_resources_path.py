import requests
import pytest


class TestDocumentsDir:

    @pytest.mark.usefixtures("template_bucket_with_templates")
    def test_get_list_of_available_documents(self, api_gateway_url):
        response = requests.get(f"{api_gateway_url}/documents")

        assert response.status_code == 200
        assert len(response.json()) == 2, "Did not find two documents in bucket"

    @pytest.mark.usefixtures(
        "template_bucket_with_templates", "generated_documents_bucket"
    )
    def test_post_returns_201_and_location_header(self, api_gateway_url):
        response = requests.post(
            f"{api_gateway_url}/documents",
            params={"template": "documents/blank_template_doc.docx"},
            json={"docket_number": "foo"},
        )
        assert "OK" in response.json()
        # TODO: don't hardcode bucket, region, or key
        assert (
            response.headers["Location"]
            == "https://webshell-dev-generated-documents.s3.us-east-1.amazonaws.com/documents/test.docx"
        )
        assert response.status_code == 201

    # def test_creates_new_doc_using_template(self):
    #     pass


class TestEmailsDir:
    pass


class TestQuestionnaires:
    # (number available set in dynamodb)
    pass
