def test_template_bucket_exists(s3_client):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/head_bucket.html
    # TODO: don't hardcode name
    response = s3_client.head_bucket(Bucket="sam-webshell-templates")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
