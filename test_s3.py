import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def test_s3_connection():
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    print(f"Testing connection to bucket: {bucket_name}...")
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Try to list objects
        print("Attempting to list objects...")
        s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print("✅ Successfully connected to S3 and accessed the bucket!")
        
    except Exception as e:
        print(f"❌ Failed to connect to S3: {str(e)}")
        print("\nPlease ensure:")
        print("1. Your AWS_S3_BUCKET_NAME in .env is correct.")
        print("2. The IAM user has 's3:ListBucket' permissions.")
        print("3. The bucket exists and is in the correct region.")

if __name__ == "__main__":
    test_s3_connection()
