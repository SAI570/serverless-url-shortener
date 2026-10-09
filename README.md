# Serverless URL Shortener with Analytics (AWS)

Stack: S3 + CloudFront, API Gateway, Lambda (Python 3.12), DynamoDB, CloudWatch, IAM, optional WAF. Defined in AWS SAM.

## Prerequisites
- AWS account, AWS CLI configured (`aws configure`)
- AWS SAM CLI installed

## Deploy
```bash
sam build
sam deploy --guided          # stack name: url-shortener, accept defaults
# EnableWAF=false keeps you in free tier. Set true to add rate limiting.
```

Take the outputs (ApiUrl, SiteUrl, BucketName), then upload the frontend:
```bash
API_URL=<ApiUrl output>
BUCKET=<BucketName output>
sed "s|REPLACE_ME|$API_URL|" frontend/index.html > /tmp/index.html
aws s3 cp /tmp/index.html s3://$BUCKET/index.html --content-type text/html
```
Open the SiteUrl output in a browser.

## Test from CLI
```bash
curl -X POST $API_URL/links -d '{"url":"https://aws.amazon.com"}'
curl -i $API_URL/<code>        # 302 redirect
curl $API_URL/stats/<code>     # click count
```

## Security features
- Least-privilege IAM: each Lambda has only the one DynamoDB action it needs
- URL validation (http/https only, blocks IPs/localhost, domain blocklist)
- API Gateway throttling, optional WAF rate limit per IP
- DynamoDB encryption + point-in-time recovery; S3 fully private (CloudFront OAC)
- XSS-safe frontend (escaped output); structured click logs in CloudWatch
- CloudWatch alarm on Lambda errors

## Extend (for extra marks)
- Cognito auth on POST /links
- Enable CloudTrail + GuardDuty
- Custom domain with Route 53 + ACM
- Click dashboard with CloudWatch Logs Insights

## Cleanup
```bash
aws s3 rm s3://$BUCKET --recursive
sam delete
```
