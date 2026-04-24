from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils.api_key_auth import validate_api_key
import io
from fpdf import FPDF

router = APIRouter(prefix="/v1", tags=["Logistics Data (Needs API Key)"])

@router.get("/couriers", response_model=List[schemas.Courier], summary="Daftar Kurir", description="Mengambil daftar mitra kurir logistik yang tersedia (JNE, J&T, SiCepat, dll) lengkap dengan Logo dan Deskripsi layanan.")
def get_couriers(response: Response, db: Session = Depends(get_db), api_key=Depends(validate_api_key)):
    user = api_key.owner
    response.headers["X-RateLimit-Limit"] = str(user.quota_limit)
    response.headers["X-RateLimit-Remaining"] = str(user.quota_limit - user.quota_used)
    response.headers["X-RateLimit-Used"] = str(user.quota_used)
    
    return db.query(models.Courier).all()

@router.get("/cities", response_model=List[schemas.City], summary="Daftar Kota operasional", description="Mengambil data wilayah kiriman di Indonesia yang didukung oleh sistem, termasuk Tipe (Kota/Kabupaten) dan Kode Pos.")
def get_cities(response: Response, db: Session = Depends(get_db), api_key=Depends(validate_api_key)):
    user = api_key.owner
    response.headers["X-RateLimit-Limit"] = str(user.quota_limit)
    response.headers["X-RateLimit-Remaining"] = str(user.quota_limit - user.quota_used)
    
    return db.query(models.City).all()

@router.get("/cost", summary="Kalkulasi Ongkos Kirim", description="Menghitung estimasi biaya pengiriman antar kota berdasarkan berat paket dan pilihan kurir. Mengembalikan berbagai jenis layanan (REG, OKE, YES) beserta estimasi waktu sampai (ETD).")
def calculate_cost(
    response: Response,
    origin_id: int = Query(..., description="ID Kota Asal (lihat /v1/cities)", examples=[6]),
    destination_id: int = Query(..., description="ID Kota Tujuan (lihat /v1/cities)", examples=[7]),
    weight_gram: int = Query(1000, description="Berat paket dalam gram (default 1000g)", examples=[1000]),
    courier_code: str = Query(..., description="Kode kurir (jne, jnt, sicepat, pos, anteraja)", examples=["jne"]),
    db: Session = Depends(get_db),
    api_key=Depends(validate_api_key)
):
    user = api_key.owner
    response.headers["X-RateLimit-Limit"] = str(user.quota_limit)
    response.headers["X-RateLimit-Remaining"] = str(user.quota_limit - user.quota_used)
    # Logic: Validate cities
    origin = db.query(models.City).filter(models.City.id == origin_id).first()
    destination = db.query(models.City).filter(models.City.id == destination_id).first()
    
    if not origin or not destination:
        raise HTTPException(status_code=404, detail="Origin or Destination city not found")

    courier = db.query(models.Courier).filter(models.Courier.code == courier_code).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    # Simple logic for UTS: Generate multiple services based on courier
    services = []
    base_price = 10000 + (len(courier.name) * 100) # Arbitrary base
    weight_kg = weight_gram / 1000
    
    if courier.code == "jne":
        services = [
            {"service": "REG", "description": "Reguler", "cost": int(base_price * weight_kg), "etd": "2-3 Days"},
            {"service": "YES", "description": "Yakin Esok Sampai", "cost": int(base_price * 1.5 * weight_kg), "etd": "1 Day"},
            {"service": "OKE", "description": "Ongkos Kirim Ekonomis", "cost": int(base_price * 0.8 * weight_kg), "etd": "4-5 Days"}
        ]
    elif courier.code == "jnt":
        services = [
            {"service": "EZ", "description": "Regular Service", "cost": int(base_price * 0.95 * weight_kg), "etd": "2-3 Days"},
            {"service": "ECO", "description": "Economy Service", "cost": int(base_price * 0.7 * weight_kg), "etd": "5-7 Days"}
        ]
    else:
        services = [
            {"service": "REG", "description": "Regular Service", "cost": int(base_price * weight_kg), "etd": "3-4 Days"},
            {"service": "EXP", "description": "Express Service", "cost": int(base_price * 1.4 * weight_kg), "etd": "1-2 Days"}
        ]
    
    return {
        "origin": origin.name,
        "destination": destination.name,
        "courier": courier.name,
        "weight": weight_gram,
        "results": services,
        "currency": "IDR"
    }


