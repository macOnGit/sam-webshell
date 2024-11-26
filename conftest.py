import pytest
import boto3
import os


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture()
def api_gateway_url():
    """Get the API Gateway URL from Cloudformation Stack outputs"""
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")

    if stack_name is None:
        raise ValueError(
            "Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack"
        )

    client = boto3.client("cloudformation")

    try:
        response = client.describe_stacks(StackName=stack_name)
    except Exception as e:
        raise Exception(
            f"Cannot find stack {stack_name} \n"
            f'Please make sure a stack with the name "{stack_name}" exists'
        ) from e

    stacks = response["Stacks"]
    stack_outputs = stacks[0]["Outputs"]
    api_outputs = [
        output for output in stack_outputs if output["OutputKey"] == "RestApi"
    ]

    if not api_outputs:
        raise KeyError(f"RestAPI not found in stack {stack_name}")

    return api_outputs[0]["OutputValue"]  # Extract url from stack outputs


# TODO: this should be in events
@pytest.fixture()
def apigw_event():
    """Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }
