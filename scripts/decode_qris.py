"""Decode a QR image and validate the EMVCo/QRIS payload (TLV structure + CRC16).

Usage:
    python scripts/decode_qris.py path/to/qr.jpeg

Exit codes: 0 valid QRIS, 1 unreadable image, 2 no QR payload, 3 invalid payload/CRC.
"""

import sys

import cv2


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, the checksum defined by the EMVCo QR spec."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return crc


def parse_tlv(payload: str):
    fields, i = [], 0
    while i + 4 <= len(payload):
        tag, length = payload[i : i + 2], payload[i + 2 : i + 4]
        if not length.isdigit():
            break
        n = int(length)
        fields.append((tag, payload[i + 4 : i + 4 + n]))
        i += 4 + n
    return fields, payload[i:]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    image = cv2.imread(sys.argv[1])
    if image is None:
        print("image: unreadable")
        return 1

    detector = cv2.QRCodeDetector()
    payload, _, _ = detector.detectAndDecode(image)
    if not payload:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        payload, _, _ = detector.detectAndDecode(upscaled)

    if not payload:
        print("DECODE: failed (no QR payload found)")
        return 2

    print("payload:", payload)
    if not payload.startswith("000201"):
        print("VERDICT: not an EMVCo QRIS payload")
        return 3

    fields, rest = parse_tlv(payload)
    labels = {
        "00": "Payload format",
        "01": "Point of initiation",
        "52": "Merchant category",
        "53": "Currency",
        "54": "Amount",
        "58": "Country",
        "59": "Merchant name",
        "60": "Merchant city",
        "61": "Postal code",
        "63": "CRC",
    }
    for tag, value in fields:
        print(f"  {tag} {labels.get(tag, 'nested/other'):20} = {value}")

    if rest:
        print("  trailing data:", rest)

    crc_field = next((v for t, v in fields if t == "63"), None)
    if not crc_field:
        print("VERDICT: missing CRC (tag 63)")
        return 3

    expected = f"{crc16_ccitt(payload[:-4].encode('ascii')):04X}"
    valid = expected == crc_field.upper()
    mode = next((v for t, v in fields if t == "01"), "")
    print(f"CRC: printed={crc_field} computed={expected} -> {'VALID' if valid else 'INVALID'}")
    print("type:", "static" if mode == "11" else "dynamic" if mode == "12" else "unknown")
    return 0 if valid else 3


if __name__ == "__main__":
    raise SystemExit(main())
