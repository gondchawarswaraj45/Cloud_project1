"""
Data Integrity Test Suite
Tests: split → encrypt → decrypt → merge with zero data loss
"""
import sys
import hashlib
sys.path.insert(0, '.')
from encryption_utils import EncryptionUtils
from file_manager import FileManager

fm = FileManager()

# Test cases with different sizes and data types
test_cases = [
    ("Small text", b"Hello, this is a test file for SaaS Cloud HDFS!"),
    ("2 bytes", b"AB"),
    ("1 byte", b"X"),
    ("3 bytes (exact split)", b"ABC"),
    ("Large text", b"X" * 10000),
    ("Binary data", bytes(range(256)) * 10),
    ("Empty-ish", b"\x00\x01\x02"),
    ("Unicode bytes", "Hello 🌍 World 💻".encode("utf-8")),
]

all_passed = True
for name, content in test_cases:
    original_hash = hashlib.sha256(content).hexdigest()
    original_size = len(content)

    # Split and encrypt
    parts_meta, file_hash = fm.split_and_encrypt_file(
        content, f"test_{name}.bin", 999, "testkey1234567890"
    )

    # Verify hash
    assert file_hash == original_hash, f"{name}: Hash mismatch after split!"

    # Add sequence_order for DB simulation
    for p in parts_meta:
        p["sequence_order"] = p["order"]

    # Decrypt and merge
    recovered = fm.decrypt_and_merge_file(
        f"test_{name}.bin", 999, parts_meta, "testkey1234567890"
    )

    recovered_hash = hashlib.sha256(recovered).hexdigest()

    # Verify integrity
    size_ok = len(recovered) == original_size
    hash_ok = recovered_hash == original_hash
    content_ok = recovered == content

    if size_ok and hash_ok and content_ok:
        chunk_sizes = [p["original_chunk_size"] for p in parts_meta]
        print(f"  PASS  {name:20s} | {original_size:6d}B | chunks: {chunk_sizes}")
    else:
        all_passed = False
        print(f"  FAIL  {name}")
        print(f"        Size: {original_size} -> {len(recovered)} ({'OK' if size_ok else 'MISMATCH'})")
        print(f"        Hash: {'OK' if hash_ok else 'MISMATCH'}")

    # Cleanup
    fm.delete_file_parts(f"test_{name}.bin", 999, parts_meta)

print()
if all_passed:
    print("=" * 60)
    print("  ALL TESTS PASSED!")
    print("  Zero data loss | Correct sequence | Perfect SHA-256 match")
    print("=" * 60)
else:
    print("SOME TESTS FAILED!")
    sys.exit(1)
