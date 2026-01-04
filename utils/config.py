import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):

    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL")
    AWS_REGION: str = os.getenv("AWS_REGION")
    S3_BUCKET: str = os.getenv("S3_BUCKET")
    DYNAMO_TABLE: str = os.getenv("DYNAMO_TABLE")

    LOCALSTACK_AUTH_TOKEN: str = os.getenv('LOCALSTACK_AUTH_TOKEN')
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")
    LOG_DIR: str = os.getenv("LOG_DIR")



    class Config:
        env_file = "../.env"

settings = Settings()