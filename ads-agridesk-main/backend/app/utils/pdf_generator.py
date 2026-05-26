import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from io import BytesIO
from textwrap import wrap
from typing import Dict, Optional, Union, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from app.config import settings
from app.domain.exceptions import InternalError


class PDFGenerator:
    @staticmethod
    def _format_label(key: str) -> str:
        return key.replace("_", " ").strip().title()

    @staticmethod
    def _wrapped_lines(text: str, font_size: float, max_width: float) -> list[str]:
        approx_chars = max(int(max_width / (font_size * 0.52)), 18)
        return wrap(text, width=approx_chars) or [text]

    @staticmethod
    def _draw_paragraph(
        pdf_canvas: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        font_name: str = "Helvetica",
        font_size: float = 10.5,
        leading: float = 13,
        justify: bool = False,
    ) -> float:
        pdf_canvas.setFont(font_name, font_size)
        current_y = y
        lines = PDFGenerator._wrapped_lines(text, font_size, max_width)
        for i, line in enumerate(lines):
            if justify and i < len(lines) - 1 and " " in line:
                # Don't justify lines that are artificially broken by newlines
                text_width = pdf_canvas.stringWidth(line, font_name, font_size)
                extra_space = max_width - text_width
                words = line.split(" ")
                num_gaps = len(words) - 1
                
                # Only justify if extra space is not absurdly large (e.g. half the line empty)
                if num_gaps > 0 and extra_space < (max_width * 0.4):
                    space_addition = extra_space / num_gaps
                    word_x = x
                    for word in words:
                        pdf_canvas.drawString(word_x, current_y, word)
                        word_x += pdf_canvas.stringWidth(word + " ", font_name, font_size) + space_addition
                    current_y -= leading
                    continue

            pdf_canvas.drawString(x, current_y, line)
            current_y -= leading
        return current_y

    @staticmethod
    def _draw_header(pdf_canvas: canvas.Canvas, width: float, height: float, template_name: str) -> float:
        pdf_canvas.setFillColor(colors.HexColor("#184d47"))
        pdf_canvas.setFont("Helvetica-Bold", 14)
        pdf_canvas.drawString(2.15 * cm, height - 1.9 * cm, "AGRIDESK")
        pdf_canvas.setFillColor(colors.HexColor("#6b7280"))
        pdf_canvas.setFont("Helvetica", 8.5)
        pdf_canvas.drawString(2.15 * cm, height - 2.38 * cm, "Sistem Administrasi Surat Akademik")
        pdf_canvas.setStrokeColor(colors.HexColor("#184d47"))
        pdf_canvas.setLineWidth(1.1)
        pdf_canvas.line(2 * cm, height - 2.85 * cm, width - 2 * cm, height - 2.85 * cm)
        pdf_canvas.setFillColor(colors.black)
        pdf_canvas.setFont("Helvetica-Bold", 13)
        pdf_canvas.drawCentredString(width / 2, height - 3.7 * cm, template_name.upper())
        return height - 4.35 * cm

    @staticmethod
    def _draw_meta_box(pdf_canvas: canvas.Canvas, width: float, top_y: float, jenis: str, keperluan: str) -> float:
        box_height = 2.05 * cm
        box_y = top_y - box_height
        pdf_canvas.setFillColor(colors.HexColor("#f8faf7"))
        pdf_canvas.setStrokeColor(colors.HexColor("#d1d5db"))
        pdf_canvas.roundRect(2 * cm, box_y, width - 4 * cm, box_height, 6, fill=1, stroke=1)
        pdf_canvas.setFillColor(colors.HexColor("#184d47"))
        pdf_canvas.setFont("Helvetica-Bold", 8.8)
        pdf_canvas.drawString(2.35 * cm, box_y + 1.26 * cm, "Jenis Surat")
        pdf_canvas.drawString(8.8 * cm, box_y + 1.26 * cm, "Keperluan")
        pdf_canvas.setFillColor(colors.black)
        pdf_canvas.setFont("Helvetica", 9)
        pdf_canvas.drawString(2.35 * cm, box_y + 0.72 * cm, jenis or "-")
        pdf_canvas.drawString(8.8 * cm, box_y + 0.72 * cm, keperluan or "-")
        return box_y - 0.85 * cm

    @staticmethod
    def _draw_signature_block(pdf_canvas: canvas.Canvas, width: float, y: float, signature_path: Optional[str]) -> None:
        block_width = 7.2 * cm
        block_height = 4.3 * cm
        block_x = width - 2.15 * cm - block_width
        block_y = max(2.0 * cm, y - block_height)
        pdf_canvas.setFillColor(colors.white)
        pdf_canvas.setStrokeColor(colors.HexColor("#d1d5db"))
        pdf_canvas.roundRect(block_x, block_y, block_width, block_height, 6, fill=1, stroke=1)
        pdf_canvas.setFillColor(colors.HexColor("#184d47"))
        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.drawCentredString(block_x + block_width / 2, block_y + block_height - 0.55 * cm, "Tanda Tangan Mahasiswa")
        if signature_path:
            try:
                from app.utils.storage import storage_service
                from reportlab.lib.utils import ImageReader
                sig_bytes = storage_service.get_file_content(signature_path)
                img = ImageReader(BytesIO(sig_bytes))
                pdf_canvas.drawImage(
                    img,
                    block_x + 0.8 * cm,
                    block_y + 0.55 * cm,
                    width=5.55 * cm,
                    height=2.4 * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception as e:
                logger.error(f"Failed to load signature from storage: {e}")
                pdf_canvas.setFillColor(colors.HexColor("#9ca3af"))
                pdf_canvas.setFont("Helvetica-Oblique", 9)
                pdf_canvas.drawCentredString(block_x + block_width / 2, block_y + 1.65 * cm, "Belum ada tanda tangan")
        else:
            pdf_canvas.setFillColor(colors.HexColor("#9ca3af"))
            pdf_canvas.setFont("Helvetica-Oblique", 9)
            pdf_canvas.drawCentredString(block_x + block_width / 2, block_y + 1.65 * cm, "Belum ada tanda tangan")

    @staticmethod
    def _format_indonesian_date(date_value: datetime) -> str:
        months = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]
        return f"{date_value.day} {months[date_value.month - 1]} {date_value.year}"

    @staticmethod
    def _render_internal_body(pdf_canvas: canvas.Canvas, width: float, y: float, template_name: str, fields: Dict[str, str]) -> float:
        left = 2.15 * cm
        body_width = width - 4.3 * cm

        if template_name == "Surat Keterangan Aktif Kuliah":
            y = PDFGenerator._draw_paragraph(
                pdf_canvas,
                "Yang bertanda tangan di bawah ini menerangkan bahwa mahasiswa berikut masih aktif terdaftar sebagai mahasiswa pada institusi ini:",
                left,
                y,
                body_width,
            ) - 4

            table = Table(
                [["Nama", fields.get("nama", "-")], ["NIM", fields.get("nim", "-")], ["Keperluan", fields.get("keperluan_surat_aktif", "-")]],
                colWidths=[4.0 * cm, body_width - 4.0 * cm],
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d1d5db")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            _, table_height = table.wrap(body_width, y)
            table.drawOn(pdf_canvas, left, y - table_height)
            y -= table_height + 10
            y = PDFGenerator._draw_paragraph(
                pdf_canvas,
                "Surat ini diterbitkan sebagai bukti resmi bahwa nama tersebut di atas memenuhi status akademik yang masih aktif pada semester berjalan.",
                left,
                y,
                body_width,
            )
            return y

        if template_name == "Surat Pembatalan Mata Kuliah":
            pdf_canvas.setFont("Helvetica", 11)
            y = PDFGenerator._draw_paragraph(pdf_canvas, "Saya yang bertanda tangan di bawah ini :", left, y, body_width) - 10

            info_rows = [
                ("Nama", fields.get("nama", "-")),
                ("NIM", fields.get("nim", "-")),
                ("Program Studi", "Ilmu Komputer"),
            ]
            info_table = Table(
                [[label, ":", value] for label, value in info_rows],
                colWidths=[4.1 * cm, 0.45 * cm, body_width - 4.55 * cm],
                hAlign="LEFT",
            )
            info_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (2, 0), (2, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 11),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            _, info_height = info_table.wrap(body_width, y)
            info_table.drawOn(pdf_canvas, left, y - info_height)
            y -= info_height + 14

            y = PDFGenerator._draw_paragraph(pdf_canvas, "mengajukan pembatalan mata kuliah berikut :", left, y, body_width) - 10

            course_rows = [
                ("Nama Mata Kuliah", fields.get("nama_mata_kuliah", "-")),
                ("Kode Mata Kuliah", fields.get("kode_mata_kuliah", "-")),
                ("Semester", fields.get("semester", "-")),
                ("Tahun Akademik", fields.get("tahun_akademik", "-")),
            ]
            course_table = Table(
                [[label, ":", value] for label, value in course_rows],
                colWidths=[4.1 * cm, 0.45 * cm, body_width - 4.55 * cm],
                hAlign="LEFT",
            )
            course_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (2, 0), (2, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 11),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            _, course_height = course_table.wrap(body_width, y)
            course_table.drawOn(pdf_canvas, left, y - course_height)
            y -= course_height + 14

            y = PDFGenerator._draw_paragraph(pdf_canvas, "dengan alasan :", left, y, body_width) - 10
            y = PDFGenerator._draw_paragraph(pdf_canvas, fields.get("alasan_pembatalan_kuliah", "-"), left + 0.55 * cm, y, body_width - 0.55 * cm, leading=15, justify=True) - 12
            return y

        y = PDFGenerator._draw_paragraph(
            pdf_canvas,
            "Dokumen ini dibuat berdasarkan data yang diisikan pada formulir pengajuan surat.",
            left,
            y,
            body_width,
        ) - 4
        for key, value in fields.items():
            y = PDFGenerator._draw_paragraph(pdf_canvas, f"{PDFGenerator._format_label(key)}: {value}", left, y, body_width) - 2
        return y

    @staticmethod
    def generate_from_template(
        template_name: str,
        fields: Dict[str, str],
        filename: str,
        signature_path: Optional[str] = None,
    ) -> str:
        try:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4


            y = PDFGenerator._draw_header(pdf, width, height, template_name)
            
            # Start the body slightly higher since we removed the meta box
            y -= 1.0 * cm
            
            y = PDFGenerator._render_internal_body(pdf, width, y, template_name, fields)

            if template_name == "Surat Pembatalan Mata Kuliah":
                pdf.setFont("Helvetica", 10.8)

                left = 1.5 * cm
                col1_x = left
                pdf.drawString(col1_x, 7.3 * cm, "Mengetahui,")
                pdf.drawString(col1_x, 6.5 * cm, "Dosen Pembimbing,")
                pdf.drawString(col1_x, 3.7 * cm, fields.get("dosen_pembimbing", "-"))
                pdf.drawString(col1_x, 3.2 * cm, f"NIP. {fields.get('dosen_pembimbing_nip', '-')}")

                col2_x = 8.25 * cm
                pdf.drawString(col2_x, 7.3 * cm, "Menyetujui,")
                pdf.drawString(col2_x, 6.5 * cm, "Ketua Program Studi,")
                pdf.drawString(col2_x, 3.7 * cm, fields.get("ketua_program_studi_ilmu_komputer", "-"))
                pdf.drawString(col2_x, 3.2 * cm, f"NIP. {fields.get('ketua_program_studi_ilmu_komputer_nip', '-')}")

                col3_x = width - 6.0 * cm
                pdf.drawString(col3_x, 7.3 * cm, f"Bogor, {PDFGenerator._format_indonesian_date(datetime.now())}")
                pdf.drawString(col3_x, 6.5 * cm, "Pemohon,")
                pdf.drawString(col3_x, 3.7 * cm, fields.get("nama", "-"))
                pdf.drawString(col3_x, 3.2 * cm, f"NIM. {fields.get('nim', '-')}")
            else:
                PDFGenerator._draw_signature_block(pdf, width, y, signature_path)
            pdf.save()
            
            from app.utils.storage import storage_service
            s3_key = storage_service.upload_file(buffer.getvalue(), filename)
            return s3_key
        except Exception as exc:
            raise InternalError("Gagal menghasilkan PDF template") from exc

    @staticmethod
    def attach_signature(
        pdf_path: str,
        signature_image_path: str,
        output_path: str,
        x: float = 2,
        y: float = 5,
        width: float = 4,
        height: float = 2,
    ) -> str:
        try:
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            page_width, page_height = A4
            c.setFont("Helvetica", 10)
            c.drawString(2 * cm, page_height - 2 * cm, "[Signed Document]")
            if signature_image_path:
                try:
                    from app.utils.storage import storage_service
                    from reportlab.lib.utils import ImageReader
                    sig_bytes = storage_service.get_file_content(signature_image_path)
                    img = ImageReader(BytesIO(sig_bytes))
                    c.drawImage(
                        img,
                        x * cm,
                        y * cm,
                        width=width * cm,
                        height=height * cm,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                except Exception as e:
                    logger.error(f"Failed to attach signature: {e}")
            c.save()
            from app.utils.storage import storage_service
            s3_key = storage_service.upload_file(buffer.getvalue(), "attached_sig.pdf")
            return s3_key
        except Exception as exc:
            raise InternalError("Gagal menempelkan tanda tangan") from exc

    @staticmethod
    def overlay_signatures_on_pdf(
        pdf_path_or_bytes: Union[str, bytes],
        signatures: List,
        document_hash: Optional[str] = None,
    ) -> bytes:
        from pypdf import PdfReader, PdfWriter  # type: ignore
        from reportlab.pdfgen import canvas as rl_canvas
        
        if isinstance(pdf_path_or_bytes, bytes):
            reader = PdfReader(BytesIO(pdf_path_or_bytes))
        else:
            reader = PdfReader(pdf_path_or_bytes)
            
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        # Group signatures by page (0-indexed)
        sigs_by_page = {}
        if signatures:
            for sig in signatures:
                if sig.is_signed() and sig.image_path and sig.pos_x is not None and sig.pos_y is not None:
                    pg = (sig.page_number or 1) - 1
                    sigs_by_page.setdefault(pg, []).append(sig)

        # Overlay signed signatures onto each page if present
        for page_idx, page_sigs in sigs_by_page.items():
            if page_idx >= len(writer.pages):
                continue
            target_page = writer.pages[page_idx]
            page_width = float(target_page.mediabox.width)
            page_height = float(target_page.mediabox.height)

            overlay_buf = BytesIO()
            overlay = rl_canvas.Canvas(overlay_buf, pagesize=(page_width, page_height))

            for sig in page_sigs:
                if not sig.image_path:
                    continue
                
                # Convert from screen coordinates (top-left origin) to PDF coordinates (bottom-left origin)
                rendered_width = 700  # approximate rendered width in frontend wizard
                scale = page_width / rendered_width

                box_x = sig.pos_x * scale
                box_y = page_height - (sig.pos_y * scale) - (sig.pos_height * scale)
                box_w = sig.pos_width * scale
                box_h = sig.pos_height * scale

                pdf_w = box_w * 0.95
                pdf_h = box_h * 0.75
                pdf_x = box_x + (box_w - pdf_w) / 2
                pdf_y = box_y + (box_h - pdf_h) / 2

                try:
                    # 1. Background & Border
                    overlay.setFillColorRGB(1, 1, 1, 0.8)
                    overlay.rect(pdf_x, pdf_y, pdf_w, pdf_h, fill=1, stroke=0)
                    
                    overlay.setStrokeColorRGB(0.2, 0.2, 0.2)
                    overlay.setLineWidth(0.7)
                    overlay.rect(pdf_x, pdf_y, pdf_w, pdf_h, fill=0, stroke=1)

                    # 2. QR Code
                    sig_qr_filename = f"sig_qr_{sig.owner_id}.png"
                    try:
                        from app.utils.storage import storage_service
                        storage_service.get_file_content(sig_qr_filename)
                    except FileNotFoundError:
                        url = f"{settings.BASE_URL}/verify/{document_hash}" if document_hash else f"{settings.BASE_URL}/verify-sig/{sig.signature_hash}"
                        from app.utils.qr_generator import QRCodeGenerator
                        qr_path = QRCodeGenerator.generate_qr_code(url, sig_qr_filename)
                        with open(qr_path, "rb") as f:
                            storage_service.upload_file(f.read(), sig_qr_filename)
                        # Remove temp file
                        try:
                            os.remove(qr_path)
                        except:
                            pass

                    qr_padding = 4 * scale
                    qr_size = pdf_h - (qr_padding * 2)
                    qr_x = pdf_x + qr_padding
                    qr_y = pdf_y + qr_padding

                    try:
                        from app.utils.storage import storage_service
                        from reportlab.lib.utils import ImageReader
                        qr_bytes = storage_service.get_file_content(sig_qr_filename)
                        qr_img = ImageReader(BytesIO(qr_bytes))
                        overlay.drawImage(
                            qr_img, qr_x, qr_y,
                            width=qr_size, height=qr_size,
                            preserveAspectRatio=True, mask="auto"
                        )
                    except Exception as e:
                        logger.error(f"Failed to draw QR code from storage: {e}")

                    # 3. Text label
                    text_x = qr_x + qr_size + qr_padding
                    text_y = pdf_y + pdf_h - (8 * scale)

                    overlay.setFillColorRGB(0.2, 0.2, 0.2)
                    overlay.setFont("Helvetica", 3.8 * scale)
                    overlay.drawString(text_x, text_y, "Ditandatangani secara elektronik oleh:")

                    overlay.setFont("Helvetica-Bold", 4.2 * scale)
                    owner_name = (sig.owner_name or "Sistem Agridesk")[:25]
                    overlay.drawString(text_x, text_y - (5.5 * scale), owner_name)

                    # 4. Signature graphic
                    sig_img_h = pdf_h - (18 * scale)
                    sig_img_w = pdf_w - qr_size - (3 * qr_padding)
                    sig_img_y = pdf_y + (4 * scale)
                    try:
                        from app.utils.storage import storage_service
                        from reportlab.lib.utils import ImageReader
                        sig_bytes = storage_service.get_file_content(sig.image_path)
                        img = ImageReader(BytesIO(sig_bytes))
                        overlay.drawImage(
                            img,
                            text_x, sig_img_y,
                            width=sig_img_w, height=sig_img_h,
                            preserveAspectRatio=True, mask="auto"
                        )
                    except Exception as e:
                        logger.error(f"Failed to draw signature image from storage: {e}")

                    # 5. Domain branding
                    overlay.setFont("Helvetica", 3.5 * scale)
                    overlay.drawRightString(pdf_x + pdf_w - (4 * scale), pdf_y + (3 * scale), "drive.hq.idenx.id")
                except Exception as e:
                    logger.error(f"Failed to draw signature overlay for owner_id {sig.owner_id}: {e}", exc_info=True)

            overlay.save()
            overlay_buf.seek(0)
            overlay_pdf = PdfReader(overlay_buf)
            if overlay_pdf.pages:
                target_page.merge_page(overlay_pdf.pages[0])

        output_buf = BytesIO()
        writer.write(output_buf)
        return output_buf.getvalue()

    @staticmethod
    def generate_final_pdf(
        pdf_path: str,
        qr_path: Optional[str],
        output_filename: str,
        signatures: Optional[list] = None,
        is_external: bool = False,
        document_hash: Optional[str] = None,
    ) -> str:
        try:
            from app.utils.storage import storage_service
            
            try:
                source_pdf_bytes = storage_service.get_file_content(pdf_path)
            except FileNotFoundError:
                source_pdf_bytes = None

            if not source_pdf_bytes:
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                page_width, page_height = A4
                c.setFont("Helvetica", 10)
                c.drawString(2 * cm, page_height - 2 * cm, "[Final Approved Document]")
                if qr_path:
                    try:
                        from reportlab.lib.utils import ImageReader
                        qr_bytes = storage_service.get_file_content(qr_path)
                        qr_img = ImageReader(BytesIO(qr_bytes))
                        c.drawImage(
                            qr_img,
                            page_width - 6 * cm,
                            2 * cm,
                            width=4 * cm,
                            height=4 * cm,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                    except Exception as e:
                        logger.error(f"Failed to draw QR code: {e}")
                c.save()
                return storage_service.upload_file(buffer.getvalue(), output_filename)

            # Call our newly extracted method to overlay the signatures
            overlaid_pdf_bytes = PDFGenerator.overlay_signatures_on_pdf(
                pdf_path_or_bytes=source_pdf_bytes,
                signatures=signatures,
                document_hash=document_hash
            )
            
            # Read back using PdfReader so we can continue with the master QR overlay on the last page!
            from pypdf import PdfReader, PdfWriter  # type: ignore
            reader = PdfReader(BytesIO(overlaid_pdf_bytes))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            # Now overlay the document master QR & SHA256 Hash onto the last page as final approval seal
            last_page = writer.pages[-1]
            page_width = float(last_page.mediabox.width)
            page_height = float(last_page.mediabox.height)

            overlay_bytes = BytesIO()
            overlay = canvas.Canvas(overlay_bytes, pagesize=(page_width, page_height))

            footer_margin = 0.6 * cm
            qr_size = 2.2 * cm

            if qr_path:
                qr_x = page_width - footer_margin - qr_size
                qr_y = footer_margin
                try:
                    from reportlab.lib.utils import ImageReader
                    qr_bytes = storage_service.get_file_content(qr_path)
                    qr_img = ImageReader(BytesIO(qr_bytes))
                    overlay.drawImage(
                        qr_img,
                        qr_x,
                        qr_y,
                        width=qr_size,
                        height=qr_size,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                except Exception as e:
                    logger.error(f"Failed to draw master QR: {e}")

            if document_hash:
                overlay.setFillColor(colors.HexColor("#6b7280"))
                overlay.setFont("Helvetica", 5)
                hash_text = f"SHA256: {document_hash[:32]}..."
                text_x = page_width - footer_margin - qr_size - 0.1 * cm
                overlay.drawRightString(text_x, footer_margin + 0.15 * cm, hash_text)

            overlay.save()
            overlay_bytes.seek(0)

            overlay_pdf = PdfReader(overlay_bytes)
            last_page.merge_page(overlay_pdf.pages[0])

            output_pdf_buffer = BytesIO()
            writer.write(output_pdf_buffer)

            return storage_service.upload_file(output_pdf_buffer.getvalue(), output_filename)
        except Exception as exc:
            raise InternalError("Gagal menghasilkan PDF final") from exc
