import requests
import pytest


class TestDocumentsDir:

    @pytest.mark.usefixtures("template_bucket_with_templates")
    def test_get_list_of_available_documents(self, api_gateway_url):
        # 1. Available documents if there's no query string (under prefix and tagged in s3 as available)
        # call api /documents which makes call to s3
        response = requests.get(f"{api_gateway_url}/documents")

        assert response.status_code == 200
        assert len(response.json()) == 2, "Did not find two documents in bucket"


class TestEmailsDir:
    pass


class TestQuestionnaires:
    # (number available set in dynamodb)
    pass
