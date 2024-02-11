import boto3
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

        return "File uploaded successfully"
    except:
        return "Something went wrong"

    # with open(file_to_upload.read(), "rb") as f:
    #     s3_client.upload_fileobj(f, BUCKET_NAME, "something")
    # response = s3_client.upload_file(file_to_upload, BUCKET_NAME, upload_file_name)


def download_file():
    s3_client.download_file(
        BUCKET_NAME,
        "test_file.pdf",
        "downloaded.pdf",
    )


# upload_file()
# download_file()
