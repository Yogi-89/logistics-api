from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils.api_key_auth import validate_api_key
import io
from fpdf import FPDF

from app.utils.limiter import limiter
import random
import string
from datetime import datetime
import os
import httpx
import asyncio

router = APIRouter(prefix="/v1", tags=["Logistics Data (Needs API Key)"])

@router.post("/cost/recommend", response_model=List[schemas.CourierCostRecommendation], summary="Rekomendasi Kurir Termurah")
@limiter.limit("20/minute")
async def calculate_recommendations(
    request: Request,
    payload: schemas.CostRecommendRequest,
    db: Session = Depends(get_db),
    api_key=Depends(validate_api_key)
):
    """
    Menghitung ongkos kirim dari SEMUA kurir yang tersedia dan mengurutkannya dari yang termurah.
    Menggunakan asyncio.gather untuk performa tinggi (paralel request ke RajaOngkir).
    """
    couriers = db.query(models.Courier).all()
    rajaongkir_key = os.getenv("RAJA_ONGKIR_API_KEY")

    origin_city = db.query(models.City).filter(models.City.id == payload.origin).first()
    destination_city = db.query(models.City).filter(models.City.id == payload.destination).first()

    if not origin_city or not destination_city:
        raise HTTPException(status_code=404, detail="Origin or Destination city not found")

    if not origin_city.rajaongkir_id or not destination_city.rajaongkir_id:
        raise HTTPException(
            status_code=400,
            detail="Raja Ongkir ID belum tersedia. Jalankan seed_rajaongkir_ids.py"
        )
    
    # Calculate effective weight (volumetric)
    volumetric_weight = 0
    if payload.length and payload.width and payload.height:
        volumetric_weight = (payload.length * payload.width * payload.height) / 6000 * 1000
    effective_weight = max(payload.weight, volumetric_weight)

    async def get_single_courier_cost(courier):
        results = []
        if rajaongkir_key and rajaongkir_key != "your_raja_ongkir_key_here":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://rajaongkir.komerce.id/api/v1/calculate/domestic-cost",
                        headers={"key": rajaongkir_key},
                        data={
                            "origin": str(origin_city.rajaongkir_id),
                            "destination": str(destination_city.rajaongkir_id),
                            "weight": int(effective_weight),
                            "courier": courier.code.lower()
                        },
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raja_results = data.get("data", [])
                        for r in raja_results:
                            results.append({
                                "courier_name": r.get("name", courier.name),
                                "courier_code": courier.code,
                                "service": r.get("service", ""),
                                "description": r.get("description", ""),
                                "cost": r.get("cost", 0),
                                "etd": r.get("etd", "N/A"),
                                "source": "rajaongkir"
                            })
            except Exception:
                pass
        
        if not results:
            # Internal Fallback
            weight_kg = effective_weight / 1000
            # Base price per courier could be different, but for now we use a slightly varied formula
            base_price = 12000 + (len(courier.name) * 500) 
            results = [
                {
                    "courier_name": courier.name,
                    "courier_code": courier.code,
                    "service": "REG",
                    "cost": int(base_price * weight_kg),
                    "etd": "2-3 Days",
                    "source": "internal_fallback"
                }
            ]
        return results

    # Run all requests in parallel
    tasks = [get_single_courier_cost(c) for c in couriers]
    all_results_lists = await asyncio.gather(*tasks)
    
    # Flatten results
    final_results = [item for sublist in all_results_lists for item in sublist]
    
    # Sort by cost ASC
    final_results.sort(key=lambda x: x["cost"])
    
    return final_results

@router.get("/couriers", response_model=List[schemas.Courier], summary="Daftar Kurir")
@limiter.limit("60/minute")
def get_couriers(request: Request, db: Session = Depends(get_db), api_key=Depends(validate_api_key)):
    user = api_key.owner
    return db.query(models.Courier).all()

@router.get("/cities", response_model=List[schemas.City], summary="Daftar Kota")
@limiter.limit("60/minute")
def get_cities(request: Request, db: Session = Depends(get_db), api_key=Depends(validate_api_key)):
    return db.query(models.City).all()

@router.get("/cities/{city_id}/subdistricts", summary="Daftar Kecamatan")
@limiter.limit("60/minute")
def get_subdistricts(city_id: int, request: Request, db: Session = Depends(get_db), api_key=Depends(validate_api_key)):
    return db.query(models.Subdistrict).filter(models.Subdistrict.city_id == city_id).all()

