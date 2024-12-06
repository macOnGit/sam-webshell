import pytest


def test_template_bucket_exists(s3_client):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/head_bucket.html
    response = s3_client.head_bucket(Bucket="webshell-dev-templates")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


@pytest.mark.usefixtures("template_bucket_with_templates")
def test_upload_to_template_bucket(template_bucket):
    num_objects = len([item for item in template_bucket.objects.all()])

    assert num_objects == 2, "Could not upload all files to S3 bucket"
