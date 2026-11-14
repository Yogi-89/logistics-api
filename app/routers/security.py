"""Public-key discovery for application-layer payload encryption.

Clients (for example an Odoo 19 connector) fetch the server's RSA and ECC public keys here,
then encrypt request bodies with the ``RSA-AES`` or ``ECC-AES`` scheme described in
``app/utils/hybrid_crypto.py``.
"""

from fastapi import APIRouter, Depends

from app.utils.api_key_auth import validate_api_key
from app.utils.hybrid_crypto import (
    ECC_CURVE_NAME,
    GCM_NONCE_BYTES,
    HKDF_INFO,
    RSA_KEY_SIZE,
    SUPPORTED_SCHEMES,
    get_public_keys,
)

router = APIRouter(prefix="/v1/security", tags=["Security (Encryption)"])


@router.get("/public-keys", summary="Public keys & supported encryption schemes")
def get_server_public_keys(api_key=Depends(validate_api_key)):
    """
    Returns the server's public keys and the contract a client must follow.

    Send the encrypted JSON wrapper as the request body together with the header
    ``X-Encryption-Scheme: RSA-AES`` (or ``ECC-AES``). Omit the header, or set it to
    ``NONE``, to send plaintext JSON as before.
    """
    keys = get_public_keys()
    return {
        "rsa_public_key_pem": keys["rsa_public_key_pem"],
        "ecc_public_key_pem": keys["ecc_public_key_pem"],
        "supported_schemes": list(SUPPORTED_SCHEMES),
        "rsa_key_size": RSA_KEY_SIZE,
        "ecc_curve": ECC_CURVE_NAME,
        "wire_format": {
            "encrypted_key": "base64",
            "nonce": f"base64, {GCM_NONCE_BYTES} bytes",
            "ciphertext": "base64, AES-GCM ciphertext including 16-byte tag",
        },
        "rsa_aes": {
            "key_wrap": "RSA-OAEP with MGF1/SHA-256",
            "content_encryption": "AES-256-GCM",
        },
        "ecc_aes": {
            "exchange": "ECDH on SECP256R1 (P-256)",
            "kdf": "HKDF-SHA256",
            "hkdf_info": HKDF_INFO.decode("ascii"),
            "content_encryption": "AES-256-GCM",
        },
    }
