"""
config.py — Bot configuration (Clean Pune)
"""

import os

# ─────────────────────────────────────────────
# REQUIRED: Fill in before running
# ─────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8739488313:AAEWwFI0SrI074v2HmcKxD5zSFVRGzU8cQQ")

# ─────────────────────────────────────────────
# ALLOWED USERS — both IDs hardcoded
# ─────────────────────────────────────────────
ALLOWED_USERS = {
    6536685508,   # original owner
    776065946,    # second user
}

# ─────────────────────────────────────────────
# BUSINESS DETAILS  (extracted from invoice)
# ─────────────────────────────────────────────
BUSINESS_NAME       = "CLEAN PUNE"
BUSINESS_TAGLINE    = "PREMIUM CLEANING SOLUTIONS"
BUSINESS_ADDRESS    = "Mont Vert Road Troprz, Near Kaspate Wasti,\nWakad, Pimpri Chinchwad, Pune - 411057"
BUSINESS_PHONE      = "+91 9325160053"
BUSINESS_EMAIL      = ""
BUSINESS_WEBSITE    = "www.cleanpune.com"

CURRENCY_SYMBOL     = "₹"

# ─────────────────────────────────────────────
# BRAND COLORS  (matched from the invoice PDF)
# ─────────────────────────────────────────────
HEADER_COLOR_LEFT   = "#1B8EA6"
HEADER_COLOR_RIGHT  = "#0D5C75"
TABLE_HEADER_COLOR  = "#1C2D4A"
ACCENT_COLOR        = "#1B8EA6"
TOTAL_PILL_COLOR    = "#1B8EA6"
CARD_BG             = "#F0F4F8"
ROW_STRIPE          = "#F7FAFB"

# ─────────────────────────────────────────────
# LOGO
# ─────────────────────────────────────────────
LOGO_PATH = None

# ─────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────
OUTPUT_DIR    = "invoices"
COUNTER_FILE  = "invoice_counter.json"
