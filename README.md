# 📄 Telegram Invoice Bot

A private Telegram bot that generates branded PDF invoices through a guided conversation flow.

---

## Folder Structure

```
invoice-bot/
├── bot.py                ← Main bot logic & conversation flow
├── invoice_generator.py  ← PDF creation with ReportLab
├── template.py           ← Brand template (colors, layout, fonts)
├── services.py           ← Pre-loaded services list
├── config.py             ← Token, owner ID, business details
├── requirements.txt
└── README.md
```

---

## Quick Setup

### 1 — Create your bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
2. Copy the **bot token** you receive

### 2 — Find your Telegram user ID
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy the **Id** number it returns

### 3 — Configure `config.py`
Open `config.py` and fill in:

```python
BOT_TOKEN  = "7123456789:AAG..."   # from BotFather
OWNER_ID   = 123456789             # your numeric user ID

BUSINESS_NAME    = "Acme Studio"
BUSINESS_ADDRESS = "42 Design Lane, Cape Town, ZA"
BUSINESS_EMAIL   = "hello@acme.co"
BUSINESS_PHONE   = "+27 21 000 0000"
BUSINESS_WEBSITE = "www.acme.co"

CURRENCY_SYMBOL  = "$"
LOGO_PATH        = None            # or "assets/logo.png"
```

### 4 — Customise your services (`services.py`)
```python
SERVICES = [
    "Web Design",
    "Logo Design",
    "SEO Audit",
    # add your own ...
]
```

### 5 — (Optional) Add your logo
Place a PNG logo (~300×100 px) anywhere in the project and set `LOGO_PATH` in `config.py`:
```python
LOGO_PATH = "assets/logo.png"
```

### 6 — Install dependencies & run
```bash
pip install -r requirements.txt
python bot.py
```

---

## Bot Commands

| Command   | Action                         |
|-----------|--------------------------------|
| `/start`  | Welcome message + start flow   |
| `/new`    | Start a new invoice            |
| `/cancel` | Cancel the current invoice     |

---

## Conversation Flow

```
/start or /new
    │
    ├─► Enter customer name
    ├─► Enter customer address
    ├─► Select services (inline buttons, tap to toggle)
    │       ↕  for each service: enter price
    ├─► Review summary + grand total
    ├─► Confirm → PDF generated & sent in chat
    └─► "Create another invoice?"
```

---

## Deploying 24/7

### Option A — Railway.app (easiest)
1. Push the folder to a GitHub repo
2. Create a project on [Railway](https://railway.app) → deploy from GitHub
3. Set environment variables `BOT_TOKEN` and `OWNER_ID` in Railway's dashboard
4. Add a `Procfile`:
   ```
   worker: python bot.py
   ```

### Option B — VPS (e.g. DigitalOcean, Hetzner)
```bash
# Install deps
pip install -r requirements.txt

# Run in background with screen or systemd
screen -S invoicebot
python bot.py
# Ctrl+A, D to detach
```

### Option C — systemd service (Linux VPS)
```ini
# /etc/systemd/system/invoicebot.service
[Unit]
Description=Telegram Invoice Bot
After=network.target

[Service]
WorkingDirectory=/path/to/invoice-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
Environment=BOT_TOKEN=your_token_here
Environment=OWNER_ID=123456789

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable invoicebot
systemctl start invoicebot
```

---

## Generated PDF Features

- Auto-incremented invoice number (`INV-0001`, `INV-0002`, …)
- Today's date + 30-day due date
- Business header with logo (or text fallback)
- Bill-To / From blocks side by side
- Itemised services table with alternating row colours
- Grand total in branded footer band
- Saved as `invoices/invoice_CustomerName_YYYY-MM-DD.pdf`

---

## Customising Brand Colors

In `config.py`:
```python
PRIMARY_COLOR = "#1A1A2E"   # header, table header, footer
ACCENT_COLOR  = "#E94560"   # divider line, "INVOICE" title
LIGHT_BG      = "#F7F9FC"   # alternating table rows
```

---

## Security

- The bot **only responds to your Telegram user ID** (set in `OWNER_ID`)
- All other users receive an "Unauthorized access" rejection
- No data is stored externally — only local PDF files and an invoice counter JSON
