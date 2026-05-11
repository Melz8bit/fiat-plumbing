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
