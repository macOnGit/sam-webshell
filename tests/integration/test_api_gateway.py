import requests


class TestApiGateway:

    def test_api_gateway(self, api_gateway_url):
        """Call the API Gateway endpoint and check the response"""
        response = requests.get(f"{api_gateway_url}/documents")

        assert response.status_code == 200
