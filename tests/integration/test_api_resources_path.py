import requests
import pytest


class TestDocumentsDir:

    @pytest.mark.parametrize(
        "template_bucket_with_templates",
        [("blank_template_doc", "general_amdt_doc")],
        indirect=True,
    )
    def test_get_list_of_available_documents(
        self, api_gateway_url, template_bucket_with_templates
    ):
        response = requests.get(f"{api_gateway_url}/documents")

        assert response.status_code == 200
        assert len(response.json()) == 2, "Did not find documents in bucket"

    @pytest.mark.parametrize(
        "template_bucket_with_templates", [("blank_template_doc",)], indirect=True
    )
    @pytest.mark.usefixtures("generated_documents_bucket")
    def test_post_returns_201_ok_and_location_header(
        self,
        api_gateway_url,
        generated_documents_bucket_arn,
        template_bucket_with_templates,
    ):
        location_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        response = requests.post(
            f"{api_gateway_url}/documents",
            params={
                "template": "documents/blank_template_doc.docx",
                "documentKey": "documents/test.docx",
            },
            json={"docket_number": "foo"},
        )
        assert "OK" in response.json()
        assert response.headers["Location"] == location_url.format(
            bucket=generated_documents_bucket_arn.split(":::")[1],
            region="us-east-1",
            key="documents/test.docx",
        )
        assert response.status_code == 201

    # TODO:
    # def test_creates_new_doc_using_template(self):
    #     pass


class TestEmailsDir:
    pass


class TestQuestionnaires:
    # (number available set in dynamodb)
    pass
