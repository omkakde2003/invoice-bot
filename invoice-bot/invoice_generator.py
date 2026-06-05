"""
invoice_generator.py — Clean Pune PDF invoice
Reproduces the exact layout from the sample:
  1. Rounded teal gradient header  (CLEAN PUNE left | INVOICE right)
  2. Invoice No + Date pill (white rounded box, top-right of header)
  3. CUSTOMER ADDRESS card (light grey, rounded)
  4. Services table  (dark navy header, teal SR.NO, alternating rows)
  5. Subtotal + Total Due pill
  6. THANK YOU footer card
"""

import os, json
from datetime import date, timedelta
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from config import OUTPUT_DIR, COUNTER_FILE
from template import TEMPLATE as T


# ── counter ──────────────────────────────────────────────────────────────────

def _load_counter() -> int:
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            return json.load(f).get("counter", 1324)   # starts after #1325
    return 1324

def _save_counter(n: int):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"counter": n}, f)

def next_invoice_number() -> str:
    n = _load_counter() + 1
    _save_counter(n)
    return f"#{n}"


# ── drawing primitives ────────────────────────────────────────────────────────

def _rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None, lw=0):
    """Draw a filled rounded rectangle."""
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
    """Simulate a left→right gradient with thin vertical slices."""
    steps = 60
    rl = col_left.red;  gl = col_left.green;  bl = col_left.blue
    rr = col_right.red; gr = col_right.green; br = col_right.blue
    slice_w = w / steps
    c.saveState()
    # clip to rounded rect
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    c.clipPath(p, stroke=0)
    for i in range(steps):
        t = i / (steps - 1)
        rc = rl + t * (rr - rl)
        gc = gl + t * (gr - gl)
        bc = bl + t * (br - bl)
        c.setFillColor(colors.Color(rc, gc, bc))
        c.rect(x + i * slice_w, y, slice_w + 0.5, h, fill=1, stroke=0)
    c.restoreState()


def _font(c, bold: bool, size: float):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

def _right(c, x, y, text):
    w = c.stringWidth(text, c._fontname, c._fontsize)
    c.drawString(x - w, y, text)

def _center(c, cx, y, text):
    w = c.stringWidth(text, c._fontname, c._fontsize)
    c.drawString(cx - w/2, y, text)


# ── main generator ────────────────────────────────────────────────────────────

