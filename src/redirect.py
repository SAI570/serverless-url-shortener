import json, os, time
import boto3
from botocore.exceptions import ClientError

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def handler(event, context):
    code = (event.get("pathParameters") or {}).get("code", "")
    if not code.isalnum() or len(code) > 16:
        return {"statusCode": 400, "body": "Bad code"}

    try:
        # One atomic call: increment clicks and fetch the URL. Fails if code is unknown.
        r = table.update_item(
            Key={"code": code},
            UpdateExpression="ADD clicks :one SET last_click = :now",
            ConditionExpression="attribute_exists(code)",
            ExpressionAttributeValues={":one": 1, ":now": int(time.time())},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 404, "body": "Link not found"}
        raise

    headers = event.get("headers") or {}
    print(json.dumps({
        "event": "click",
        "code": code,
        "referer": headers.get("Referer", "-"),
        "ua": headers.get("User-Agent", "-")[:150],
        "ip": event["requestContext"]["identity"].get("sourceIp"),
    }))
    return {"statusCode": 302, "headers": {"Location": r["Attributes"]["url"], "Cache-Control": "no-store"}, "body": ""}
