""" Writes the front end's types (frontend/src/api-types.ts) from the API's OpenAPI schema, so both sides share one definition of every
    request and response (api/schemas.py).

    uv run python -m api.openapi           (tests/test_api.py fails when the file is out of date) """
from pathlib import Path

from api.main import app

PATH = Path(__file__).parent.parent / "frontend" / "src" / "api-types.ts"
HEADER = "// Generated from the API's schema by `uv run python -m api.openapi`. Don't edit: change api/schemas.py and run it again\n"

def ts_type(schema):
    """ A JSON schema as a TypeScript type """
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    for key in ("anyOf", "oneOf"):
        if key in schema:
            return " | ".join(dict.fromkeys(ts_type(s) for s in schema[key]))
    if "const" in schema:
        return repr(schema["const"]) if isinstance(schema["const"], str) else str(schema["const"]).lower()
    if "enum" in schema:
        return " | ".join(repr(v) for v in schema["enum"])
    kind = schema.get("type")
    if kind == "array":
        if "prefixItems" in schema:
            return "[" + ", ".join(ts_type(s) for s in schema["prefixItems"]) + "]"
        inner = ts_type(schema.get("items", {}))
        return f"({inner})[]" if " | " in inner else f"{inner}[]"
    if kind == "object":
        if "properties" in schema:
            return "{ " + "; ".join(_property(name, s, schema.get("required", [])) for name, s in schema["properties"].items()) + " }"
        extra = schema.get("additionalProperties")
        return f"Record<string, {ts_type(extra) if isinstance(extra, dict) else 'unknown'}>"
    return {"string": "string", "integer": "number", "number": "number", "boolean": "boolean", "null": "null"}.get(kind, "unknown")

def _property(name, schema, required):
    key = name if name.isidentifier() else repr(name)
    # A field with a default is always present in a response, and may be left out of a request
    optional = name not in required and "default" not in schema
    return f"{key}{'?' if optional else ''}: {ts_type(schema)}"

def types_text():
    schemas = app.openapi()["components"]["schemas"]
    lines = [HEADER]
    for name in sorted(schemas):
        schema = schemas[name]
        if name in ("HTTPValidationError", "ValidationError"):
            continue
        description = " ".join((schema.get("description") or "").split())
        if description:
            lines.append(f"/** {description} */")
        if schema.get("type") == "object" and "properties" in schema:
            lines.append(f"export interface {name} {{")
            lines += [f"  {_property(prop, s, schema.get('required', []))}" for prop, s in schema["properties"].items()]
            lines.append("}\n")
        else:
            lines.append(f"export type {name} = {ts_type(schema)}\n")
    return "\n".join(lines)

if __name__ == "__main__":
    PATH.write_text(types_text(), encoding="utf-8")
    print(f"Wrote {PATH}")
