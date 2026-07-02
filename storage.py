import logging
import json 
from datetime import datetime, timezone
from config import USE_S3, AWS_CONFIG

logger = logging.getLogger(__name__)

def save_raw(data: dict, source_name: str, local_path: str) -> None:
    if USE_S3:
        _save_to_s3(data, source_name)
    else:
        _save_to_local(data, local_path)

def _save_to_local(data: dict, filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent = 2)
    logger.info(f"Saved raw data locally to {filepath}")


def _save_to_s3(data: dict, source_name: str) -> None:
    import boto3
    from botocore.exceptions import ClientError

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    object_key = f"raw/{source_name}/{source_name}_{timestamp}.json"

    s3 = boto3.client("s3", region_name = AWS_CONFIG["region"])
    body = json.dumps(data, indent=2).encode("utf-8")

    try:
        s3.put_object(
            Bucket=AWS_CONFIG["bucket_name"],
            Key=object_key,
            Body = body,
            ContentType="application/json",
        )
        logger.info(f"Saved raw data to S3://{AWS_CONFIG['bucket_name']}/{object_key}")
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise