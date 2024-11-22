import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway:

    def test_api_gateway(self, api_gateway_url):
        """Call the API Gateway endpoint and check the response"""
        response = requests.get(f"{api_gateway_url}/hello")

        assert response.status_code == 200
        assert response.json() == {"message": "hello world"}
