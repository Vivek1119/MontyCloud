import boto3
from botocore.exceptions import ClientError

from utils.common import generate_uuid
from utils.config import settings




class AWSService:
    """
    A service class for managing AWS S3 and DynamoDB operations.
    """

    def __init__(self):

        self.region = settings.AWS_REGION
        self.s3_bucket = settings.S3_BUCKET
        self.dynamo_table = settings.DYNAMO_TABLE

        self.s3_client = boto3.client("s3",
                                      region_name=self.region,
                                      endpoint_url=settings.AWS_ENDPOINT_URL,
                                      aws_access_key_id="test",
                                      aws_secret_access_key="test",
                                      )
        self.dynamo_resource = boto3.resource("dynamodb",
                                              region_name=self.region,
                                              endpoint_url = settings.AWS_ENDPOINT_URL,
                                              aws_access_key_id = "test",
                                              aws_secret_access_key = "test"
                                              )
        self.table = self.dynamo_resource.Table(self.dynamo_table)


    def generate_image_key(self, user_id: str, filename: str):

        ext = filename.split(".")[-1]
        image_id = generate_uuid()
        key = f"uploads/{user_id}/{image_id}.{ext}"
        return key, image_id


    def get_image_url(self, key: str) -> str:
        if settings.AWS_ENDPOINT_URL:
            return f"{settings.AWS_ENDPOINT_URL}/{self.s3_bucket}/{key}"
        return f"https://{self.s3_bucket}.s3.{self.region}.amazonaws.com/{key}"


    def upload_image_to_s3(self, file_obj, key: str, content_type: str):

        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.s3_bucket,
                key,
                ExtraArgs={"ContentType": content_type}
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to upload image to S3: {e}")


    def save_image_metadata(self, metadata: dict):

        try:
            self.table.put_item(Item=metadata)
        except ClientError as e:
            raise RuntimeError(f"Failed to save metadata to DynamoDB: {e}")


    def query_images(self, filters: dict) -> list:

        #table = self.dynamo_table.Table(self.table)

        try:
            scan_kwargs = {}

            from boto3.dynamodb.conditions import Attr

            filter_expression = None
            if "user_id" in filters:
                filter_expression = Attr("user_id").eq(filters["user_id"])

            if "tag" in filters:
                tag_filter = Attr("tags").contains(filters["tag"])
                filter_expression = (
                    tag_filter if filter_expression is None else filter_expression & tag_filter
                )

            if filter_expression:
                scan_kwargs["FilterExpression"] = filter_expression

            response = self.table.scan(**scan_kwargs)
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response:
                response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"], **scan_kwargs)
                items.extend(response.get("Items", []))

            return items

        except Exception as e:
            raise Exception(f"Error querying DynamoDB: {str(e)}")



    def get_image_metadata(self, image_id: str) -> dict:

        try:
            response = self.table.get_item(Key={"image_id": image_id})
            return response.get("Item")
        except Exception as e:
            raise Exception(f"Error fetching image metadata: {str(e)}")


    def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:

        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.s3_bucket, "Key": s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def delete_image_from_s3(self, s3_key: str):

        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
        except Exception as e:
            raise Exception(f"Failed to delete image from S3: {str(e)}")

    def delete_metadata_from_dynamo(self, image_id: str):

        try:
            self.table.delete_item(Key={"image_id": image_id})
        except Exception as e:
            raise Exception(f"Failed to delete metadata from DynamoDB: {str(e)}")