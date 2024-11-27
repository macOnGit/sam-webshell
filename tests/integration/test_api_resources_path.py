import requests


class TestDocumentsDir:

    def test_get_list_of_available_documents(self, api_gateway_url):
        # 1. Available documents if there's no query string (under prefix and tagged in s3 as available)
        # call api /documents which makes call to s3
        response = requests.get(f"{api_gateway_url}/documents")

        assert response.status_code == 200
        assert len(response["content"]) == 2


class TestEmailsDir:
    pass


class TestQuestionnaires:
    # (number available set in dynamodb)
    pass