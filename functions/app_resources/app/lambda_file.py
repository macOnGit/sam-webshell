import logging
import json
from os import environ
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError
from boto3 import resource
from .schemas import INPUT_SCHEMA


logger = logging.getLogger()
logger.setLevel("INFO")


# TODO: dupe from documents - layers?
class S3Resource:
    """AWS S3 Resource"""

    def __init__(self, lambda_s3_resource: dict):
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


# TODO: dupe from documents - layers?
class S3ResoureOutput(S3Resource):
    # separate classes for patching
    pass


# TODO: dupe from documents - layers?
class S3ResourceTemplates(S3Resource):
    # separate classes for patching
    pass


class MissingEnvError(Exception):
    pass


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):
    logger.info("###EVENT RECIEVED")
    logger.info(json.dumps(event, indent=2))

    headers = {"Content-Type": "application/json"}

    try:
        validate(event=event, schema=INPUT_SCHEMA)

        template_bucket = environ.get("TEMPLATES_BUCKET")
        if not template_bucket:
            raise MissingEnvError("Missing env TEMPLATES_BUCKET")
        output_bucket = environ.get("OUTPUT_BUCKET")
        if not output_bucket:
            raise MissingEnvError("Missing env OUTPUT_BUCKET")

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

        templates = [obj.key for obj in s3resource_templates.bucket.objects.all()]
        documents = [obj.key for obj in s3resource_output.bucket.objects.all()]
        body = {
            "template_buckets": [
                {"bucket_name": template_bucket, "templates": templates}
            ],
            "output_buckets": [{"bucket_name": output_bucket, "documents": documents}],
        }
        status_code = 200

    except SchemaValidationError as e:
        body = str(e)
        status_code = 400

    except MissingEnvError as e:
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
