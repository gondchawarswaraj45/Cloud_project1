from database import init_db
print("Initializing DB...")
init_db()
print("DB initialized.")
from encryption_utils import EncryptionUtils
key = EncryptionUtils.generate_key()
data = b"Testing 123"
enc = EncryptionUtils.encrypt(data, key)
dec = EncryptionUtils.decrypt(enc, key)
print("Encryption/Decryption test: PASSED" if data == dec else "FAILED")
