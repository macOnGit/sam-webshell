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

region = environ["AWS_REGION"]

logger = logging.getLogger()
logger.setLevel("INFO")


class S3Resource:
    """AWS S3 Resource"""

    def __init__(self, lambda_s3_resource):
        """Initialize an S3 Resource"""
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


def download_template(s3resource: S3Resource, *, key: str, filename: str) -> bool:
    # key - name of key in source bucket
    # filename - path downloaded file
    try:
        s3resource.bucket.download_file(key, filename)
        logger.info(f"template: {key} downloaded from {s3resource.bucket_name}")
    except ClientError as e:
        logger.error(e)
        return False
    return True


def upload_generated_document(
    s3resource: S3Resource, *, key: str, filename: str
) -> bool:
    # key - name of key in target bucket
    # filename - path of file to upload
    try:
        s3resource.bucket.upload_file(filename, key)
        logger.info(f"{key} created in {s3resource.bucket_name} bucket as {key}")
    except ClientError as e:
        logger.error(e)
        return False
    return True


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):

    global _S3_RESOURCE_TEMPLATES
    s3resource_templates = S3Resource(_S3_RESOURCE_TEMPLATES)

    if event["httpMethod"] == "POST":

        print("###EVENT RECIEVED", event)

        generated_document_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
        download_path = f"/tmp/template-{uuid.uuid4()}.docx"
        template = json.loads(event["body"])["template"]

        template_downloaded = download_template(
            s3resource_templates, key=template, filename=download_path
        )
        if not template_downloaded:
            raise Exception("Failed to get template")
        # TODO: use jinja
        # upload_path = f"/tmp/generated-{uuid.uuid4()}.docx"
        upload_path = download_path

        # TODO: get generated document template name from dynamodb
        generated_document_key = "documents/test.docx"

        global _S3_RESOURCE_GENERATED_DOCUMENTS
        s3resource_generated_documents = S3Resource(_S3_RESOURCE_GENERATED_DOCUMENTS)
        uploaded_generated_document = upload_generated_document(
            s3resource_generated_documents,
            key=generated_document_key,
            filename=upload_path,
        )
        if not uploaded_generated_document:
            raise Exception("Failed to upload generated document")

        # TODO: write content to a dynamodb table

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Location": generated_document_url.format(
                    bucket=s3resource_generated_documents.bucket_name,
                    region=region,
                    key=generated_document_key,
                ),
            },
        }

    keys = [obj.key for obj in s3resource_templates.bucket.objects.all()]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(keys),
    }
