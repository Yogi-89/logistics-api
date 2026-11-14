# Payload encryption (RSA-AES & ECC-AES)

ShipStream can decrypt request bodies at the application layer. This protects payloads from
intermediaries that terminate TLS — reverse proxies, API gateways, WAFs — and is the contract
used by the Odoo 19 connector.

TLS is still required. Application-layer encryption is an additional control, not a replacement.

## Enabling it per request

Encryption is opt-in through a header:

| `X-Encryption-Scheme` | Behaviour |
|---|---|
| absent or `NONE` | Body is parsed as plaintext JSON (backward compatible) |
| `RSA-AES` | Body is the encrypted wrapper, AES key wrapped with the server RSA key |
| `ECC-AES` | Body is the encrypted wrapper, AES key derived via ECDH with the server P-256 key |

Protected routes: `POST /v1/cost`, `POST /v1/shipments`, `POST /v1/shipments/batch`.

## Discovering the server keys

```bash
curl https://apilogistik.my.id/v1/security/public-keys \
  -H "X-API-Key: $SHIPSTREAM_KEY"
```

```json
{
  "rsa_public_key_pem": "-----BEGIN PUBLIC KEY-----\n...",
  "ecc_public_key_pem": "-----BEGIN PUBLIC KEY-----\n...",
  "supported_schemes": ["NONE", "RSA-AES", "ECC-AES"],
  "rsa_key_size": 2048,
  "ecc_curve": "SECP256R1"
}
```

## Wire format

The body is a JSON object; every field is base64:

```json
{
  "encrypted_key": "<base64>",
  "nonce": "<base64, 12 bytes>",
  "ciphertext": "<base64, AES-GCM ciphertext || 16-byte tag>"
}
```

### RSA-AES

1. Client generates a random 32-byte AES key and a 12-byte nonce.
2. Encrypts the JSON payload with AES-256-GCM.
3. Wraps the AES key with RSA-2048 **OAEP** (MGF1/SHA-256).
4. Sends the wrapper with `X-Encryption-Scheme: RSA-AES`.

Server unwraps the key with its RSA private key and decrypts with AES-GCM.

### ECC-AES (ECIES)

1. Client generates an ephemeral **P-256** key pair.
2. Performs ECDH with the server's P-256 public key.
3. Derives a 32-byte key with `HKDF-SHA256(salt=None, info="shipstream-ecc-aes-v1")`.
4. Encrypts the payload with AES-256-GCM.
5. `encrypted_key` carries the **ephemeral public key**: 65-byte uncompressed point
   (`0x04 || X || Y`), DER `SubjectPublicKeyInfo`, or a PEM string — the server accepts all three.

### Client example (Python)

```python
import base64, json, os
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BASE = "https://apilogistik.my.id"
HEADERS = {"X-API-Key": os.environ["SHIPSTREAM_KEY"]}

keys = requests.get(f"{BASE}/v1/security/public-keys", headers=HEADERS, timeout=10).json()

def encrypt_rsa(payload: dict) -> dict:
    aes_key, nonce = os.urandom(32), os.urandom(12)
    ct = AESGCM(aes_key).encrypt(nonce, json.dumps(payload).encode(), None)
    pub = serialization.load_pem_public_key(keys["rsa_public_key_pem"].encode())
    wrapped = pub.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return {
        "encrypted_key": base64.b64encode(wrapped).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct).decode(),
    }

body = encrypt_rsa({"origin": 1, "destination": 2, "weight": 1000, "courier": "jne"})
resp = requests.post(
    f"{BASE}/v1/cost",
    json=body,
    headers={**HEADERS, "X-Encryption-Scheme": "RSA-AES"},
    timeout=15,
)
print(resp.status_code, resp.json())
print("server decrypt ms:", resp.headers.get("X-Server-Decrypt-Ms"))
```

Server-side helpers with the same behaviour live in `app/utils/hybrid_crypto.py`
(`encrypt_rsa_aes`, `encrypt_ecc_aes`, `encrypt_request`) and are covered by
`tests/test_hybrid_crypto.py`.

## Responses

Successful decryption adds two headers, useful for research and latency budgets:

| Header | Meaning |
|---|---|
| `X-Server-Decrypt-Ms` | Server-side decrypt time in milliseconds |
| `X-Decrypted-Bytes` | Size of the decrypted JSON payload in bytes |

Failures return **400** with:

```json
{"detail": "Payload decryption or integrity check failed"}
```

That covers a bad wrapper, wrong key material, or a failed GCM authentication tag (tampering).

## Key management

| Source | Variable / path | Notes |
|---|---|---|
| RSA private key | `RSA_PRIVATE_KEY_PEM` | PEM string; wins over the file |
| ECC private key | `ECC_PRIVATE_KEY_PEM` | PEM string; wins over the file |
| Key directory | `KEYS_DIR` | Defaults to `<repo>/keys` |

If neither is provided, keys are generated on first use and written as
`keys/rsa_private.pem` and `keys/ecc_private.pem` (mode `0600`). This makes local runs and fresh
deploys work without provisioning.

On an ephemeral filesystem (Render, containers) generated keys change on every deploy, so clients
must re-fetch `/v1/security/public-keys`. For a stable key pair, set the PEM environment variables
or mount a persistent volume at `KEYS_DIR`.

Never commit `keys/` — it is ignored by `.gitignore`.

## Odoo 19 integration notes

- Fetch `/v1/security/public-keys` once per session and cache it; refresh on a 400 response.
- Store the API key in Odoo's system parameters, never in code.
- Send `X-Encryption-Scheme: RSA-AES` (widely supported) or `ECC-AES` (smaller payloads, faster).
- For batches, use `POST /v1/shipments/batch` with up to 100 shipments per call.
- Treat any 400 from the decryption layer as non-retryable: the payload or key is wrong.

## Limits and caveats

- Nonces are not tracked server-side, so replay protection belongs to the client/TLS layer.
- AES-GCM is authenticated but not nonce-misuse resistant: never reuse a nonce with the same key.
- The middleware only inspects three POST routes; other endpoints stay plaintext-only.
- Key generation happens lazily on first encrypted request (or first public-key fetch).
