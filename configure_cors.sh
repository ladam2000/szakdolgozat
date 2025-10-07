#!/bin/bash
# Configure CORS on Lambda Function URL

echo "Configuring CORS on Lambda Function URL..."

aws lambda update-function-url-config \
  --function-name travel-assistant-proxy \
  --cors '{
    "AllowOrigins": ["*"],
    "AllowMethods": ["POST", "OPTIONS"],
    "ExposeHeaders": ["Content-Type"],
    "MaxAge": 86400,
    "AllowCredentials": false
  }'

echo ""
echo "Verifying CORS configuration..."
aws lambda get-function-url-config \
  --function-name travel-assistant-proxy

echo ""
echo "✅ CORS configured!"
echo ""
echo "Test from browser now."
