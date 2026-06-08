"""
invoice_generator.py — Clean Pune PDF invoice
Returns PDF as bytes in memory (no disk write needed).
"""

import io, json, os
from datetime import date
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from config import COUNTER_FILE
from template import TEMPLATE as T

# ── pre-compute constants once ────────────────────────────────────────────────
_PAGE_W = 210 * mm
_PAGE_H = 297 * mm
_MARGIN = 14  * mm
_HDR_H  = 44  * mm
_CW     = _PAGE_W - 2 * _MARGIN


# ── counter ───────────────────────────────────────────────────────────────────

def _load_counter() -> int:
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            return json.load(f).get("counter", 1324)
    return 1324

def _save_counter(n: int):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"counter": n}, f)

def next_invoice_number() -> str:
    n = _load_counter() + 1
    _save_counter(n)
    return f"#{n}"


# ── drawing helpers ───────────────────────────────────────────────────────────

def _rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None, lw=0):
    c.saveState()
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(lw)
    else:
        c.setStrokeColor(fill_color)
        c.setLineWidth(0)
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.drawPath(p, fill=1, stroke=1 if stroke_color else 0)
    c.restoreState()


def _gradient_rect(c, x, y, w, h, r, col_left, col_right):
    steps = 8
    rl, gl, bl = col_left.red,  col_left.green,  col_left.blue
    rr, gr, br = col_right.red, col_right.green, col_right.blue
    sw = w / steps
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.clipPath(p, stroke=0)
    for i in range(steps):
        t = i / (steps - 1)
        c.setFillColor(colors.Color(
            rl + t*(rr-rl), gl + t*(gr-gl), bl + t*(br-bl)
        ))
        c.rect(x + i*sw, y, sw + 1, h, fill=1, stroke=0)
    c.restoreState()


def _font(c, bold, size):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

def _right(c, x, y, text):
    c.drawString(x - c.stringWidth(text, c._fontname, c._fontsize), y, text)

def _center(c, cx, y, text):
    c.drawString(cx - c.stringWidth(text, c._fontname, c._fontsize)/2, y, text)


# ── main — returns (pdf_bytes, filename) ─────────────────────────────────────

