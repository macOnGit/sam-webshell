import json
import logging
import uuid
from boto3 import resource
from botocore.exceptions import ClientError
from os import environ
from pathlib import Path
from docxtpl import DocxTemplate
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

_S3_RESOURCE_TEMPLATES = {
    "resource": resource("s3"),
    "bucket_name": environ.get("TEMPLATE_BUCKET_NAME"),
}

_S3_RESOURCE_GENERATED_DOCUMENTS = {
    "resource": resource("s3"),
    "bucket_name": environ.get("GENERATED_DOCUMENTS_BUCKET_NAME"),
}

REGION = environ.get("AWS_REGION")

logger = logging.getLogger()
logger.setLevel("INFO")


class S3Resource:
    """AWS S3 Resource"""

    def __init__(self, lambda_s3_resource: dict):
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


class S3ResoureGeneratedDocuments(S3Resource):
    # seperate classes for patching
    pass


class S3ResourceTemplates(S3Resource):
    # seperate classes for patching
    pass


class TemplateNotFoundError(Exception):
    pass


class EnvUnsetError(Exception):
    pass


class UploadFailError(Exception):
    pass


def download_template(s3resource: S3Resource, *, key: str, filename: str):
    # key - name of key in source bucket
    # filename - path downloaded file
    try:
        s3resource.bucket.download_file(key, filename)
        logger.info(f"template: {key} downloaded from {s3resource.bucket_name}")
    except ClientError as e:
        logger.error(e)
        raise TemplateNotFoundError(f"Failed to get template: {key}")


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
        raise UploadFailError(f"Failed to upload generated document: {key}")


def generate_document(documentpath: Path, templatepath: Path, *args, **kwargs):
    docxtemplate = DocxTemplate(templatepath)
    docxtemplate.render(kwargs.get("content", {}), jinja_env=kwargs.get("jinja_env"))
    docxtemplate.save(documentpath)


def get_generated_document_key() -> str:
    # TODO: get generated document key name from parameter store
    return "documents/test.docx"


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):

    # TODO: seperate funcs for POST and GET

    logger.info("###EVENT RECIEVED", event)

    # Default fail
    status_code = 500
    headers = {"Content-Type": "application/json"}
    body = "Unhandled Server Error"

    try:
        global _S3_RESOURCE_TEMPLATES
        s3resource_templates = S3ResourceTemplates(_S3_RESOURCE_TEMPLATES)
        if not s3resource_templates.bucket_name:
            raise EnvUnsetError("env TEMPLATE_BUCKET_NAME unset")

        if event["httpMethod"] == "POST":
            global _S3_RESOURCE_GENERATED_DOCUMENTS
            s3resource_generated_documents = S3ResoureGeneratedDocuments(
                _S3_RESOURCE_GENERATED_DOCUMENTS
            )
            if not s3resource_generated_documents.bucket_name:
                raise EnvUnsetError("env GENERATED_DOCUMENTS_BUCKET_NAME unset")

            generated_document_url = "https://{bucket}.s3.{region}.amazonaws.com/{key}"
            download_path = Path(f"/tmp/template-{uuid.uuid4()}.docx")
            # TODO: template as queryStringParameter
            template = json.loads(event["body"])["template"]
            download_template(
                s3resource_templates, key=template, filename=download_path
            )

            upload_path = Path(f"/tmp/generated-{uuid.uuid4()}.docx")
            generate_document(documentpath=upload_path, templatepath=download_path)
            generated_document_key = get_generated_document_key()

            upload_generated_document(
                s3resource_generated_documents,
                key=generated_document_key,
                filename=upload_path,
            )

            # TODO: write recreatable content to a dynamodb table
            # TODO: sns for prior art download

            status_code = 201
            headers["Location"] = generated_document_url.format(
                bucket=s3resource_generated_documents.bucket_name,
                region=REGION,
                key=generated_document_key,
            )
            body = "OK"

        else:
            keys = [obj.key for obj in s3resource_templates.bucket.objects.all()]
            status_code = 200
            body = keys

    except TemplateNotFoundError as e:
        body = str(e)
        status_code = 404

    except EnvUnsetError as e:
        body = str(e)
        status_code = 500

    except UploadFailError as e:
        body = str(e)
        status_code = 500

    finally:
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body),
        }
