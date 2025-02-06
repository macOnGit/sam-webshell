import json
import logging
import uuid
from boto3 import resource
from botocore.exceptions import ClientError
from boto3.exceptions import S3UploadFailedError
from os import environ
from pathlib import Path
from docxtpl import DocxTemplate
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError

# TODO: put into seperate file
INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/documents.schema.json",
    "title": "Document Content",
    "description": "Content for a document",
    "type": "object",
    "required": ["queryStringParameters", "body"],
    "properties": {
        "queryStringParameters": {
            "description": "The template to base the document on",
            "type": "object",
            "required": ["template", "documentKey", "templateBucket", "outputBucket"],
            "properties": {
                # TODO: pass template in as path param
                "template": {
                    "$id": "#/properties/queryStringParameters/template",
                    "type": "string",
                },
                "documentKey": {
                    "$id": "#/properties/queryStringParameters/documentKey",
                    "type": "string",
                },
                "templateBucket": {
                    "$id": "#/properties/queryStringParameters/templateBucket",
                    "type": "string",
                },
                "outputBucket": {
                    "$id": "#/properties/queryStringParameters/outputBucket",
                    "type": "string",
                },
            },
        },
        "body": {
            "description": "Content for the template to render",
            "type": "string",
            "contentMediaType": "application/json",
        },
    },
}

# TODO :code smell - maybe just pass bucket name to S3Resource class?
_S3_RESOURCE_TEMPLATES = {
    "resource": resource("s3"),
    "bucket_name": None,
}

_S3_RESOURCE_GENERATED_DOCUMENTS = {
    "resource": resource("s3"),
    "bucket_name": None,
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


class DownloadFailError(Exception):
    pass


class UploadFailError(Exception):
    pass


class TemplateRenderError(Exception):
    pass


def download_template(s3resource: S3Resource, *, key: str, filename: str):
    # key - name of key in source bucket
    # filename - path for downloaded file
    try:
        s3resource.bucket.download_file(key, filename)
        logger.info(f"template: {key} downloaded from {s3resource.bucket_name}")
    except ClientError as e:
        # TODO: specify 403 Forbidden or 404 not found
        logger.error(e)
        raise DownloadFailError(
            f"Failed to get template: {key} from {s3resource.bucket_name}"
        )


def upload_generated_document(
    s3resource: S3Resource, *, key: str, filename: str
) -> bool:
    # key - name of key in target bucket
    # filename - path of file to upload
    try:
        s3resource.bucket.upload_file(filename, key)
        logger.info(f"{key} created in {s3resource.bucket_name} bucket")
    except (ClientError, S3UploadFailedError) as e:
        logger.error(e)
        raise UploadFailError(
            f"Failed to upload generated document: {key} to {s3resource.bucket_name}"
        )


def generate_document(documentpath: Path, templatepath: Path, *args, **kwargs):
    content = kwargs.get("content", {})
    try:
        docxtemplate = DocxTemplate(templatepath)
        docxtemplate.render(content, jinja_env=kwargs.get("jinja_env"))
        docxtemplate.save(documentpath)
        logger.info(f"Rendered {str(templatepath)} template with {json.dumps(content)}")
    except Exception as e:
        logger.error(e)
        raise TemplateRenderError(
            f"Failed to render error: {str(e)} "
            f"template: {str(templatepath)} "
            f"content: {json.dumps(content)}"
        )


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):
    logger.info("###EVENT RECIEVED")
    logger.info(json.dumps(event, indent=2))

    headers = {"Content-Type": "application/json"}

    try:
        global _S3_RESOURCE_TEMPLATES
        # TODO: pass full arn of bucket and validate
        _S3_RESOURCE_TEMPLATES["bucket_name"] = event["queryStringParameters"][
            "templateBucket"
        ]
        s3resource_templates = S3ResourceTemplates(_S3_RESOURCE_TEMPLATES)

        global _S3_RESOURCE_GENERATED_DOCUMENTS
        _S3_RESOURCE_GENERATED_DOCUMENTS["bucket_name"] = event[
            "queryStringParameters"
        ]["outputBucket"]
        s3resource_generated_documents = S3ResoureGeneratedDocuments(
            _S3_RESOURCE_GENERATED_DOCUMENTS
        )

        # TODO: only accept post
        if event["httpMethod"] == "POST":
            validate(event=event, schema=INPUT_SCHEMA)

            download_path = Path(f"/tmp/template-{uuid.uuid4()}.docx")
            template_key = event["queryStringParameters"]["template"]
            download_template(
                s3resource_templates, key=template_key, filename=download_path
            )

            upload_path = Path(f"/tmp/generated-{uuid.uuid4()}.docx")
            content = json.loads(event["body"])
            generate_document(
                documentpath=upload_path, templatepath=download_path, content=content
            )
            generated_document_key = event["queryStringParameters"]["documentKey"]
            upload_generated_document(
                s3resource_generated_documents,
                key=generated_document_key,
                filename=upload_path,
            )

            bucket = s3resource_generated_documents.bucket_name
            key = generated_document_key
            headers["Location"] = f"https://{bucket}.s3.{REGION}.amazonaws.com/{key}"
            status_code = 201
            body = "OK"

        else:
            # TODO: move to func that returns just available resources
            keys = [obj.key for obj in s3resource_templates.bucket.objects.all()]
            status_code = 200
            body = keys

    except DownloadFailError as e:
        logger.error(e)
        body = str(e)
        status_code = 404

    except SchemaValidationError as e:
        logger.error(e)
        body = str(e)
        status_code = 400

    except (UploadFailError, TemplateRenderError) as e:
        logger.error(e)
        body = str(e)
        status_code = 500

    except Exception as e:
        logger.error(e)
        body = "Unhandled Server Error: " + str(e)
        status_code = 500

    finally:
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body),
        }
