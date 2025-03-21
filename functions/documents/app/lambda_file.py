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
from .schemas import INPUT_SCHEMA

REGION = environ.get("AWS_REGION")
logger = logging.getLogger()
logger.setLevel("INFO")


class S3Resource:
    """AWS S3 Resource"""

    def __init__(self, lambda_s3_resource: dict):
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


class S3ResoureOutput(S3Resource):
    # separate classes for patching
    pass


class S3ResourceTemplates(S3Resource):
    # separate classes for patching
    pass


class DownloadFailTemplateError(Exception):
    pass


class DownloadFailBucketError(Exception):
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
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            raise DownloadFailTemplateError(
                f"Failed to get template: {key} from {s3resource.bucket_name}. "
                "Please verify template name and its existance."
            )
        elif (error_code == "NoSuchBucket") or (error_code == "403"):
            raise DownloadFailBucketError(
                f"Failed to get template: {key} from {s3resource.bucket_name}. "
                "Please verify bucket name and your access to it."
            )
        else:
            raise e


def upload_generated_document(
    s3resource: S3Resource, *, key: str, filename: str
) -> bool:
    # key - name of key in target bucket
    # filename - path of file to upload
    try:
        s3resource.bucket.upload_file(filename, key)
        logger.info(f"{key} created in {s3resource.bucket_name} bucket")
    except (ClientError, S3UploadFailedError) as e:
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
        validate(event=event, schema=INPUT_SCHEMA)

        template_bucket = event["queryStringParameters"]["templateBucket"].split(":::")[
            1
        ]
        output_bucket = event["queryStringParameters"]["outputBucket"].split(":::")[1]
        s3resource_templates = S3ResourceTemplates(
            {
                "resource": resource("s3"),
                "bucket_name": template_bucket,
            }
        )
        s3resource_output = S3ResoureOutput(
            {
                "resource": resource("s3"),
                "bucket_name": output_bucket,
            }
        )
        download_path = Path(f"/tmp/template-{uuid.uuid4()}.docx")
        template_key = event["path"][1:]
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
            s3resource_output,
            key=generated_document_key,
            filename=upload_path,
        )

        bucket = s3resource_output.bucket_name
        key = generated_document_key
        headers["Location"] = f"https://{bucket}.s3.{REGION}.amazonaws.com/{key}"
        status_code = 201
        body = "OK"

    except DownloadFailTemplateError as e:
        logger.error(e)
        body = str(e)
        status_code = 404

    except DownloadFailBucketError as e:
        logger.error(e)
        body = str(e)
        status_code = 403

    except SchemaValidationError as e:
        body = str(e)
        status_code = 400

    except (UploadFailError, TemplateRenderError) as e:
        logger.error(e)
        body = str(e)
        status_code = 500

    except Exception as e:
        logger.error(e, exc_info=True)
        body = "Unhandled Server Error: " + str(e)
        status_code = 500

    finally:
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body),
        }
