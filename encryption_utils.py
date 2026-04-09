import struct
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class EncryptionUtils:
    @staticmethod
    def encrypt(data, key):
        if isinstance(key, str):
            key = key.encode('utf-8').ljust(32, b'\0')[:32]
        elif isinstance(key, bytes):
            key = key.ljust(32, b'\0')[:32]
        original_size = len(data)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return struct.pack('>I', original_size) + cipher.nonce + tag + ciphertext

    @staticmethod
    def decrypt(encrypted_data, key):
        if isinstance(key, str):
            key = key.encode('utf-8').ljust(32, b'\0')[:32]
        elif isinstance(key, bytes):
            key = key.ljust(32, b'\0')[:32]
        original_size = struct.unpack('>I', encrypted_data[:4])[0]
        nonce = encrypted_data[4:20]
        tag = encrypted_data[20:36]
        ciphertext = encrypted_data[36:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        try:
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted[:original_size]
        except ValueError:
            raise Exception("Decryption failed: data corrupted or wrong key.")
