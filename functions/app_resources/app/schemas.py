INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/documents.schema.json",
    "title": "Resource Request Content",
    "description": "Content for a document",
    "type": "object",
    "required": ["httpMethod"],
    "properties": {
        "httpMethod": {
            "description": "Endpoint only accepts GET method",
            "type": "string",
            "pattern": "GET",
        },
    },
}
