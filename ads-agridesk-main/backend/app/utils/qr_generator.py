import os

import qrcode
from PIL import Image

from app.config import settings


class QRCodeGenerator:
    @staticmethod
    def generate_qr_code(data: str, filename: str) -> str:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img: Image.Image = qr.make_image(fill_color="black", back_color="white")
        from io import BytesIO
        from app.utils.storage import storage_service
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        s3_key = storage_service.upload_file(buffer.getvalue(), filename)
        return s3_key
