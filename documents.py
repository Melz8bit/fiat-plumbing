import boto3
import io
import logging
import os

from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

session = boto3.session.Session()
s3_client = session.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)


def upload_file(file_to_upload, upload_file_name):
    try:
        # Safety check: If BUCKET_NAME is None, this is the culprit
        if not BUCKET_NAME or not isinstance(BUCKET_NAME, str):
            raise TypeError(f"BUCKET_NAME must be a string, got {type(BUCKET_NAME)}")

        file_to_upload.seek(0)

        # Using the standard put_object with a read() to be safe
        s3_client.put_object(
            Body=file_to_upload.read(),
            Bucket=str(BUCKET_NAME),
            Key=str(upload_file_name),
            ContentType=file_to_upload.content_type,
        )
        return True
    except Exception as e:
        logging.error("S3 upload error: %s - %s", type(e).__name__, e)
        return False


def upload_proposal(pdf_bytes, project_id, upload_file_name):
    try:
        # ---- Upload to S3 ----
        bucket = BUCKET_NAME
        key = secure_filename(upload_file_name)

        s3_client.upload_fileobj(io.BytesIO(pdf_bytes), bucket, key)

        return "Proposal finalized and saved to documents."
    except Exception as e:
        logging.error("S3 proposal upload error: %s", e)
        return "Error: Proposal document was not created"


def download_file(doc_filename):
    file = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=doc_filename,
    )
    return file


def list_coi_year_folders():
    """Return year subfolders under company-docs/certificates-of-liability/ that contain at least one PDF."""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="company-docs/certificates-of-liability/",
        )
        folders = set()
        for obj in response.get("Contents", []):
            key = obj["Key"].removeprefix("company-docs/certificates-of-liability/")
            parts = key.split("/")
            if len(parts) >= 2 and parts[0] and parts[1].lower().endswith(".pdf"):
                folders.add(parts[0])
        return sorted(folders, reverse=True)
    except Exception as e:
        logging.error("S3 COI folder list error: %s", e)
        return []


def list_company_doc_folders():
    """Return all nested folder paths under company-docs/ that contain files."""
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        folders = set()
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix="company-docs/"):
            for obj in page.get("Contents", []):
                key = obj["Key"].removeprefix("company-docs/")
                parts = key.split("/")
                # Collect every directory component (skip the filename at the end)
                for depth in range(1, len(parts)):
                    folder = "/".join(parts[:depth])
                    if folder:
                        folders.add(folder)
        return sorted(folders)
    except Exception as e:
        logging.error("S3 folder list error: %s", e)
        return []


def upload_company_doc(file, folder, filename):
    key = f"company-docs/{folder}/{secure_filename(filename)}"
    try:
        file.seek(0)
        s3_client.put_object(
            Body=file.read(),
            Bucket=BUCKET_NAME,
            Key=key,
            ContentType=file.content_type,
        )
        return key
    except Exception as e:
        logging.error("S3 company doc upload error: %s", e)
        return None


def delete_file(key):
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        return True
    except Exception as e:
        logging.error("S3 delete error: %s", e)
        return False
