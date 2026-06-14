from fastapi import APIRouter, Depends, HTTPException, status
import os
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timedelta
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils.dependencies import get_current_user
from app.utils.crypto_validator import validator
from app.utils.exchange_rate import exchange_rate_provider


router = APIRouter(prefix="/v1/billing", tags=["Billing & Transactions"])

PAYMENT_WINDOW_HOURS = 1      # Hours until a PENDING order expires
AWAITING_WINDOW_HOURS = 2     # Hours until an AWAITING_VERIFICATION order is marked expired


def _auto_expire_pending(db: Session, user_id: int):
    """Mark any pending transactions past their expiry as 'expired'."""
    now = datetime.utcnow()
    expired_txs = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.status == "pending",
        models.Transaction.expires_at != None,
        models.Transaction.expires_at < now
    ).all()
    for tx in expired_txs:
        tx.status = "expired"
        tx.status_reason = "Kadaluarsa"
    if expired_txs:
        try:
            db.commit()
        except Exception:
            db.rollback()


def _auto_expire_awaiting(db: Session, user_id: int):
    """Mark awaiting_verification orders older than AWAITING_WINDOW_HOURS as expired."""
    cutoff = datetime.utcnow() - timedelta(hours=AWAITING_WINDOW_HOURS)
    stale_txs = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.status == "awaiting_verification",
        models.Transaction.created_at < cutoff
    ).all()
    for tx in stale_txs:
        tx.status = "expired"
        txid_display = tx.tx_hash[:20] + "..." if tx.tx_hash else "tidak diketahui"
        tx.status_reason = f"Tidak terkonfirmasi dalam {AWAITING_WINDOW_HOURS} jam. TXID: {txid_display}"
    if stale_txs:
        try:
            db.commit()
        except Exception:
            db.rollback()



@router.get("/exchange-rate")
async def get_current_exchange_rate():
    """
    Get the current dynamic exchange rate (IDR per 1 USD/USDC).
    """
    rate = await exchange_rate_provider.get_idr_rate()
    return {"rate": rate, "currency": "IDR", "provider": "CoinGecko"}


@router.get("/contact", tags=["Public Config"])
def get_admin_contact():
    """
    Public endpoint: Returns admin contact info for support.
    Configurable via environment variables.
    """
    return {
        "name": os.getenv("ADMIN_NAME", "Admin ShipStream"),
        "email": os.getenv("ADMIN_EMAIL", "admin@shipstream.dev"),
        "whatsapp": os.getenv("ADMIN_WHATSAPP", ""),
        "whatsapp_url": f"https://wa.me/{os.getenv('ADMIN_WHATSAPP', '').replace('+', '').replace('-', '').replace(' ', '')}"
    }

@router.post("/topup", response_model=schemas.Transaction)
async def create_topup(request: schemas.TopupRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Step 1: Create a pending transaction (Invoice). 
    In the real world, this is where you'd call Midtrans to get a payment URL.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fitur Billing memerlukan verifikasi akun. Silakan verifikasi email Anda terlebih dahulu."
        )
    # Verify API key belongs to user if provided
    if request.api_key_id:
        api_key = db.query(models.APIKey).filter(models.APIKey.id == request.api_key_id, models.APIKey.user_id == current_user.id).first()
        if not api_key:
            raise HTTPException(status_code=404, detail="API Key not found")
    
    order_id = f"BILL-{uuid.uuid4().hex[:8].upper()}"
    expires_at = datetime.utcnow() + timedelta(hours=PAYMENT_WINDOW_HOURS)
    
    metadata = None
    if request.payment_method == "crypto":
        # Get current exchange rate to "freeze" the nominal
        idr_rate = await exchange_rate_provider.get_idr_rate()
        expected_usd = round(request.amount / idr_rate, 2)

        # Get the real wallet address from environment
        dest_wallet = os.getenv("MY_CRYPTO_WALLET", "0x47443cef765320f815c651fab1196c7ad55789a5")
        metadata = {
            "address": dest_wallet,
            "chain": request.chain or "base",
            "symbol": request.symbol or "USDC",
            "expected_usd": expected_usd,
            "network": "Mainnet"
        }

    db_transaction = models.Transaction(
        user_id=current_user.id,
        api_key_id=request.api_key_id,
        order_id=order_id,
        amount=request.amount,
        quota_added=request.quota_added,
        payment_method=request.payment_method or "midtrans",
        tx_metadata=metadata,
        status="pending",
        expires_at=expires_at
    )
    try:
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal membuat pesanan topup")
    return db_transaction