@router.get("/tracking/{awb}", response_model=schemas.TrackingInfo, summary="Lacak Paket (Tracking)", description="Melacak status terkini dan histori perjalanan paket berdasarkan nomor resi (AWB) secara real-time.")
def track_package(
    response: Response,
    awb: str = Path(..., description="Nomor Resi Paketan", examples=["LGS-12345678"]), 
    db: Session = Depends(get_db), 
    api_key=Depends(validate_api_key)
):
    user = api_key.owner
    response.headers["X-RateLimit-Limit"] = str(user.quota_limit)
    response.headers["X-RateLimit-Remaining"] = str(user.quota_limit - user.quota_used)
    track = db.query(models.Tracking).filter(models.Tracking.awb == awb).first()
    if not track:
        raise HTTPException(status_code=404, detail="Tracking number (AWB) not found")
    
    courier = db.query(models.Courier).filter(models.Courier.id == track.courier_id).first()
    
    return {
        "awb": track.awb,
        "courier": courier.name if courier else "Unknown",
        "status": track.status,
        "history": track.history
    }

@router.get("/label/{awb}", summary="Generate Shipping Label (PDF)", description="Menghasilkan label pengiriman (Shipping Label) standar industri dalam format PDF untuk dicetak.")
def get_shipping_label(
    awb: str = Path(..., description="Nomor Resi Paketan"), 
    lang: str = Query("id", description="Language for the label (id/en)"),
    db: Session = Depends(get_db), 
    api_key=Depends(validate_api_key)
):
    track = db.query(models.Tracking).filter(models.Tracking.awb == awb).first()
    if not track:
        raise HTTPException(status_code=404, detail="Tracking number (AWB) not found")
    
    courier = db.query(models.Courier).filter(models.Courier.id == track.courier_id).first()
    
    # Translations for PDF
    txt = {
        "id": {
            "title": "SHIPSTREAM LOGISTICS",
            "subtitle": "Label Pengiriman Digital Resmi",
            "awb": "AWB / RESI:",
            "courier": "KURIR:",
            "sender": " PENGIRIM (SENDER)",
            "receiver": " PENERIMA (RECEIVER)",
            "address": "Alamat:",
            "phone": "Telp:",
            "note": "Note: Simpan label ini sebagai bukti pengiriman yang sah. Hubungi support@shipstream.com jika ada kendala sistem."
        },
        "en": {
            "title": "SHIPSTREAM LOGISTICS",
            "subtitle": "Official Digital Shipping Label",
            "awb": "AWB / RESI:",
            "courier": "COURIER:",
            "sender": " SENDER",
            "receiver": " RECEIVER",
            "address": "Address:",
            "phone": "Phone:",
            "note": "Note: Keep this label as valid proof of shipment. Contact support@shipstream.com for any system issues."
        }
    }
    
    L = txt.get(lang, txt["id"])

    # Generate PDF (A6 format: 105mm x 148mm)
    pdf = FPDF(format=(105, 148))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # 1. Header Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, L["title"], 0, 1, "C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, L["subtitle"], 0, 1, "C")
    pdf.ln(5)
    
    # Draw Line
    pdf.line(10, 30, 95, 30)
    
    # 2. Main Labels Segment
    pdf.set_xy(10, 35)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 6, L["awb"], 0, 0)
    pdf.cell(45, 6, L["courier"], 0, 1)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(40, 8, f"{track.awb}", 1, 0, "C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(45, 8, f"{courier.name.upper() if courier else 'N/A'}", 1, 1, "C")
    pdf.ln(5)
    
    # 3. Sender & Receiver Sections
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 6, L["sender"], 1, 1, "L", fill=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f" {track.sender_name or 'Default Sender'}", "LR", 1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f" {L['phone']} {track.sender_phone or '-'}", "LRB", 1)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, L["receiver"], 1, 1, "L", fill=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" {track.receiver_name or 'Customer Name'}", "LR", 1)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, f" {L['address']} {track.receiver_address or '-'}\n {L['phone']} {track.receiver_phone or '-'}", "LRB")
    pdf.ln(5)

    # 4. Footer & Verification
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, L["note"], 0, "C")
    
    # Simple Visual Barcode (Lines representation)
    pdf.ln(2)
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(20, 125, 65, 4, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(20, 130)
    pdf.cell(65, 5, f"* {track.awb} *", 0, 1, "C")

    # Output to bytes
    pdf_data = pdf.output()
    
    return Response(
        content=bytes(pdf_data), 
        media_type="application/pdf", 
        headers={
            'Content-Disposition': f'attachment; filename="shipstream_label_{track.awb}.pdf"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
    )

@router.get("/quota", summary="Cek Kuota API", description="Mendapatkan sisa kuota Anda yang terhubung dengan API Key ini. Berguna untuk pengecekan otomatis dari sisi aplikasi klien.")
def get_quota_status(api_key=Depends(validate_api_key)):
    user = api_key.owner
    return {
        "status": "success",
        "username": user.username,
        "quota_limit": user.quota_limit,
        "quota_used": user.quota_used,
        "quota_remaining": user.quota_limit - user.quota_used,
        "is_active": user.is_active
    }
