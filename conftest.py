pytest_plugins = ["tests.unit.mock_fixtures", "tests.integration.real_fixtures"]

from pathlib import Path
from dataclasses import dataclass
import pytest

# TODO: create/validate schemes
# from aws_lambda_powertools.utilities.validation import validate
# from src.sample_lambda.schemas import (
#     INPUT_SCHEMA,
# )  # pylint: disable=wrong-import-position
# TODO: use scheme validator
# from aws_lambda_powertools.utilities.validation import validator

base_path = Path(__file__).parent


@dataclass
class Filenames:
    template_bucket_name: str
    generated_documents_bucket_name: str


@pytest.fixture
def filenames():
    return Filenames(
        template_bucket_name="test_s3_template_bucket",
        generated_documents_bucket_name="test_s3_generated_document_bucket",
    )
