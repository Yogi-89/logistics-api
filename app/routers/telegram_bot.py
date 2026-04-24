from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import base as models
import httpx
import os

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])

# We use a dynamic token in the URL for basic protection
@router.post("/webhook/{bot_token}")
async def telegram_webhook(bot_token: str, request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming updates from Telegram.
    """
    data = await request.json()
    
    # We only care about messages for now
    if "message" not in data:
        return {"status": "ignored"}

    msg = data["message"]
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").lower()

    if not chat_id or not text:
        return {"status": "ignored"}

    # Find user by Telegram Chat ID stored in preferences
    # Preferences is a JSON column, so we query it using cast or contains logic
    # In SQLite/PostgreSQL, we can fetch all users with telegram settings and check in memory
    # for simplicity in this UTS project, or use JSON query if database supports it.
    
    target_user = None
    all_users = db.query(models.User).all()
    for user in all_users:
        prefs = user.preferences or {}
        webhooks = prefs.get("webhooks", {})
        
        # Support both numeric and string for flexibility
        reg_chat_id = str(webhooks.get("telegram_chat_id", ""))
        reg_token = webhooks.get("telegram_token", "")
        
        # Security: Only respond if the token in URL matches the token stored for this chat
        if reg_chat_id == str(chat_id) and reg_token == bot_token:
            target_user = user
            break

    response_text = ""

    if text.startswith("/start"):
        response_text = (
            "👋 Selamat datang di ShipStream Pro Max Bot!\n\n"
            "Anda telah berhasil terhubung. Anda akan menerima notifikasi otomatis jika kuota Anda hampir habis.\n\n"
            "Gunakan perintah /cek_kuota untuk melihat saldo akun Anda."
        )
    elif "cek kuota" in text or text.startswith("/cek_kuota"):
        if target_user:
            remaining = target_user.quota_limit - target_user.quota_used
            response_text = (
                f"📊 *Informasi Kuota ShipStream*\n\n"
                f"👤 User: {target_user.username}\n"
                f"📉 Sisa Kuota: {remaining} requests\n"
                f"📈 Total Limit: {target_user.quota_limit}\n\n"
                "Gunakan API Key Anda dengan bijak!"
            )
        else:
            response_text = "❌ Akun Telegram Anda belum terintegrasi dengan Dashboard ShipStream. Silakan hubungkan di menu Settings."
    else:
        response_text = "🤖 Saya tidak mengerti perintah itu. Gunakan /cek_kuota untuk mengecek sisa kuota Anda."

    # Send response back to Telegram
    if response_text:
        async with httpx.AsyncClient() as client:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            await client.post(tg_url, json={
                "chat_id": chat_id,
                "text": response_text,
                "parse_mode": "Markdown"
            })

    return {"status": "success"}
