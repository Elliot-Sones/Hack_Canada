"""S3/MinIO storage wrapper for file uploads."""

import boto3
from botocore.exceptions import ClientError

from app.config import settings


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


def ensure_bucket_exists() -> None:
    client = _get_s3_client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.S3_BUCKET_NAME)


def upload_file(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def download_file(key: str) -> bytes:
    client = _get_s3_client()
    response = client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    return response["Body"].read()


def generate_presigned_url(key: str, expires: int = 3600) -> str:
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expires,
    )


def delete_file(key: str) -> None:
    client = _get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
