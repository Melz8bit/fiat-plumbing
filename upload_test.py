import boto3
import os

from dotenv import load_dotenv

load_dotenv()

access_key = os.getenv("S3_ACCESS_KEY")
secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
s3_region = os.getenv("S3_REGION")
bucket_name = os.getenv("S3_BUCKET_NAME")


session = boto3.session.Session()
s3_client = session.client(
    "s3",
    region_name=s3_region,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_access_key,
)


def upload_file():

    response = s3_client.upload_file("TEST_FILE.pdf", bucket_name, "test_file.pdf")
    print(f"{response=}")

    # try:
    #     response = s3_client.list_buckets()
    #     print(f"{response=}")
    #     buckets = []
    #     for bucket in response["Buckets"]:
    #         buckets += {bucket["Name"]}

    # except:
    #     print("Couldn't get buckets.")
    #     raise
    # else:
    #     return buckets


def download_file():
    s3_client.download_file(
        bucket_name,
        "test_file.pdf",
        "downloaded.pdf",
    )


# upload_file()
download_file()