@router.get("/history", response_model=List[schemas.Transaction])
def get_billing_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    List all billing activities for the logged-in user, auto-expiring stale orders.
    """
    _auto_expire_pending(db, current_user.id)
    _auto_expire_awaiting(db, current_user.id)
    return db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.created_at.desc()).all()


@router.delete("/cancel/{order_id}")
def cancel_pending_order(order_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Cancel a pending order (user-initiated). Only pending/expired orders can be cancelled."""
    tx = db.query(models.Transaction).filter(
        models.Transaction.order_id == order_id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    if tx.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Order dengan status '{tx.status}' tidak dapat dibatalkan."
        )
    try:
        tx.status = "cancelled"
        tx.status_reason = "Cancel by user"
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal membatalkan pesanan")
    return {"message": f"Order {order_id} telah dibatalkan.", "order_id": order_id, "status": "cancelled", "status_reason": "Cancel by user"}

@router.post("/submit-proof/{order_id}")
async def submit_crypto_proof(order_id: str, tx_hash: str, db: Session = Depends(get_db)):
    """
    Step 2 (Crypto): User submits their Transaction Hash (TXID).
    Now with AUTOMATED VERIFICATION via BaseScan API.
    """
    import re
    # EVM TXID pattern: 0x followed by 64 hex characters
    tx_pattern = r"^0x[a-fA-F0-9]{64}$"
    if not re.match(tx_pattern, tx_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Format Transaction Hash (TXID) tidak valid. Pastikan Anda memasukkan TXID, bukan alamat wallet."
        )

    tx = db.query(models.Transaction).filter(models.Transaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.status == "success":
        return {"message": "Transaksi ini sudah sukses.", "status": "success"}

    if tx.status == "expired":
        raise HTTPException(status_code=400, detail="Order ini sudah kadaluarsa (lebih dari 1 jam). Silakan buat order baru.")

    existing_tx = db.query(models.Transaction).filter(
        models.Transaction.tx_hash == tx_hash
    ).first()
    
    if existing_tx:
        if existing_tx.order_id == order_id:
            # User is resubmitting same hash for same order, likely just checking status
            pass 
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Transaction Hash (TXID) ini sudah pernah digunakan untuk pesanan lain!"
            )
    
    # === AUTO-VERIFY via blockchain ===
    verification = await validator.verify_crypto_payment(
        tx_hash=tx_hash,
        expected_idr_amount=tx.amount,
        chain=tx.tx_metadata.get("chain", "base") if tx.tx_metadata else "base",
        symbol=tx.tx_metadata.get("symbol", "USDC") if tx.tx_metadata else "USDC",
        expected_usd=tx.tx_metadata.get("expected_usd") if tx.tx_metadata else None
    )
    
    if verification["status"] == "success":
        # Global Quota Credit
        user = db.query(models.User).filter(models.User.id == tx.user_id).first()
        if user:
            user.quota_limit += tx.quota_added
        
        # Optional: Legacy/Compatibility check
        api_key = db.query(models.APIKey).filter(models.APIKey.id == tx.api_key_id).first()
        if api_key and api_key.status == "limited":
            api_key.status = "active"
        
        try:
            tx.tx_hash = tx_hash
            tx.status = "success"
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Gagal memverifikasi pembayaran")
        return {
            "message": "Pembayaran BERHASIL diverifikasi secara otomatis! Kuota telah ditambahkan.",
            "status": "success",
            "tx_details": verification
        }
    
    elif verification["status"] == "pending":
        try:
            tx.status = "awaiting_verification"
            db.commit()
        except Exception:
            db.rollback()
    
    else:
        # Decisive Rejection: If amount is wrong/insufficient outside tolerance
        try:
            tx.status = "failed"
            db.commit()
        except Exception:
            db.rollback()
        return {
            "message": f"Verifikasi otomatis GAGAL: {verification['message']}. Pastikan Anda mengirim jumlah yang benar.",
            "status": "failed",
            "details": verification
        }

@router.post("/admin/confirm-payment/{order_id}")
def confirm_payment(order_id: str, db: Session = Depends(get_db)):
    """
    Step 3 (Admin): Admin confirms the payment is valid.
    Only after this, the Quota is added to the API Key.
    """
    # Find transaction
    tx = db.query(models.Transaction).filter(models.Transaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.status == "success":
        return {"message": "Transaction already processed"}

    try:
        # Update status to success
        tx.status = "success"
        
        # Global Quota Credit
        user = db.query(models.User).filter(models.User.id == tx.user_id).first()
        if user:
            user.quota_limit += tx.quota_added
            
        # Optional: Legacy/Compatibility check (reset limited status if any)
        api_key = db.query(models.APIKey).filter(models.APIKey.id == tx.api_key_id).first()
        if api_key and api_key.status == "limited":
            api_key.status = "active"
        
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal mengonfirmasi pembayaran")
    return {
        "message": "Pembayaran berhasil dikonfirmasi. Kuota telah ditambahkan.", 
        "order_id": order_id,
        "new_global_limit": user.quota_limit if user else None,
        "status": "success"
    }
