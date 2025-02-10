INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/documents.schema.json",
    "title": "Document Content",
    "description": "Content for a document",
    "type": "object",
    "required": ["queryStringParameters", "pathParameters", "body"],
    "properties": {
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
                },
                "outputBucket": {
                    "$id": "#/properties/queryStringParameters/outputBucket",
                    "type": "string",
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
