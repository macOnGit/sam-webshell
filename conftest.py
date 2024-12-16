import json
from pathlib import Path
import pytest
import boto3
import os

base_path = Path(__file__).parent


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture(scope="session")
def template_bucket():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(name="webshell-dev-templates")
    yield bucket
    for key in bucket.objects.all():
        key.delete()


@pytest.fixture(scope="session")
def generated_documents_bucket():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(name="webshell-dev-generated-documents")
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
def template_bucket_with_templates(
    template_bucket, blank_template_doc, general_amdt_doc
):
    try:
        template_bucket.upload_file(blank_template_doc, "blank_template_doc.docx")
    except Exception as err:
        print(str(err))

    try:
        template_bucket.upload_file(general_amdt_doc, "general_amdt_doc.docx")
    except Exception as err:
        print(str(err))


@pytest.fixture()
def stack_outputs():
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


@pytest.fixture
def event(request):
    filename = request.param
    json_file = base_path / "events" / f"{filename}.json"
    with json_file.open() as fp:
        fixture = json.load(fp)
    return fixture
