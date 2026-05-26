#!/usr/bin/env python3
"""Upload recipe images to Cloudflare R2 and write a CSV with uploaded URIs.

Required environment variables:
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET

Optional environment variables:
- R2_PUBLIC_BASE_URL (for example: https://cdn.example.com)
"""

from __future__ import annotations

import argparse
import csv
import mimetypes
import os
from pathlib import Path
from typing import Dict
from uuid import UUID, uuid4

import boto3
from botocore.client import BaseClient
from dotenv import load_dotenv

load_dotenv()


REQUIRED_ENV_VARS = (
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET",
)


def _load_required_env() -> Dict[str, str]:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {missing_str}")

    return {name: os.environ[name] for name in REQUIRED_ENV_VARS}


def _load_bucket_for_dry_run() -> str:
    bucket = os.getenv("R2_BUCKET")
    return bucket if bucket else "dry-run-bucket"


def _build_r2_client(account_id: str, access_key: str, secret_key: str) -> BaseClient:
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )


def _row_uuid(row: Dict[str, str]) -> str:
    raw_id = (row.get("id") or "").strip()
    if raw_id:
        try:
            return str(UUID(raw_id))
        except ValueError:
            pass
    return str(uuid4())


def _content_type(file_path: Path) -> str:
    guessed, _ = mimetypes.guess_type(file_path.as_posix())
    return guessed or "application/octet-stream"


def _build_uri(public_base_url: str | None, bucket: str, object_key: str) -> str:
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{object_key}"
    return f"r2://{bucket}/{object_key}"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        default="data/cleaned_recipes.csv",
        help="Input CSV path (default: data/cleaned_recipes.csv)",
    )
    parser.add_argument(
        "--output-csv",
        default="data/cleaned_recipes_with_r2_uri.csv",
        help="Output CSV path (default: data/cleaned_recipes_with_r2_uri.csv)",
    )
    parser.add_argument(
        "--images-dir",
        default="notebooks/data/images",
        help="Directory containing source image files (default: data/images)",
    )
    parser.add_argument(
        "--prefix",
        default="recipes/images",
        help="R2 object key prefix (default: recipes/images)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate mappings and generate output CSV without uploading",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    env = _load_required_env() if not args.dry_run else None
    bucket = env["R2_BUCKET"] if env is not None else _load_bucket_for_dry_run()
    public_base_url = os.getenv("R2_PUBLIC_BASE_URL")

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv)
    images_dir = Path(args.images_dir)
    prefix = args.prefix.strip("/")

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    client = None
    if not args.dry_run:
        if env is None:
            raise RuntimeError("R2 environment is not configured")
        client = _build_r2_client(
            account_id=env["R2_ACCOUNT_ID"],
            access_key=env["R2_ACCESS_KEY_ID"],
            secret_key=env["R2_SECRET_ACCESS_KEY"],
        )

    with input_csv.open("r", newline="", encoding="utf-8") as in_fp:
        reader = csv.DictReader(in_fp)
        if reader.fieldnames is None:
            raise RuntimeError("Input CSV has no header")

        output_fields = list(reader.fieldnames)
        if "image_uri" not in output_fields:
            output_fields.append("image_uri")
        if "uploaded_image_name" not in output_fields:
            output_fields.append("uploaded_image_name")

        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as out_fp:
            writer = csv.DictWriter(out_fp, fieldnames=output_fields)
            writer.writeheader()

            total = 0
            uploaded = 0
            skipped = 0

            for row in reader:
                total += 1

                original_path = (row.get("image_path") or "").strip()
                image_name = Path(original_path).name
                local_image_path = images_dir / image_name

                if not image_name or not local_image_path.exists():
                    row["image_uri"] = ""
                    row["uploaded_image_name"] = ""
                    writer.writerow(row)
                    skipped += 1
                    print(f"[{total}] skip: file missing for image_path='{original_path}'")
                    continue

                image_uuid = _row_uuid(row)
                object_name = f"{image_uuid}{local_image_path.suffix.lower() or '.jpg'}"
                object_key = f"{prefix}/{object_name}" if prefix else object_name

                if client is not None:
                    client.upload_file(
                        Filename=local_image_path.as_posix(),
                        Bucket=bucket,
                        Key=object_key,
                        ExtraArgs={"ContentType": _content_type(local_image_path)},
                    )

                row["image_uri"] = _build_uri(public_base_url, bucket, object_key)
                row["uploaded_image_name"] = object_name
                writer.writerow(row)
                uploaded += 1
                print(f"[{total}] uploaded: {local_image_path.name} -> {object_key}")

    print("---")
    print(f"Done. total={total} uploaded={uploaded} skipped={skipped}")
    print(f"Output CSV: {output_csv}")


if __name__ == "__main__":
    main()
