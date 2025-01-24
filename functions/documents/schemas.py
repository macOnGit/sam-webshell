INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/documents.schema.json",
    "title": "Document Content",
    "description": "Content for a document",
    "type": "object",
    "required": ["queryStringParameters"],
    "properties": {
        "queryStringParameters": {
            "description": "The template to base the document on",
            "type": "object",
            "required": ["template"],
            "properties": {
                "template": {
                    "$id": "#/properties/queryStringParameters/template",
                    "type": "string",
                }
            },
        }
    },
}
