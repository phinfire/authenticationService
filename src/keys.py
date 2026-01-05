import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

KEYS_DIR = "keys"


def generate_rsa_keys():
    """Generate RSA public and private keys on startup if they don't exist."""
    os.makedirs(KEYS_DIR, exist_ok=True)
    
    private_key_path = os.path.join(KEYS_DIR, "private_key.pem")
    public_key_path = os.path.join(KEYS_DIR, "public_key.pem")
    
    # Generate keys if they don't exist
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        print("Generating new RSA key pair...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Generate public key
        public_key = private_key.public_key()
        
        # Save private key
        with open(private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        print("RSA keys generated and saved")
    else:
        print("RSA keys already exist")


def load_private_key():
    """Load private key from file."""
    private_key_path = os.path.join(KEYS_DIR, "private_key.pem")
    with open(private_key_path, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )


def load_public_key():
    """Load public key from file."""
    public_key_path = os.path.join(KEYS_DIR, "public_key.pem")
    with open(public_key_path, "rb") as f:
        return serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )


def get_private_key_pem():
    """Get private key as PEM string."""
    private_key = load_private_key()
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()


def get_public_key_pem():
    """Get public key as PEM string."""
    public_key = load_public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
