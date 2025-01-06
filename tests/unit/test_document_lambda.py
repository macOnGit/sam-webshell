import os
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch
from boto3 import resource, client
from moto import mock_aws

# TODO: drop "Generated" in name
from documents.app import (
    S3ResourceTemplates,
    S3ResoureGeneratedDocuments,
    lambda_handler,
)


@mock_aws
class TestDocumentLambda(TestCase):
    def setUp(self) -> None:
        """Create mocked resources for use during tests"""

        # Mock environment & override resources
        # self.test_ddb_table_name = "test_ddb"
        self.test_s3_template_bucket_name = "test_s3_template_bucket"
        self.test_s3_generated_document_bucket_name = (
            "test_s3_generated_document_bucket"
        )
        # TODO: these have effect, why are they being used?
        # os.environ["TEMPLATE_DATA_TABLE_NAME"] = self.test_ddb_table_name
        # os.environ["TEMPLATE_BUCKET_NAME"] = self.test_s3_template_bucket_name
        # os.environ["GENERATED_DOCUMENTS_BUCKET_NAME"] = (
        #     self.test_s3_generated_document_bucket_name
        # )
        # os.environ["AWS_REGION"] = "us-east-1"

        # Set up the services: construct a (mocked!) DynamoDB table
        # dynamodb = resource("dynamodb", region_name="us-east-1")
        # dynamodb.create_table(
        #     TableName=self.test_ddb_table_name,
        #     KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
        #     AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        #     BillingMode="PAY_PER_REQUEST",
        # )

        # Set up the services: construct (mocked!) S3 Buckets
        s3_client = client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=self.test_s3_template_bucket_name)
        s3_client.create_bucket(Bucket=self.test_s3_generated_document_bucket_name)

        # Establish the "GLOBAL" environment for use in tests.
        # mock_dynamodb_template_data_resource = {
        #     "resource": resource("dynamodb"),
        #     "table_name": self.test_ddb_table_name,
        # }
        mock_s3_template_resource = {
            "resource": resource("s3"),
            "bucket_name": self.test_s3_template_bucket_name,
        }
        mock_s3_generated_documents_resource = {
            "resource": resource("s3"),
            "bucket_name": self.test_s3_generated_document_bucket_name,
        }
        # self.mock_dynamodb_template_data = DynamoDBResource(
        #     mock_dynamodb_template_data_resource
        # )
        self.mock_s3_templates = S3ResourceTemplates(mock_s3_template_resource)
        self.mock_s3_generated_documents = S3ResoureGeneratedDocuments(
            mock_s3_generated_documents_resource
        )

    def upload_template_to_s3(self):
        # Add template to (mocked!) S3 bucket
        # TODO: temp code, remove when switched to pytest fixtures
        docx_file = Path(__file__).parents[2] / "fixtures" / "blank_template_doc.docx"
        self.mock_s3_templates.bucket.upload_file(
            docx_file, "documents/blank_template_doc.docx"
        )

    def load_sample_event_from_file(self) -> dict:
        # TODO: temp code, remove when switched to pytest fixtures
        json_file = Path(__file__).parents[2] / "events" / "blank_template_doc.json"
        with json_file.open() as fp:
            event = json.load(fp)
            return event

    # @patch("document.DynamoDBResource")
    @patch("documents.app.S3ResoureGeneratedDocuments")
    @patch("documents.app.S3ResourceTemplates")
    @patch("documents.app.REGION", "us-east-1")
    def test_lambda_handler_valid_event_returns_200(
        self,
        # patch_region: MagicMock,
        patch_s3_template_resource: MagicMock,
        patch_s3_document_resource: MagicMock,
        # patch_dynamodb_resource: MagicMock,
    ):
        # patch_dynamodb_resource.return_value = self.mock_dynamodb_template_data
        # patch_region.return_value = self.region
        patch_s3_template_resource.return_value = self.mock_s3_templates
        patch_s3_document_resource.return_value = self.mock_s3_generated_documents

        test_event = self.load_sample_event_from_file()
        self.upload_template_to_s3()
        response = lambda_handler(event=test_event, context=None)

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(
            response["headers"]["Location"],
            f"https://{self.test_s3_generated_document_bucket_name}.s3.us-east-1.amazonaws.com/documents/test.docx",
        )

    def tearDown(self) -> None:

        # [13] Remove (mocked!) S3 Objects and Bucket
        s3_resource = resource("s3", region_name="us-east-1")
        s3_bucket = s3_resource.Bucket(self.test_s3_template_bucket_name)
        for key in s3_bucket.objects.all():
            key.delete()
        s3_bucket.delete()

        # [14] Remove (mocked!) DynamoDB Table
        # dynamodb_resource = client("dynamodb", region_name="us-east-1")
        # dynamodb_resource.delete_table(TableName=self.test_ddb_table_name)
