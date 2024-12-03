import json
from boto3 import resource
from os import environ

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

_LAMBDA_S3_RESOURCE = {
    "resource": resource("s3"),
    # TODO: don't hardcode bucket name
    # "bucket_name": environ.get("TEMPLATE_BUCKET_NAME", "NONE"),
    "bucket_name": "sam-webshell-templates",
}


class LambdaS3Class:
    """
    AWS S3 Resource Class
    """

    def __init__(self, lambda_s3_resource):
        """
        Initialize an S3 Resource
        """
        self.resource = lambda_s3_resource["resource"]
        self.bucket_name = lambda_s3_resource["bucket_name"]
        self.bucket = self.resource.Bucket(self.bucket_name)


def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):

    global _LAMBDA_S3_RESOURCE

    s3_resource_class = LambdaS3Class(_LAMBDA_S3_RESOURCE)

    keys = [obj.key for obj in s3_resource_class.bucket.objects.all()]

    return {
        "statusCode": 200,
        "body": json.dumps(keys),
    }
