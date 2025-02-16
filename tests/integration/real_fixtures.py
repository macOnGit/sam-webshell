import json
from pathlib import Path
import os
import pytest
import boto3

base_path = Path(__file__).parents[2]


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture(scope="session")
def s3_resource():
    return boto3.resource("s3")


@pytest.fixture
def cloudformation_client():
    return boto3.client("cloudformation")


@pytest.fixture(scope="session")
def template_bucket(stack_name, s3_resource):
    bucket = s3_resource.Bucket(name=f"{stack_name}-templates")
    yield bucket
    for key in bucket.objects.all():
        key.delete()


@pytest.fixture(scope="session")
def generated_documents_bucket(stack_name, s3_resource):
    bucket = s3_resource.Bucket(name=f"{stack_name}-generated-documents")
    yield bucket
    for key in bucket.objects.all():
        key.delete()


@pytest.fixture(scope="session")
def template_bucket_with_templates(template_bucket, request):
    prefix = "documents"
    doc_names = request.param
    for doc_name in doc_names:
        doc_path = base_path / "fixtures" / f"{doc_name}.docx"
        try:
            template_bucket.upload_file(f"{doc_path}", f"{prefix}/{doc_name}.docx")
        except Exception as err:
            print(str(err))
    return doc_names


@pytest.fixture(scope="session")
def stack_name():
    _stack_name = os.environ.get("AWS_SAM_STACK_NAME")
    if _stack_name is None:
        raise ValueError(
            "Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack"
        )
    return _stack_name


@pytest.fixture()
def stack_outputs(stack_name, cloudformation_client):
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
    except Exception as e:
        raise Exception(
            f"Cannot find stack {stack_name} \n"
            f'Please make sure a stack with the name "{stack_name}" exists'
        ) from e

    stacks = response["Stacks"]
    return stacks[0]["Outputs"]


@pytest.fixture()
def api_gateway_url(stack_outputs):
    """Get the API Gateway URL from Cloudformation Stack outputs"""
    target = "RestApi"
    api_outputs = [output for output in stack_outputs if output["OutputKey"] == target]
    if not api_outputs:
        raise KeyError(f"{target} not found in stack")
    return api_outputs[0]["OutputValue"]  # Extract url from stack outputs


@pytest.fixture
def generated_documents_bucket_arn(stack_outputs):
    target = "GeneratedDocumentsBucket"
    api_outputs = [output for output in stack_outputs if output["OutputKey"] == target]
    if not api_outputs:
        raise KeyError(f"{target} not in stack")
    return api_outputs[0]["OutputValue"]  # Extract url from stack outputs


@pytest.fixture
def templates_bucket_arn(stack_outputs):
    # TODO: dupe, refactor
    target = "TemplatesBucket"
    api_outputs = [output for output in stack_outputs if output["OutputKey"] == target]
    if not api_outputs:
        raise KeyError(f"{target} not in stack")
    return api_outputs[0]["OutputValue"]  # Extract url from stack outputs


# usage: @pytest.mark.parametrize("event", ["apigw_event"], indirect=True)
@pytest.fixture
def event(request):
    # TODO: validate event scheme
    # from aws_lambda_powertools.utilities.validation import validate
    filename = request.param
    json_file = base_path / "events" / f"{filename}.json"
    with json_file.open() as fp:
        fixture = json.load(fp)
    return fixture
