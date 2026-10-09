import json, os, re, secrets, string, time
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
ALPHABET = string.ascii_letters + string.digits
MAX_URL_LEN = 2048

# Security: simple blocklist. Extend or load from S3/DynamoDB in production.
BLOCKED_DOMAINS = {"malware.testing.google.test", "evil.example", "phishing.example"}
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}


def resp(status, body):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(body)}


def validate(url):
    if len(url) > MAX_URL_LEN:
        return "URL too long"
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return "Only valid http/https URLs are allowed"
    host = p.hostname.lower()
    if host in ("localhost",) or IP_RE.match(host):
        return "Raw IPs and localhost are not allowed"
    if any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS):
        return "Domain is blocklisted"
    return None


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return resp(400, {"error": "Invalid JSON"})

    url = (body.get("url") or "").strip()
    error = validate(url)
    if error:
        print(json.dumps({"event": "rejected", "reason": error, "url": url[:200]}))
        return resp(400, {"error": error})

    for _ in range(5):  # retry on the rare code collision
        code = "".join(secrets.choice(ALPHABET) for _ in range(7))
        try:
            table.put_item(
                Item={"code": code, "url": url, "clicks": 0, "created_at": int(time.time())},
                ConditionExpression="attribute_not_exists(code)",
            )
            break
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
    else:
        return resp(500, {"error": "Could not generate code"})

    rc = event["requestContext"]
    short_url = f"https://{rc['domainName']}/{rc['stage']}/{code}"
    print(json.dumps({"event": "created", "code": code}))
    return resp(201, {"code": code, "short_url": short_url})
