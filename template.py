"""
template.py — Clean Pune brand template
Faithfully reproduces the layout from the sample invoice:
  • Teal gradient header with big bold "CLEAN PUNE" left, "INVOICE" right
  • Rounded card for customer address
  • Dark navy table header with teal SR.NO column
  • Subtotal row + teal "Total Due" pill
  • Thank-you footer card with teal text
"""

from reportlab.lib import colors
from reportlab.lib.units import mm

from config import (
    HEADER_COLOR_LEFT, HEADER_COLOR_RIGHT,
    TABLE_HEADER_COLOR, ACCENT_COLOR,
    TOTAL_PILL_COLOR, CARD_BG, ROW_STRIPE,
    BUSINESS_NAME, BUSINESS_TAGLINE,
    BUSINESS_ADDRESS, BUSINESS_PHONE,
    BUSINESS_EMAIL, BUSINESS_WEBSITE,
    CURRENCY_SYMBOL, LOGO_PATH,
)


def _hex(h: str) -> colors.Color:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.Color(r/255, g/255, b/255)


class BrandTemplate:
    # ── colours ──────────────────────────────────────────────────
    header_left    = _hex(HEADER_COLOR_LEFT)
    header_right   = _hex(HEADER_COLOR_RIGHT)
    tbl_header     = _hex(TABLE_HEADER_COLOR)
    accent         = _hex(ACCENT_COLOR)
    total_pill     = _hex(TOTAL_PILL_COLOR)
    card_bg        = _hex(CARD_BG)
    row_stripe     = _hex(ROW_STRIPE)
    white          = colors.white
    black          = colors.black
    dark_text      = colors.Color(0.15, 0.15, 0.15)
    mid_grey       = colors.Color(0.50, 0.50, 0.50)
    light_line     = colors.Color(0.85, 0.88, 0.90)

    # ── page (A4) ─────────────────────────────────────────────────
    page_w   = 210 * mm
    page_h   = 297 * mm
    margin   = 14 * mm          # uniform margin

    # ── header band ──────────────────────────────────────────────
    header_h       = 44 * mm
    header_radius  = 8           # rounded corners (points)

    # ── card corner radius ────────────────────────────────────────
    card_radius    = 6

    # ── typography (pt) ──────────────────────────────────────────
    font_brand     = 28          # "CLEAN PUNE"
    font_tagline   = 8
    font_invoice   = 30          # "INVOICE" top-right
    font_meta      = 9           # invoice no / date labels
    font_section   = 8          # "CUSTOMER ADDRESS"
    font_cust_name = 13          # bold customer name
    font_body      = 9
    font_small     = 7.5

    # ── business ─────────────────────────────────────────────────
    biz_name     = BUSINESS_NAME
    biz_tagline  = BUSINESS_TAGLINE
    biz_address  = BUSINESS_ADDRESS
    biz_phone    = BUSINESS_PHONE
    biz_email    = BUSINESS_EMAIL
    biz_website  = BUSINESS_WEBSITE
    currency     = CURRENCY_SYMBOL
    logo_path    = LOGO_PATH


TEMPLATE = BrandTemplate()
