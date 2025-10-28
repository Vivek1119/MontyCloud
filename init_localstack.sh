#!/bin/bash
set -e

echo "Initializing LocalStack resources..."

until awslocal s3 ls >/dev/null 2>&1; do
  echo "Waiting for LocalStack to start..."
  sleep 3
done

BUCKET_NAME="my-instagram-images"
if ! awslocal s3 ls "s3://$BUCKET_NAME" >/dev/null 2>&1; then
  echo "Creating S3 bucket: $BUCKET_NAME"
  awslocal s3 mb "s3://$BUCKET_NAME"
else
  echo "S3 bucket already exists: $BUCKET_NAME"
fi

TABLE_NAME="image_metadata"
EXISTING_TABLE=$(awslocal dynamodb list-tables --query "TableNames[]" --output text)

if [[ "$EXISTING_TABLE" != *"$TABLE_NAME"* ]]; then
  echo "Creating DynamoDB table: $TABLE_NAME"
  awslocal dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --attribute-definitions AttributeName=image_id,AttributeType=S \
    --key-schema AttributeName=image_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
else
  echo "DynamoDB table already exists: $TABLE_NAME"
fi

echo "LocalStack initialization complete!"
