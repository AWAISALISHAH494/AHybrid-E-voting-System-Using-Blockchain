import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


class EncryptionService:
    def __init__(self, key: str):
        self.key = hashlib.sha256(key.encode('utf-8')).digest()

    def encrypt(self, plaintext: str) -> bytes:
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        return iv + ciphertext

    def decrypt(self, encrypted_data: bytes) -> str:
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)
        plaintext = unpad(padded_plaintext, AES.block_size)
        return plaintext.decode('utf-8')

    @staticmethod
    def hash_sha256(data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_voter_hash(cnic: str, election_id: int) -> str:
        combined = f"{cnic}:{election_id}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
