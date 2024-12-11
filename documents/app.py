import json
import logging
import uuid
from boto3 import resource
from botocore.exceptions import ClientError
from os import environ

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

_S3_RESOURCE_TEMPLATES = {
    "resource": resource("s3"),
    "bucket_name": environ.get("TEMPLATE_BUCKET_NAME", "NONE"),
}

_S3_RESOURCE_GENERATED_DOCUMENTS = {
    "resource": resource("s3"),
    "bucket_name": environ.get("GENERATED_DOCUMENTS_BUCKET_NAME", "NONE"),
}


logger = logging.getLogger()
logger.setLevel("INFO")


class S3Resource:
    """AWS S3 Resource Class"""

    def __init__(self, lambda_s3_resource):
        """Initialize an S3 Resource"""
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


def download_template(templates_resource, key, download_path):
    try:
        templates_resource.download_file(key, download_path)
        logger.info(f"template: {key} downloaded")
    except ClientError as e:
        logger.error(e)
        return False
    return True


def upload_generated_document(templates_resource, upload_path, key):
    try:
        templates_resource.upload_file(upload_path, key)
        logger.info(f"{key} created in {templates_resource.bucket_name} bucket")
    except ClientError as e:
        logger.error(e)
        return False
    return True


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):

    global _S3_RESOURCE_TEMPLATES
    s3resource_templates = S3Resource(_S3_RESOURCE_TEMPLATES)

    if event["httpMethod"] == "POST":

        print("###EVENT RECIEVED", event)

        download_path = f"/tmp/template-{uuid.uuid4()}.docx"

        template_downloaded = download_template(
            s3resource_templates, event["template"], download_path
        )
        if not template_downloaded:
            raise Exception("Failed to get template")
        # TODO: use jinja
        # upload_path = f"/tmp/generated-{uuid.uuid4()}.docx"
        upload_path = download_path

        # TODO: get generated docket name from dynamodb
        # TODO: generated documents shold be under /documents key
        key = "test.docx"

        global _S3_RESOURCE_GENERATED_DOCUMENTS
        s3resource_generated_documents = S3Resource(_S3_RESOURCE_GENERATED_DOCUMENTS)
        uploaded_generated_document = upload_generated_document(
            s3resource_generated_documents, key, upload_path
        )
        if not uploaded_generated_document:
            raise Exception("Failed to upload generated document")

        # TODO: write content to a dynamodb table

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Location": f"https://{s3resource_generated_documents.bucket_name}.s3.amazonaws.com/{key}",
            },
        }

    keys = [obj.key for obj in s3resource_templates.bucket.objects.all()]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(keys),
    }
