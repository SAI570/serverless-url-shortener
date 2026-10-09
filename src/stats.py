import json, os
import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}


def handler(event, context):
    code = (event.get("pathParameters") or {}).get("code", "")
    item = table.get_item(Key={"code": code}).get("Item") if code.isalnum() else None
    if not item:
        return {"statusCode": 404, "headers": HEADERS, "body": json.dumps({"error": "Not found"})}
    out = {k: int(v) if k in ("clicks", "created_at", "last_click") else v for k, v in item.items()}
    return {"statusCode": 200, "headers": HEADERS, "body": json.dumps(out)}
