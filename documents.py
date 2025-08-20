import boto3
import io
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


def upload_file(file_to_upload, upload_file_name, filetype):
    try:
        s3_client.put_object(
            Body=file_to_upload,
            Bucket=BUCKET_NAME,
            Key=secure_filename(upload_file_name),
            ContentType=file_to_upload.content_type,
        )

        print("File uploaded successfully")
    except Exception as e:
        print(f"Something went wrong - {e}")


def upload_proposal(pdf_bytes, project_id, upload_file_name):
    try:
        # ---- Upload to S3 ----
        # s3_client = boto3.client("s3")
        bucket = BUCKET_NAME
        key = secure_filename(upload_file_name)

        s3_client.upload_fileobj(io.BytesIO(pdf_bytes), bucket, key)

        # # Optional: signed URL for immediate download
        # signed_url = s3_client.generate_presigned_url(
        #     "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=3600
        # )

        return "Proposal finalized and saved to documents."
    except Exception as e:
        print(f"Something went wrong - {e}")
        return "Error: Proposal document was not created"


def download_file(doc_filename):
    file = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=doc_filename,
    )
    return file
