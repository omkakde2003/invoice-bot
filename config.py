"""
config.py — Bot configuration (Clean Pune)
"""

import os

# ─────────────────────────────────────────────
# REQUIRED: Fill in before running
# ─────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ─────────────────────────────────────────────
# ALLOWED USERS — add Telegram IDs here
# ─────────────────────────────────────────────
ALLOWED_USERS = {
    int(os.getenv("OWNER_ID", "6353328701")),  # original owner
    776065946,                                    # second user
    # add more IDs here when needed:
    # 111111111,
}

# ─────────────────────────────────────────────
# BUSINESS DETAILS  (extracted from invoice)
# ─────────────────────────────────────────────
BUSINESS_NAME       = "CLEAN PUNE"
BUSINESS_TAGLINE    = "PREMIUM CLEANING SOLUTIONS"
BUSINESS_ADDRESS    = "Mont Vert Road Troprz, Near Kaspate Wasti,\nWakad, Pimpri Chinchwad, Pune - 411057"
BUSINESS_PHONE      = "+91 9325160053"
BUSINESS_EMAIL      = ""                  # add if needed
BUSINESS_WEBSITE    = "www.cleanpune.com"

CURRENCY_SYMBOL     = "₹"

# ─────────────────────────────────────────────
# BRAND COLORS  (matched from the invoice PDF)
# ─────────────────────────────────────────────
# Header gradient colours (teal → dark teal)
HEADER_COLOR_LEFT   = "#1B8EA6"   # bright teal
HEADER_COLOR_RIGHT  = "#0D5C75"   # dark teal

# Table header — dark navy
TABLE_HEADER_COLOR  = "#1C2D4A"

# Accent — teal (used for "CUSTOMER ADDRESS" label, sr.no column, total pill)
ACCENT_COLOR        = "#1B8EA6"

# Total Due pill background
TOTAL_PILL_COLOR    = "#1B8EA6"

# Light background for customer / footer card
CARD_BG             = "#F0F4F8"

# Alternating row stripe
ROW_STRIPE          = "#F7FAFB"

# ─────────────────────────────────────────────
# LOGO
# ─────────────────────────────────────────────
LOGO_PATH = None   # e.g. "assets/cleanpune_logo.png"

# ─────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────
OUTPUT_DIR    = "invoices"
COUNTER_FILE  = "invoice_counter.json"