def generate_invoice(customer_name, customer_address, services,
                     invoice_number=None) -> str:

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if invoice_number is None:
        invoice_number = next_invoice_number()

    today = date.today()
    safe  = "".join(ch for ch in customer_name if ch.isalnum() or ch in " _-").strip().replace(" ", "_")
    fpath = os.path.join(OUTPUT_DIR, f"invoice_{safe}_{today.isoformat()}.pdf")

    pw, ph = T.page_w, T.page_h
    m      = T.margin
    cw     = pw - 2*m           # content width

    c = rl_canvas.Canvas(fpath, pagesize=(pw, ph))

    # ── 1. HEADER GRADIENT BAND ───────────────────────────────────────────
    hh = T.header_h
    hy = ph - m - hh            # top-left y of header rect

    _gradient_rect(c, m, hy, cw, hh, T.header_radius, T.header_left, T.header_right)

    pad = 7 * mm                # inner padding inside header

    # Brand name — left
    c.setFillColor(T.white)
    _font(c, True, T.font_brand)
    c.drawString(m + pad, hy + hh - pad - T.font_brand * 0.75, T.biz_name)

    # Tagline — left, below brand
    _font(c, False, T.font_tagline)
    c.setFillColor(colors.Color(1, 1, 1, 0.85))
    tag_y = hy + hh - pad - T.font_brand * 0.75 - 6 * mm
    # letter-spacing simulation: draw char by char
    spacing = 1.4
    cx_pos  = m + pad
    for ch in T.biz_tagline:
        c.drawString(cx_pos, tag_y, ch)
        cx_pos += c.stringWidth(ch, "Helvetica", T.font_tagline) + spacing

    # Address + phone — left, below tagline
    c.setFillColor(colors.Color(1, 1, 1, 0.80))
    _font(c, False, 7.5)
    addr_lines = T.biz_address.split("\n")
    ay = tag_y - 5 * mm
    # location pin unicode approximation
    for line in addr_lines:
        c.drawString(m + pad + 3, ay, line)
        ay -= 4 * mm
    c.drawString(m + pad + 3, ay, T.biz_phone)

    # "INVOICE" — right, large light text
    c.setFillColor(colors.Color(1, 1, 1, 0.30))
    _font(c, True, T.font_invoice)
    inv_label = "INVOICE"
    iw = c.stringWidth(inv_label, "Helvetica-Bold", T.font_invoice)
    inv_x = m + cw - pad - iw
    inv_y = hy + hh - pad - T.font_invoice * 0.75
    c.drawString(inv_x, inv_y, inv_label)

    # Invoice No + Date white pill (right side, lower half of header)
    pill_w = 52 * mm
    pill_h = 18 * mm
    pill_x = m + cw - pad - pill_w
    pill_y = hy + pad
    _rounded_rect(c, pill_x, pill_y, pill_w, pill_h, 5, T.white)

    c.setFillColor(T.dark_text)
    _font(c, True, 7.5)
    c.drawString(pill_x + 4*mm, pill_y + pill_h - 6*mm, "Invoice No :")
    _font(c, True, 7.5)
    c.setFillColor(T.accent)
    c.drawString(pill_x + 24*mm, pill_y + pill_h - 6*mm, invoice_number)

    c.setFillColor(T.dark_text)
    _font(c, False, 7.5)
    c.drawString(pill_x + 4*mm, pill_y + 3.5*mm, "Date          :")
    c.drawString(pill_x + 24*mm, pill_y + 3.5*mm, today.strftime("%b %d, %Y"))

    y_cursor = hy - 8 * mm     # move below header

    # ── 2. CUSTOMER ADDRESS CARD ──────────────────────────────────────────
    addr_lines_cust = [l.strip() for l in customer_address.split(",") if l.strip()]
    card_rows  = 3 + len(addr_lines_cust)   # label + bold name + lines
    card_h     = card_rows * 5.5 * mm + 10 * mm
    card_y     = y_cursor - card_h

    _rounded_rect(c, m, card_y, cw, card_h, T.card_radius, T.card_bg,
                  stroke_color=T.light_line, lw=0.5)

    # "CUSTOMER ADDRESS" teal label
    c.setFillColor(T.accent)
    _font(c, True, T.font_section)
    # spaced label
    label = "C U S T O M E R   A D D R E S S"
    c.drawString(m + 5*mm, card_y + card_h - 7*mm, label)

    # Customer name bold
    c.setFillColor(T.dark_text)
    _font(c, True, T.font_cust_name)
    c.drawString(m + 5*mm, card_y + card_h - 7*mm - 7*mm, customer_name)

    # Address lines
    _font(c, False, T.font_body)
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    ly = card_y + card_h - 7*mm - 7*mm - 6*mm
    for line in addr_lines_cust:
        c.drawString(m + 5*mm, ly, line)
        ly -= 5 * mm

    y_cursor = card_y - 8 * mm

    # ── 3. SERVICES TABLE ─────────────────────────────────────────────────
    col_w_sr   = 14 * mm
    col_w_desc = cw - 14*mm - 34*mm - 34*mm
    col_w_rate = 34 * mm
    col_w_amt  = 34 * mm
    col_widths = [col_w_sr, col_w_desc, col_w_rate, col_w_amt]

    header_row = ["SR.\nNO.", "SERVICE DESCRIPTION", "RATE (INR )", "AMOUNT (INR )"]
    data = [header_row]

    for idx, svc in enumerate(services, 1):
        price = float(svc["price"])
        data.append([
            f"{idx:02d}",
            svc["name"],
            f"{price:,.2f}",
            f"{price:,.2f}",
        ])

    subtotal = sum(float(s["price"]) for s in services)

    # Style commands
    n = len(services)
    style = [
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  T.tbl_header),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  T.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  7.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  5),
        ("TOPPADDING",    (0, 0), (-1, 0),  5),
        ("ALIGN",         (0, 0), (0, 0),   "CENTER"),
        ("ALIGN",         (2, 0), (-1, 0),  "CENTER"),

        # SR.NO header cell — teal
        ("BACKGROUND",    (0, 0), (0, 0),   T.accent),

        # Body rows
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), T.font_body),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ALIGN",         (0, 1), (0, -1),  "CENTER"),
        ("ALIGN",         (2, 1), (-1, -1), "RIGHT"),
        ("TEXTCOLOR",     (0, 1), (0, -1),  T.accent),     # SR nos in teal
        ("FONTNAME",      (0, 1), (0, -1),  "Helvetica-Bold"),

        # Alternating rows
        *[("BACKGROUND", (0, r), (-1, r), T.row_stripe)
          for r in range(2, n+1, 2)],

        # Amount column bold
        ("FONTNAME",      (3, 1), (3, -1),  "Helvetica-Bold"),

        # Outer grid (subtle)
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, T.light_line),
        *[("LINEBELOW",   (0, r), (-1, r),  0.3, T.light_line)
          for r in range(1, n+1)],

        # Left border accent on SR column
        ("LINEBEFORE",    (1, 0), (1, -1),  0.5, T.light_line),
    ]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style))
    tw, th = tbl.wrapOn(c, cw, ph)
    tbl_y  = y_cursor - th
    tbl.drawOn(c, m, tbl_y)
    y_cursor = tbl_y - 6 * mm

    # ── 4. SUBTOTAL + TOTAL DUE ───────────────────────────────────────────
    right_x = m + cw          # right edge

    # Subtotal line
    _font(c, False, T.font_body)
    c.setFillColor(T.mid_grey)
    sub_label = "Subtotal:"
    c.drawString(right_x - 60*mm, y_cursor, sub_label)
    _font(c, True, T.font_body)
    c.setFillColor(T.dark_text)
    sub_val = f"{subtotal:,.2f}"
    _right(c, right_x, y_cursor, sub_val)

    y_cursor -= 7 * mm

    # Total Due pill
    pill_w2 = 58 * mm
    pill_h2 = 11 * mm
    pill_x2 = right_x - pill_w2
    pill_y2 = y_cursor - pill_h2

    # Label pill (dark navy)
    label_pill_w = 28 * mm
    _rounded_rect(c, pill_x2, pill_y2, label_pill_w, pill_h2, 4, T.tbl_header)
    c.setFillColor(T.white)
    _font(c, True, 8.5)
    _center(c, pill_x2 + label_pill_w/2, pill_y2 + 3.5*mm, "Total Due:")

    # Value pill (teal)
    val_pill_w = pill_w2 - label_pill_w
    _rounded_rect(c, pill_x2 + label_pill_w, pill_y2, val_pill_w, pill_h2, 4, T.total_pill)
    c.setFillColor(T.white)
    _font(c, True, 9)
    total_str = f"{T.currency}{subtotal:,.2f}"
    _center(c, pill_x2 + label_pill_w + val_pill_w/2, pill_y2 + 3.5*mm, total_str)

    y_cursor = pill_y2 - 10 * mm

    # ── 5. THANK YOU FOOTER CARD ──────────────────────────────────────────
    footer_h = 16 * mm
    footer_y = m
    _rounded_rect(c, m, footer_y, cw, footer_h, T.card_radius, T.card_bg,
                  stroke_color=T.light_line, lw=0.4)

    c.setFillColor(T.accent)
    _font(c, True, 9)
    _center(c, m + cw/2, footer_y + footer_h - 7*mm, "THANK YOU FOR YOUR BUSINESS!")

    _font(c, False, 8)
    _center(c, m + cw/2, footer_y + 3.5*mm, T.biz_website)

    c.save()
    return fpath
