import json
import pytest

from hello_world import app


@pytest.mark.parametrize("event", ["apigw_event"], indirect=True)
def test_lambda_handler(event):

    ret = app.lambda_handler(event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert "message" in ret["body"]
    assert data["message"] == "hello world"
