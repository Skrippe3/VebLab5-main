import os
import hashlib

def generate_salt():
    return os.urandom(16).hex()

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password, salt, password_hash):
    return hash_password(password, salt) == password_hash

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()