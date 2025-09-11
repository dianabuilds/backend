from __future__ import annotations

# JSON Schemas (Draft-07) for validation

ProviderManifest: dict = {
    "$id": "ProviderManifest",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["provider", "auth", "endpoints", "models"],
    "properties": {
        "provider": {"type": "string", "description": "provider code"},
        "display_name": {"type": "string"},
        "auth": {
            "type": "object",
            "required": ["type", "fields"],
            "properties": {
                "type": {"type": "string", "enum": ["api_key", "bearer", "basic", "none"]},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["key", "label"],
                        "properties": {
                            "key": {"type": "string"},
                            "label": {"type": "string"},
                            "secret": {"type": "boolean", "default": True},
                        },
                    },
                },
            },
        },
        "endpoints": {
            "type": "object",
            "properties": {
                "chat": {"$ref": "#/definitions/Endpoint"},
                "embed": {"$ref": "#/definitions/Endpoint"},
                "rerank": {"$ref": "#/definitions/Endpoint"},
                "image": {"$ref": "#/definitions/Endpoint"},
            },
            "additionalProperties": {"$ref": "#/definitions/Endpoint"},
        },
        "models": {
            "type": "array",
            "items": {"$ref": "#/definitions/ModelDescriptor"},
            "minItems": 1,
        },
        "safety": {"type": "array", "items": {"type": "string"}},
        "rate_limits": {"$ref": "#/definitions/RateLimits"},
    },
    "definitions": {
        "Endpoint": {
            "type": "object",
            "required": ["path", "method"],
            "properties": {
                "path": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "headers": {"type": "object", "additionalProperties": {"type": "string"}},
            },
        },
        "RateLimits": {
            "type": "object",
            "properties": {
                "rpm": {"type": "integer", "minimum": 0},
                "rps": {"type": "integer", "minimum": 0},
                "tpm": {"type": "integer", "minimum": 0},
            },
        },
        "ModelDescriptor": {
            "type": "object",
            "required": ["id", "family", "capabilities"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "family": {"type": "string"},
                "provider_model_code": {"type": "string"},
                "capabilities": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "chat",
                            "tools",
                            "json_mode",
                            "vision",
                            "long_context",
                            "stream",
                            "embed",
                            "rerank",
                        ],
                    },
                },
                "inputs": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["int", "float", "string", "bool", "enum"],
                            },
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "step": {"type": "number"},
                            "default": {},
                            "enum": {"type": "array", "items": {}},
                        },
                    },
                },
                "limits": {
                    "type": "object",
                    "properties": {
                        "max_input_tokens": {"type": "integer"},
                        "max_output_tokens": {"type": "integer"},
                    },
                },
                "pricing": {
                    "type": "object",
                    "properties": {
                        "input_per_1k": {"type": "number"},
                        "output_per_1k": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"},
                    },
                },
            },
        },
    },
}

RoutingProfile: dict = {
    "$id": "RoutingProfile",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "rules"],
    "properties": {
        "name": {"type": "string"},
        "enabled": {"type": "boolean", "default": True},
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["task", "selector"],
                "properties": {
                    "task": {"type": "string", "enum": ["chat", "embed", "rerank", "image"]},
                    "selector": {
                        "type": "object",
                        "properties": {
                            "capabilities": {"type": "array", "items": {"type": "string"}},
                            "min_context": {"type": "integer"},
                            "max_price_per_1k": {"type": "number"},
                            "plan": {"type": "string", "enum": ["Free", "Premium", "Premium+"]},
                        },
                    },
                    "route": {
                        "type": "object",
                        "required": ["provider_id", "model_id"],
                        "properties": {
                            "provider_id": {"type": "string"},
                            "model_id": {"type": "string"},
                            "params": {"type": "object", "additionalProperties": {}},
                            "fallback": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["provider_id", "model_id"],
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}

Preset: dict = {
    "$id": "Preset",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "task", "params"],
    "properties": {
        "name": {"type": "string"},
        "task": {"type": "string", "enum": ["chat", "embed", "rerank"]},
        "description": {"type": "string"},
        "params": {"type": "object", "additionalProperties": {}},
    },
}

ProviderSecrets: dict = {
    "$id": "ProviderSecrets",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    # Accept both upper- and lower-case keys like API_KEY, api_key, Token
    "patternProperties": {"^[A-Za-z0-9_]+$": {"type": "string"}},
    "additionalProperties": False,
}

__all__ = ["ProviderManifest", "RoutingProfile", "Preset", "ProviderSecrets"]
