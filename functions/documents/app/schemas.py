INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/documents.schema.json",
    "title": "Document Content",
    "description": "Content for a document",
    "type": "object",
    "required": ["httpMethod", "pathParameters", "queryStringParameters", "body"],
    "properties": {
        "httpMethod": {
            "description": "Endpoint only accepts POST method",
            "type": "string",
            "pattern": "POST",
        },
        "pathParameters": {
            "type": "object",
            "required": ["template"],
            "properties": {
                "template": {
                    "$id": "#/properties/pathParameters/template",
                    "type": "string",
                },
            },
        },
        "queryStringParameters": {
            "type": "object",
            "required": ["documentKey", "templateBucket", "outputBucket"],
            "properties": {
                "documentKey": {
                    "$id": "#/properties/queryStringParameters/documentKey",
                    "type": "string",
                },
                "templateBucket": {
                    "$id": "#/properties/queryStringParameters/templateBucket",
                    "type": "string",
                    "pattern": "(?<=arn:aws:s3:::)[ a-zA-Z0-9!_.*'()-]+",
                },
                "outputBucket": {
                    "$id": "#/properties/queryStringParameters/outputBucket",
                    "type": "string",
                    "pattern": "(?<=arn:aws:s3:::)[ a-zA-Z0-9!_.*'()-]+",
                },
            },
        },
        "body": {
            "description": "Content for the template to render",
            "type": "string",
            "contentMediaType": "application/json",
        },
    },
}
