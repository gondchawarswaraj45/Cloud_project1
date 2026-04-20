import os, math, hashlib, boto3
from encryption_utils import EncryptionUtils
from dotenv import load_dotenv

load_dotenv()

class FileManager:
    def __init__(self):
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
        
        self.nodes = ["node1", "node2", "node3"]

    def split_and_encrypt_file(self, file_content, filename, user_id, secret_key):
        file_size = len(file_content)
        original_hash = hashlib.sha256(file_content).hexdigest()
        part_size = math.ceil(file_size / 3)
        parts_meta = []

        for i in range(3):
            start = i * part_size
            end = min((i + 1) * part_size, file_size)
            chunk = file_content[start:end]
            if len(chunk) == 0:
                chunk = b''

            part_name = f"{user_id}_{filename}_part{i + 1}"
            encrypted_chunk = EncryptionUtils.encrypt(chunk, secret_key)

            # Upload to S3 under node-specific prefix
            s3_key = f"{self.nodes[i]}/{part_name}"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=encrypted_chunk
            )

            parts_meta.append({
                "part_name": part_name,
                "node": self.nodes[i],
                "order": i + 1,
                "size": len(encrypted_chunk),
                "original_chunk_size": len(chunk),
            })

        return parts_meta, original_hash

    def decrypt_and_merge_file(self, filename, user_id, parts_meta, secret_key):
        parts_meta.sort(key=lambda x: x.get('sequence_order', x.get('order', 0)))
        file_data = bytearray()

        for part in parts_meta:
            part_name = part['part_name']
            node = part['node']
            s3_key = f"{node}/{part_name}"

            try:
                response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
                encrypted_chunk = response['Body'].read()
            except Exception as e:
                raise FileNotFoundError(f"Missing chunk in S3: {s3_key}. Error: {str(e)}")

            try:
                decrypted_chunk = EncryptionUtils.decrypt(encrypted_chunk, secret_key)
                file_data.extend(decrypted_chunk)
            except Exception as e:
                seq = part.get('sequence_order', part.get('order', '?'))
                raise Exception(f"Failed to decrypt part {seq}: {str(e)}")

        return bytes(file_data)

    def delete_file_parts(self, filename, user_id, parts_meta):
        for part in parts_meta:
            s3_key = f"{part['node']}/{part['part_name']}"
            try:
                self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            except Exception:
                pass # Continue even if delete fails

    def get_storage_info(self):
        storage_info = []
        for i in range(3):
            node_prefix = f"{self.nodes[i]}/"
            try:
                response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=node_prefix)
                objects = response.get('Contents', [])
                total_size = sum(obj['Size'] for obj in objects)
                chunks = [obj['Key'].split('/')[-1] for obj in objects]
                
                storage_info.append({
                    "name": f"AWS S3 Node {i + 1}",
                    "node_id": self.nodes[i],
                    "chunk_count": len(objects),
                    "chunks": chunks[:15],
                    "size": self._fmt(total_size),
                })
            except Exception as e:
                storage_info.append({
                    "name": f"AWS S3 Node {i + 1}",
                    "node_id": self.nodes[i],
                    "chunk_count": 0,
                    "chunks": [],
                    "size": "Error connecting",
                    "error": str(e)
                })
        return storage_info

    @staticmethod
    def _fmt(size_bytes):
        if size_bytes == 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB']
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.2f} {units[i]}"