@router.post("/cost", summary="Kalkulasi Ongkos Kirim (Scale-up)")
@limiter.limit("30/minute")
async def calculate_cost(
    request: Request,
    payload: schemas.CostRequest,
    response: Response,
    db: Session = Depends(get_db),
    api_key=Depends(validate_api_key)
):
    # Logic: Validate cities
    origin = db.query(models.City).filter(models.City.id == payload.origin).first()
    destination = db.query(models.City).filter(models.City.id == payload.destination).first()
    
    if not origin or not destination:
        raise HTTPException(status_code=404, detail="Origin or Destination city not found")

    # Validasi rajaongkir_id tersedia
    if not origin.rajaongkir_id or not destination.rajaongkir_id:
        missing_city = origin.name if not origin.rajaongkir_id else destination.name
        raise HTTPException(
            status_code=400,
            detail=f"Raja Ongkir ID belum tersedia untuk kota {missing_city}. Jalankan seed_rajaongkir_ids.py"
        )

    courier = db.query(models.Courier).filter(models.Courier.code == payload.courier).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    # Volumetric Logic: (P x L x T) / 6000
    volumetric_weight = 0
    if payload.length and payload.width and payload.height:
        volumetric_weight = (payload.length * payload.width * payload.height) / 6000 * 1000 # convert to gram
    
    effective_weight = max(payload.weight, volumetric_weight)
    
    # Scale-up: Real Raja Ongkir Integration
    rajaongkir_key = os.getenv("RAJA_ONGKIR_API_KEY")
    results = []
    
    if rajaongkir_key and rajaongkir_key != "your_raja_ongkir_key_here":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://rajaongkir.komerce.id/api/v1/calculate/domestic-cost",
                    headers={"key": rajaongkir_key},
                    data={
                        "origin": str(origin.rajaongkir_id),
                        "destination": str(destination.rajaongkir_id),
                        "weight": int(effective_weight),
                        "courier": payload.courier.lower()
                    },
                    timeout=5.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    raja_results = data.get("data", [])
                    for r in raja_results:
                        results.append({
                            "service": r.get("service"),
                            "description": r.get("description", ""),
                            "cost": r.get("cost", 0),
                            "etd": r.get("etd", "N/A"),
                            "source": "rajaongkir"
                        })
        except Exception:
            pass

    if not results:
        # Fallback Logic (Dummy calculation if API fails or no key)
        weight_kg = effective_weight / 1000
        base_price = 12000 + (len(origin.name) * 100)
        results = [
            {"service": "REG", "description": "Reguler Service", "cost": int(base_price * weight_kg), "etd": "2-3 Days", "source": "internal_fallback"},
            {"service": "EXP", "description": "Express Service", "cost": int(base_price * 1.5 * weight_kg), "etd": "1 Day", "source": "internal_fallback"}
        ]
    
    return {
        "origin": origin.name,
        "destination": destination.name,
        "courier": courier.name,
        "actual_weight": payload.weight,
        "volumetric_weight": int(volumetric_weight),
        "effective_weight": int(effective_weight),
        "results": results,
        "currency": "IDR"
    }

@router.post("/shipments", summary="Generate AWB (Waybill)")
@limiter.limit("10/minute")
def create_shipment(
    request: Request,
    payload: schemas.ShipmentCreate,
    db: Session = Depends(get_db),
    api_key=Depends(validate_api_key)
):
    # Generate AWB
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    awb = f"SS-{payload.service_type}-{random_str}"
    
    # Calculate Cost (re-verify)
    base_price = 12000
    effective_weight = payload.weight_gram
    if payload.length_cm and payload.width_cm and payload.height_cm:
        volumetric = (payload.length_cm * payload.width_cm * payload.height_cm) / 6000 * 1000
        effective_weight = max(payload.weight_gram, volumetric)
    
    shipping_cost = (effective_weight / 1000) * base_price
    
    new_tracking = models.Tracking(
        awb=awb,
        courier_id=payload.courier_id,
        status="MANIFESTED",
        origin_city_id=payload.origin_city_id,
        destination_city_id=payload.destination_city_id,
        service_type=payload.service_type,
        weight_gram=payload.weight_gram,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        height_cm=payload.height_cm,
        insurance_value=payload.insurance_value,
        shipping_cost=shipping_cost,
        sender_name=payload.sender_name,
        sender_phone=payload.sender_phone,
        sender_address=payload.sender_address,
        sender_postal_code=payload.sender_postal_code,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_address=payload.receiver_address,
        receiver_postal_code=payload.receiver_postal_code,
        history=[{
            "status": "MANIFESTED",
            "location": "Origin Warehouse",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Package is being prepared for shipment"
        }]
    )
    
    try:
        db.add(new_tracking)
        db.commit()
        db.refresh(new_tracking)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal membuat shipment: {str(e)}")
    
    return {
        "status": "success",
        "awb": awb,
        "shipping_cost": shipping_cost,
        "etd": "2-3 Days"
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
        "service_type": track.service_type,
        "weight_gram": track.weight_gram,
        "shipping_cost": track.shipping_cost,
        "sender_name": track.sender_name,
        "receiver_name": track.receiver_name,
        "receiver_address": track.receiver_address,
        "history": track.history
    }

@router.post("/tracking/{awb}/update", summary="Update Status Tracking")
@limiter.limit("20/minute")
def update_tracking_status(
    request: Request,
    awb: str,
    status: str,
    location: str,
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key=Depends(validate_api_key)
):
    track = db.query(models.Tracking).filter(models.Tracking.awb == awb).first()
    if not track:
        raise HTTPException(status_code=404, detail="Tracking number (AWB) not found")
    
    new_history = list(track.history)
    new_history.append({
        "status": status,
        "location": location,
        "timestamp": datetime.utcnow().isoformat(),
        "note": note
    })
    
    try:
        track.status = status
        track.history = new_history
        track.last_updated = datetime.utcnow()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui status tracking")
    return {"status": "success", "current_status": status}

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
    # Add Logo
    logo_path = os.path.join("frontend", "assets", "logo_icon_white_modern_blue-removebg-preview.png")
    if os.path.exists(logo_path):
        pdf.image(logo_path, 10, 8, 12) # x=10, y=8, width=12mm
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(25, 8) # Offset title to the right of the logo
    pdf.cell(0, 10, L["title"], 0, 1, "L")
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(25, 16)
    pdf.cell(0, 5, L["subtitle"], 0, 1, "L")
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
