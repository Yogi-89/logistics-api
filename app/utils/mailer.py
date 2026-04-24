import os
from datetime import datetime

def send_otp_email(to_email: str, otp_code: str):
    """
    Sends a professional OTP email using Resend.com
    Lazy import for environment robustness on Windows.
    """
    try:
        import resend
    except ImportError:
        print("[Mailer] ERROR: 'resend' library not found. Please restart uvicorn.")
        return False

    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[Mailer] WARNING: RESEND_API_KEY not found in .env. Skipping email.")
        return False

    resend.api_key = api_key
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                }}
                .header {{
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .logo {{
                    color: #2563eb;
                    font-size: 24px;
                    font-weight: bold;
                    text-decoration: none;
                }}
                .content {{
                    padding: 30px 0;
                    text-align: center;
                }}
                .otp-box {{
                    background: #f8fafc;
                    border: 2px dashed #e2e8f0;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 5px;
                    color: #1e293b;
                    border-radius: 8px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #94a3b8;
                    padding-top: 20px;
                    border-top: 1px solid #f0f0f0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 500;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="#" class="logo">SHIPSTREAM</a>
                </div>
                <div class="content">
                    <h1>Verifikasi Akun Anda</h1>
                    <p>Terima kasih telah bergabung dengan ShipStream API. Gunakan kode verifikasi di bawah ini untuk mengaktifkan akun Anda:</p>
                    <div class="otp-box">{otp_code}</div>
                    <p style="color: #64748b; font-size: 14px;">Kode ini akan kedaluwarsa dalam 15 menit. Mohon jangan sampaikan kode ini pada siapapun.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} ShipStream Logistics API. All rights reserved.</p>
                    <p>Pesan ini dikirim secara otomatis. Mohon tidak membalas email ini.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": f"ShipStream Logistics <{from_email}>",
            "to": [to_email],
            "subject": f"{otp_code} adalah Kode Verifikasi ShipStream Anda",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        return response
    except Exception as e:
        print(f"[Mailer] ERROR sending email via Resend: {e}")
        return None