def generate_invoice(customer_name, customer_address, services,
                     invoice_number=None):
    """
    Returns (bytes, filename) — PDF is built in memory, never written to disk.
    """
    if invoice_number is None:
        invoice_number = next_invoice_number()

    today = date.today()
    safe  = "".join(ch for ch in customer_name if ch.isalnum() or ch in " _-").strip().replace(" ", "_")
    filename = f"invoice_{safe}_{today.isoformat()}.pdf"

    # ── build into a BytesIO buffer ───────────────────────────────────────
    buf = io.BytesIO()
    pw, ph = _PAGE_W, _PAGE_H
    m,  cw = _MARGIN, _CW

    c = rl_canvas.Canvas(buf, pagesize=(pw, ph))

    # ── HEADER ────────────────────────────────────────────────────────────
    hh  = _HDR_H
    hy  = ph - m - hh
    pad = 7 * mm

    _gradient_rect(c, m, hy, cw, hh, T.header_radius, T.header_left, T.header_right)

    c.setFillColor(T.white)
    _font(c, True, T.font_brand)
    c.drawString(m + pad, hy + hh - pad - T.font_brand * 0.75, T.biz_name)

    _font(c, False, T.font_tagline)
    c.setFillColor(colors.Color(1, 1, 1, 0.85))
    tag_y  = hy + hh - pad - T.font_brand * 0.75 - 6*mm
    cx_pos = m + pad
    for ch in T.biz_tagline:
        c.drawString(cx_pos, tag_y, ch)
        cx_pos += c.stringWidth(ch, "Helvetica", T.font_tagline) + 1.4

    c.setFillColor(colors.Color(1, 1, 1, 0.80))
    _font(c, False, 7.5)
    ay = tag_y - 5*mm
    for line in T.biz_address.split("\n"):
        c.drawString(m + pad + 3, ay, line)
        ay -= 4*mm
    c.drawString(m + pad + 3, ay, T.biz_phone)

    c.setFillColor(colors.Color(1, 1, 1, 0.30))
    _font(c, True, T.font_invoice)
    inv_label = "INVOICE"
    iw = c.stringWidth(inv_label, "Helvetica-Bold", T.font_invoice)
    c.drawString(m + cw - pad - iw, hy + hh - pad - T.font_invoice * 0.75, inv_label)

    pill_w, pill_h = 52*mm, 18*mm
    pill_x = m + cw - pad - pill_w
    pill_y = hy + pad
    _rounded_rect(c, pill_x, pill_y, pill_w, pill_h, 5, T.white)

    c.setFillColor(T.dark_text)
    _font(c, True, 7.5)
    c.drawString(pill_x + 4*mm, pill_y + pill_h - 6*mm, "Invoice No :")
    c.setFillColor(T.accent)
    c.drawString(pill_x + 24*mm, pill_y + pill_h - 6*mm, invoice_number)
    c.setFillColor(T.dark_text)
    _font(c, False, 7.5)
    c.drawString(pill_x + 4*mm,  pill_y + 3.5*mm, "Date          :")
    c.drawString(pill_x + 24*mm, pill_y + 3.5*mm, today.strftime("%b %d, %Y"))

    y = hy - 8*mm

    # ── CUSTOMER CARD ─────────────────────────────────────────────────────
    addr_lines = [l.strip() for l in customer_address.split(",") if l.strip()]
    card_h = (3 + len(addr_lines)) * 5.5*mm + 10*mm
    card_y = y - card_h

    _rounded_rect(c, m, card_y, cw, card_h, T.card_radius, T.card_bg,
                  stroke_color=T.light_line, lw=0.5)

    c.setFillColor(T.accent)
    _font(c, True, T.font_section)
    c.drawString(m + 5*mm, card_y + card_h - 7*mm,
                 "C U S T O M E R   A D D R E S S")

    c.setFillColor(T.dark_text)
    _font(c, True, T.font_cust_name)
    c.drawString(m + 5*mm, card_y + card_h - 14*mm, customer_name)

    _font(c, False, T.font_body)
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    ly = card_y + card_h - 20*mm
    for line in addr_lines:
        c.drawString(m + 5*mm, ly, line)
        ly -= 5*mm

    y = card_y - 8*mm

    # ── SERVICES TABLE ────────────────────────────────────────────────────
    col_sr   = 14*mm
    col_desc = cw - 14*mm - 34*mm - 34*mm
    col_rate = 34*mm
    col_amt  = 34*mm

    data = [["SR.\nNO.", "SERVICE DESCRIPTION", "RATE (INR )", "AMOUNT (INR )"]]
    for idx, svc in enumerate(services, 1):
        p = float(svc["price"])
        data.append([f"{idx:02d}", svc["name"], f"{p:,.2f}", f"{p:,.2f}"])

    subtotal = sum(float(s["price"]) for s in services)
    n = len(services)

    style = [
        ("BACKGROUND",    (0,0),(-1,0),  T.tbl_header),
        ("BACKGROUND",    (0,0),(0,0),   T.accent),
        ("TEXTCOLOR",     (0,0),(-1,0),  T.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  7.5),
        ("BOTTOMPADDING", (0,0),(-1,0),  5),
        ("TOPPADDING",    (0,0),(-1,0),  5),
        ("ALIGN",         (0,0),(0,0),   "CENTER"),
        ("ALIGN",         (2,0),(-1,0),  "CENTER"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1),(-1,-1), T.font_body),
        ("TOPPADDING",    (0,1),(-1,-1), 6),
        ("BOTTOMPADDING", (0,1),(-1,-1), 6),
        ("ALIGN",         (0,1),(0,-1),  "CENTER"),
        ("ALIGN",         (2,1),(-1,-1), "RIGHT"),
        ("TEXTCOLOR",     (0,1),(0,-1),  T.accent),
        ("FONTNAME",      (0,1),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",      (3,1),(3,-1),  "Helvetica-Bold"),
        ("LINEBELOW",     (0,0),(-1,0),  0.5, T.light_line),
        ("LINEBEFORE",    (1,0),(1,-1),  0.5, T.light_line),
        *[("BACKGROUND",  (0,r),(-1,r),  T.row_stripe) for r in range(2, n+1, 2)],
        *[("LINEBELOW",   (0,r),(-1,r),  0.3, T.light_line) for r in range(1, n+1)],
    ]

    tbl = Table(data, colWidths=[col_sr, col_desc, col_rate, col_amt], repeatRows=1)
    tbl.setStyle(TableStyle(style))
    _, th = tbl.wrapOn(c, cw, ph)
    tbl_y = y - th
    tbl.drawOn(c, m, tbl_y)
    y = tbl_y - 6*mm

    # ── TOTALS ────────────────────────────────────────────────────────────
    rx = m + cw
    _font(c, False, T.font_body)
    c.setFillColor(T.mid_grey)
    c.drawString(rx - 60*mm, y, "Subtotal:")
    _font(c, True, T.font_body)
    c.setFillColor(T.dark_text)
    _right(c, rx, y, f"{subtotal:,.2f}")

    y -= 7*mm
    pw2, ph2 = 58*mm, 11*mm
    px2 = rx - pw2
    py2 = y - ph2
    lpw = 28*mm

    _rounded_rect(c, px2,       py2, lpw,     ph2, 4, T.tbl_header)
    _rounded_rect(c, px2 + lpw, py2, pw2-lpw, ph2, 4, T.total_pill)

    c.setFillColor(T.white)
    _font(c, True, 8.5)
    _center(c, px2 + lpw/2,             py2 + 3.5*mm, "Total Due:")
    _font(c, True, 9)
    _center(c, px2 + lpw + (pw2-lpw)/2, py2 + 3.5*mm, f"{T.currency}{subtotal:,.2f}")

    # ── FOOTER CARD ───────────────────────────────────────────────────────
    fh = 16*mm
    fy = m
    _rounded_rect(c, m, fy, cw, fh, T.card_radius, T.card_bg,
                  stroke_color=T.light_line, lw=0.4)
    c.setFillColor(T.accent)
    _font(c, True, 9)
    _center(c, m + cw/2, fy + fh - 7*mm, "THANK YOU FOR YOUR BUSINESS!")
    _font(c, False, 8)
    _center(c, m + cw/2, fy + 3.5*mm, T.biz_website)

    c.save()

    # return raw bytes + filename
    buf.seek(0)
    return buf.read(), filename
