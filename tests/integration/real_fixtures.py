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
def blank_template_doc():
    return base_path / "fixtures" / "blank_template_doc.docx"


@pytest.fixture(scope="session")
def general_amdt_doc():
    return base_path / "fixtures" / "general_amdt_doc.docx"


@pytest.fixture(scope="session")
# TODO: use request param instead of blank_template_doc and general_amdt_doc
def template_bucket_with_templates(
    template_bucket, blank_template_doc, general_amdt_doc
):
    prefix = "documents"
    try:
        template_bucket.upload_file(
            blank_template_doc, f"{prefix}/blank_template_doc.docx"
        )
    except Exception as err:
        print(str(err))

    try:
        template_bucket.upload_file(general_amdt_doc, f"{prefix}/general_amdt_doc.docx")
    except Exception as err:
        print(str(err))


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
    api_outputs = [
        output for output in stack_outputs if output["OutputKey"] == "RestApi"
    ]

    if not api_outputs:
        raise KeyError(f"RestAPI not found in stack")

    return api_outputs[0]["OutputValue"]  # Extract url from stack outputs


# usage: @pytest.mark.parametrize("event", ["apigw_event"], indirect=True)
@pytest.fixture
def event(request):
    filename = request.param
    json_file = base_path / "events" / f"{filename}.json"
    with json_file.open() as fp:
        fixture = json.load(fp)
    return fixture
