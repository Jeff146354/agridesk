import os
from datetime import datetime
from io import BytesIO
from textwrap import wrap
from typing import Dict, Optional

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
    ) -> float:
        pdf_canvas.setFont(font_name, font_size)
        current_y = y
        for line in PDFGenerator._wrapped_lines(text, font_size, max_width):
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
        if signature_path and os.path.exists(signature_path):
            pdf_canvas.drawImage(
                signature_path,
                block_x + 0.8 * cm,
                block_y + 0.55 * cm,
                width=5.55 * cm,
                height=2.4 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
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
                ("NRP", fields.get("nim", "-")),
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
            y = PDFGenerator._draw_paragraph(pdf_canvas, fields.get("alasan_pembatalan_kuliah", "-"), left + 0.55 * cm, y, body_width - 0.55 * cm, leading=15) - 12

            lecturer_rows = [
                ("Dosen Pembimbing", fields.get("dosen_pembimbing", "-")),
                ("Ketua Program Studi Ilmu Komputer", fields.get("ketua_program_studi_ilmu_komputer", "-")),
            ]
            lecturer_table = Table(
                [[label, ":", value] for label, value in lecturer_rows],
                colWidths=[6.6 * cm, 0.45 * cm, body_width - 7.05 * cm],
                hAlign="LEFT",
            )
            lecturer_table.setStyle(
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
            _, lecturer_height = lecturer_table.wrap(body_width, y)
            lecturer_table.drawOn(pdf_canvas, left, y - lecturer_height)
            y -= lecturer_height + 8
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
            pdf_dir = os.path.join(settings.UPLOAD_DIR, "pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            filepath = os.path.join(pdf_dir, filename)

            pdf = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4

            if template_name == "Surat Pembatalan Mata Kuliah":
                left = 2.1 * cm
                body_width = width - 4.2 * cm

                pdf.setFillColor(colors.black)
                pdf.setFont("Helvetica-Bold", 13.5)
                pdf.drawCentredString(width / 2, height - 2.0 * cm, "FORMULIR PEMBATALAN MATA KULIAH")

                y = height - 3.5 * cm
                y = PDFGenerator._draw_paragraph(pdf, "Saya yang bertanda tangan di bawah ini :", left, y, body_width) - 6

                info_table = Table(
                    [
                        ["Nama", ":", fields.get("nama", "-")],
                        ["NRP", ":", fields.get("nim", "-")],
                        ["Program Studi", ":", "Ilmu Komputer"],
                    ],
                    colWidths=[4.4 * cm, 0.45 * cm, body_width - 4.85 * cm],
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
                info_table.drawOn(pdf, left, y - info_height)
                y -= info_height + 12

                y = PDFGenerator._draw_paragraph(pdf, "mengajukan pembatalan mata kuliah berikut :", left, y, body_width) - 8

                course_table = Table(
                    [
                        ["Nama Mata Kuliah", ":", fields.get("nama_mata_kuliah", "-")],
                        ["Kode Mata Kuliah", ":", fields.get("kode_mata_kuliah", "-")],
                        ["Semester", ":", fields.get("semester", "-")],
                        ["Tahun Akademik", ":", fields.get("tahun_akademik", "-")],
                    ],
                    colWidths=[4.4 * cm, 0.45 * cm, body_width - 4.85 * cm],
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
                course_table.drawOn(pdf, left, y - course_height)
                y -= course_height + 12

                y = PDFGenerator._draw_paragraph(pdf, "dengan alasan :", left, y, body_width) - 8
                y = PDFGenerator._draw_paragraph(
                    pdf,
                    fields.get("alasan_pembatalan_kuliah", "-"),
                    left + 0.55 * cm,
                    y,
                    body_width - 0.55 * cm,
                    leading=15,
                ) - 10

                lecturer_table = Table(
                    [
                        ["Dosen Pembimbing", ":", fields.get("dosen_pembimbing", "-")],
                        ["Ketua Program Studi Ilmu Komputer", ":", fields.get("ketua_program_studi_ilmu_komputer", "-")],
                    ],
                    colWidths=[6.7 * cm, 0.45 * cm, body_width - 7.15 * cm],
                    hAlign="LEFT",
                )
                lecturer_table.setStyle(
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
                _, lecturer_height = lecturer_table.wrap(body_width, y)
                lecturer_table.drawOn(pdf, left, y - lecturer_height)

                signature_x = width - 6.7 * cm
                pdf.setFont("Helvetica", 10.8)
                pdf.drawString(signature_x, 4.7 * cm, f"Bogor, {PDFGenerator._format_indonesian_date(datetime.now())}")
                pdf.drawString(signature_x, 3.9 * cm, "Tertanda,")
                pdf.drawString(signature_x, 2.05 * cm, fields.get("nama", "-"))
                pdf.drawString(signature_x, 1.6 * cm, f"NRP. {fields.get('nim', '-')}")

                pdf.save()
                return filepath

            y = PDFGenerator._draw_header(pdf, width, height, template_name)

            keperluan = fields.get("keperluan_surat_aktif") or fields.get("alasan_pembatalan_kuliah") or fields.get("keperluan") or "-"
            y = PDFGenerator._draw_meta_box(pdf, width, y, template_name, keperluan)
            y = PDFGenerator._render_internal_body(pdf, width, y, template_name, fields)

            pdf.setFillColor(colors.HexColor("#6b7280"))
            pdf.setFont("Helvetica", 8.5)
            pdf.drawString(2.15 * cm, 1.85 * cm, f"Dicetak pada {PDFGenerator._format_indonesian_date(datetime.now())}")

            if template_name == "Surat Pembatalan Mata Kuliah":
                right_x = width - 6.4 * cm
                pdf.setFont("Helvetica", 11)
                pdf.drawString(right_x, 5.4 * cm, f"Bogor, {PDFGenerator._format_indonesian_date(datetime.now())}")
                pdf.drawString(right_x, 4.5 * cm, "Tertanda,")
                pdf.drawString(right_x, 2.35 * cm, fields.get("nama", "-"))
                pdf.drawString(right_x, 1.9 * cm, f"NRP. {fields.get('nim', '-')}")

            PDFGenerator._draw_signature_block(pdf, width, y, signature_path)
            pdf.save()
            return filepath
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
            c = canvas.Canvas(output_path, pagesize=A4)
            page_width, page_height = A4
            c.setFont("Helvetica", 10)
            c.drawString(2 * cm, page_height - 2 * cm, "[Signed Document]")
            if os.path.exists(signature_image_path):
                c.drawImage(
                    signature_image_path,
                    x * cm,
                    y * cm,
                    width=width * cm,
                    height=height * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            c.save()
            return output_path
        except Exception as exc:
            raise InternalError("Gagal menempelkan tanda tangan") from exc

    @staticmethod
    def generate_final_pdf(
        pdf_path: str,
        qr_path: Optional[str],
        output_filename: str,
        signature_paths: Optional[list[str]] = None,
    ) -> str:
        try:
            pdf_dir = os.path.join(settings.UPLOAD_DIR, "pdfs", "final")
            os.makedirs(pdf_dir, exist_ok=True)
            output_path = os.path.join(pdf_dir, output_filename)

            if not pdf_path or not os.path.exists(pdf_path):
                c = canvas.Canvas(output_path, pagesize=A4)
                page_width, page_height = A4
                c.setFont("Helvetica", 10)
                c.drawString(2 * cm, page_height - 2 * cm, "[Final Approved Document]")
                if qr_path and os.path.exists(qr_path):
                    c.drawImage(
                        qr_path,
                        page_width - 6 * cm,
                        2 * cm,
                        width=4 * cm,
                        height=4 * cm,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                c.save()
                return output_path

            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            last_page = writer.pages[-1]
            page_width = float(last_page.mediabox.width)
            page_height = float(last_page.mediabox.height)

            overlay_bytes = BytesIO()
            overlay = canvas.Canvas(overlay_bytes, pagesize=(page_width, page_height))

            if qr_path and os.path.exists(qr_path):
                overlay.drawImage(
                    qr_path,
                    page_width - 6 * cm,
                    2 * cm,
                    width=4 * cm,
                    height=4 * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )

            valid_signature_paths = [p for p in (signature_paths or []) if p and os.path.exists(p)]
            sig_x = 2 * cm
            sig_y = 2 * cm
            for idx, sig_path in enumerate(valid_signature_paths):
                if idx > 0:
                    sig_x += 4.8 * cm
                if sig_x + (4 * cm) > page_width - 7 * cm:
                    break
                overlay.drawImage(
                    sig_path,
                    sig_x,
                    sig_y,
                    width=4 * cm,
                    height=2 * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )

            overlay.save()
            overlay_bytes.seek(0)

            overlay_pdf = PdfReader(overlay_bytes)
            last_page.merge_page(overlay_pdf.pages[0])

            with open(output_path, "wb") as f:
                writer.write(f)

            return output_path
        except Exception as exc:
            raise InternalError("Gagal menghasilkan PDF final") from exc
