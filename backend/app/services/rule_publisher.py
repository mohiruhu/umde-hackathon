import os
import json
import logging
from typing import List, Any, Dict
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_s3 import S3Client

from backend.app.rules.base import ValidationRule
from backend.app.rule_registry import discover_rules

logger = logging.getLogger(__name__)


def get_s3_client() -> S3Client:
    return boto3.client("s3")  # type: ignore


def get_output_path(filename: str) -> str:
    local_folder = os.getenv("LOCAL_RULE_OUTPUT_PATH", "output/rules")
    os.makedirs(local_folder, exist_ok=True)
    return os.path.join(local_folder, filename)


def serialize_rules(rules: List[ValidationRule]) -> str:
    result: List[Dict[str, Any]] = []
    for rule in rules:
        try:
            result.append({
                "id": rule.rule_id,
                "name": rule.name,
                "layer": rule.layer,
                "description": getattr(rule, "description", ""),  # Avoid AttributeError
            })
        except Exception as e:
            logger.warning(f"Failed to serialize rule {rule.rule_id}: {e}")
    return json.dumps(result, indent=2)


def publish_rules_to_s3(bucket: str, key: str, content: str) -> None:
    s3 = get_s3_client()
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))
        logger.info(f"Published rule metadata to S3: s3://{bucket}/{key}")
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to publish to S3: {e}")
        raise


def publish_rules_to_local(filepath: str, content: str) -> None:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Published rule metadata locally at: {filepath}")
    except OSError as e:
        logger.error(f"Failed to write local file: {e}")
        raise


def publish_rule_metadata() -> None:
    rules = discover_rules()
    serialized = serialize_rules(rules)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    filename = f"rules_{timestamp}.json"

    if os.getenv("USE_AWS", "false").lower() == "true":
        bucket = os.getenv("RULE_BUCKET_NAME")
        prefix = os.getenv("RULE_BUCKET_KEY_PREFIX", "rules/")
        key = f"{prefix.rstrip('/')}/rules_{timestamp}.json"
        if not bucket:
            raise ValueError("RULE_BUCKET_NAME not set in environment.")
        publish_rules_to_s3(bucket, key, serialized)
    else:
        output_path = get_output_path(filename)
        publish_rules_to_local(output_path, serialized)
