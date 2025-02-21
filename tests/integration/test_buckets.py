import pytest


def test_template_bucket_exists(s3_client, stack_name):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/head_bucket.html
    response = s3_client.head_bucket(Bucket=f"{stack_name}-templates")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


@pytest.mark.parametrize(
    "template_bucket_with_templates",
    [("blank_template_doc", "general_amdt_doc")],
    indirect=True,
)
def test_upload_to_template_bucket(template_bucket, template_bucket_with_templates):
    num_objects = len([item for item in template_bucket.objects.all()])

    assert num_objects == 2, "Could not upload all files to S3 bucket"
