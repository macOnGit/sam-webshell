def test_template_bucket_exists(s3_client):
    # TODO: don't hardcode name
    response = s3_client.head_bucket(Bucket="sam-webshell-templates")
    assert response["status_code"] == 200
