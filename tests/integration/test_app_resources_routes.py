import requests
import pytest


class TestHappyPath:
    @pytest.mark.parametrize(
        "template_bucket_with_templates",
        [("blank_template_doc",)],
        indirect=True,
    )
    def test_get_list_of_available_documents(
        self, api_gateway_url, template_bucket_with_templates
    ):
        response = requests.get(f"{api_gateway_url}/resources")
        assert (
            "documents/blank_template_doc.docx"
            in response.json()["templates"][0]["templates"]
        ), "Did not find document in bucket"
        assert response.status_code == 200
