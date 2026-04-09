import os, math, hashlib
from encryption_utils import EncryptionUtils

class FileManager:
    def __init__(self, storage_path="storage"):
        self.storage_path = storage_path
        self.nodes = [
            os.path.join(storage_path, "node1"),
            os.path.join(storage_path, "node2"),
            os.path.join(storage_path, "node3")
        ]
        for node in self.nodes:
            os.makedirs(node, exist_ok=True)

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

            node_path = os.path.join(self.nodes[i], part_name)
            with open(node_path, "wb") as f:
                f.write(encrypted_chunk)

            parts_meta.append({
                "part_name": part_name,
                "node": f"node{i + 1}",
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
            node_dir = os.path.join(self.storage_path, node)
            part_path = os.path.join(node_dir, part_name)

            if not os.path.exists(part_path):
                raise FileNotFoundError(f"Missing chunk: {part_name} in {node}")

            with open(part_path, "rb") as f:
                encrypted_chunk = f.read()

            try:
                decrypted_chunk = EncryptionUtils.decrypt(encrypted_chunk, secret_key)
                file_data.extend(decrypted_chunk)
            except Exception as e:
                seq = part.get('sequence_order', part.get('order', '?'))
                raise Exception(f"Failed to decrypt part {seq}: {str(e)}")

        return bytes(file_data)

    def delete_file_parts(self, filename, user_id, parts_meta):
        for part in parts_meta:
            part_path = os.path.join(self.storage_path, part['node'], part['part_name'])
            if os.path.exists(part_path):
                os.remove(part_path)

    def get_storage_info(self):
        storage_info = []
        for i in range(3):
            node_dir = self.nodes[i]
            chunks = os.listdir(node_dir) if os.path.exists(node_dir) else []
            total_size = sum(
                os.path.getsize(os.path.join(node_dir, f))
                for f in chunks if os.path.isfile(os.path.join(node_dir, f))
            )
            storage_info.append({
                "name": f"Node {i + 1}",
                "node_id": f"node{i + 1}",
                "chunk_count": len(chunks),
                "chunks": chunks[:15],
                "size": self._fmt(total_size),
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
