"""
bot.py — Telegram Invoice Bot (python-telegram-bot v20+)
Full conversation flow: customer details → service selection → summary → PDF.
"""

import logging
import io
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes,
)

from config import BOT_TOKEN, ALLOWED_USERS, CURRENCY_SYMBOL
from services import SERVICES
from invoice_generator import generate_invoice, next_invoice_number

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Conversation states
# ─────────────────────────────────────────────
(
    ASK_NAME,
    ASK_ADDRESS,
    PICK_SERVICE,
    ASK_PRICE,
    CONFIRM,
    ASK_ANOTHER,
) = range(6)

# ─────────────────────────────────────────────
# Access guard — allows multiple users
# ─────────────────────────────────────────────

def _is_allowed(update: Update) -> bool:
    return update.effective_user.id in ALLOWED_USERS


async def _reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "⛔ This is a private bot. Unauthorized access."
    )


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _service_keyboard(selected_names: set) -> InlineKeyboardMarkup:
    buttons = []
    for svc in SERVICES:
        label = f"✅ {svc}" if svc in selected_names else svc
        buttons.append([InlineKeyboardButton(label, callback_data=f"svc:{svc}")])
    buttons.append([InlineKeyboardButton("✔️  Done — generate invoice", callback_data="done")])
    return InlineKeyboardMarkup(buttons)


def _format_selected(services: list) -> str:
    if not services:
        return "_(none yet)_"
    lines = [f"• {s['name']}:  {CURRENCY_SYMBOL}{float(s['price']):,.2f}" for s in services]
    return "\n".join(lines)


def _total(services: list) -> float:
    return sum(float(s["price"]) for s in services)


# ─────────────────────────────────────────────
# Conversation entry points
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        await _reject(update, context)
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "👋 Welcome to *Clean Pune Invoice Bot*!\n\n"
        "I'll guide you through creating a professional PDF invoice.\n\n"
        "Let's start — what is the *customer's name*?",
        parse_mode="Markdown",
    )
    return ASK_NAME


async def new_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        await _reject(update, context)
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "❌ Invoice creation cancelled. Type /new to start again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────
# Step 1 — Customer details
# ─────────────────────────────────────────────

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Please enter a valid customer name.")
        return ASK_NAME

    context.user_data["customer_name"] = name
    await update.message.reply_text(
        f"Great! Customer: *{name}*\n\nNow enter the *customer's address*:",
        parse_mode="Markdown",
    )
    return ASK_ADDRESS


async def got_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    address = update.message.text.strip()
    if not address:
        await update.message.reply_text("Please enter a valid address.")
        return ASK_ADDRESS

    context.user_data["customer_address"] = address
    context.user_data.setdefault("services", [])

    await update.message.reply_text(
        "📋 *Select services* — tap a service to add it, then enter the price.\n"
        "Tap ✔️ *Done* when finished.\n\n"
        "_Selected so far:_ _(none yet)_",
        parse_mode="Markdown",
        reply_markup=_service_keyboard(set()),
    )
    return PICK_SERVICE


# ─────────────────────────────────────────────
# Step 2 — Service selection
# ─────────────────────────────────────────────

async def service_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "done":
        services = context.user_data.get("services", [])
        if not services:
            await query.edit_message_text(
                "⚠️ You haven't selected any services yet.\n"
                "Please tap at least one service.",
                reply_markup=_service_keyboard(set()),
            )
            return PICK_SERVICE

        name    = context.user_data["customer_name"]
        address = context.user_data["customer_address"]
        svc_txt = _format_selected(services)
        grand   = _total(services)

        summary = (
            "📄 *Invoice Summary*\n\n"
            f"👤 Customer:  {name}\n"
            f"📍 Address:   {address}\n\n"
            f"*Services:*\n{svc_txt}\n\n"
            f"💰 *Grand Total:  {CURRENCY_SYMBOL}{grand:,.2f}*\n\n"
            "Confirm and generate the PDF invoice?"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, generate!", callback_data="confirm:yes"),
                InlineKeyboardButton("✏️ Edit", callback_data="confirm:edit"),
            ]
        ])
        await query.edit_message_text(summary, parse_mode="Markdown", reply_markup=keyboard)
        return CONFIRM

    # A service was tapped
    svc_name = data.removeprefix("svc:")
    services = context.user_data.get("services", [])
    selected_names = {s["name"] for s in services}

    if svc_name in selected_names:
        # Toggle off — remove it
        context.user_data["services"] = [s for s in services if s["name"] != svc_name]
        selected_names.discard(svc_name)
        svc_txt = _format_selected(context.user_data["services"])
        await query.edit_message_text(
            f"➖ Removed *{svc_name}*.\n\n"
            f"_Selected so far:_\n{svc_txt}\n\n"
            "Tap another service or ✔️ Done.",
            parse_mode="Markdown",
            reply_markup=_service_keyboard(selected_names),
        )
        return PICK_SERVICE

    # Ask for price
    context.user_data["pending_service"] = svc_name
    await query.edit_message_text(
        f"💵 Enter the price for *{svc_name}*:\n_(numbers only, e.g. 350 or 1500.50)_",
        parse_mode="Markdown",
    )
    return ASK_PRICE


async def got_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    raw = update.message.text.strip().replace(",", "")
    try:
        price = float(raw)
        if price < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid price. Please enter a positive number (e.g. *350* or *1500.50*).",
            parse_mode="Markdown",
        )
        return ASK_PRICE

    svc_name = context.user_data.pop("pending_service")
    context.user_data["services"].append({"name": svc_name, "price": price})

    selected_names = {s["name"] for s in context.user_data["services"]}
    svc_txt = _format_selected(context.user_data["services"])

    await update.message.reply_text(
        f"✅ Added *{svc_name}* — {CURRENCY_SYMBOL}{price:,.2f}\n\n"
        f"_Selected so far:_\n{svc_txt}\n\n"
        "Tap another service or ✔️ Done.",
        parse_mode="Markdown",
        reply_markup=_service_keyboard(selected_names),
    )
    return PICK_SERVICE


# ─────────────────────────────────────────────
# Step 3 — Confirm
# ─────────────────────────────────────────────

async def confirm_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    if query.data == "confirm:edit":
        services = context.user_data.get("services", [])
        selected_names = {s["name"] for s in services}
        svc_txt = _format_selected(services)
        await query.edit_message_text(
            "✏️ *Edit your services*\n\n"
            "Tap a ✅ service to remove it, or tap a new one to add it.\n\n"
            f"_Currently selected:_\n{svc_txt}",
            parse_mode="Markdown",
            reply_markup=_service_keyboard(selected_names),
        )
        return PICK_SERVICE

    # confirm:yes — generate invoice
    await query.edit_message_text("⏳ Generating your invoice PDF…")

    name     = context.user_data["customer_name"]
    address  = context.user_data["customer_address"]
    services = context.user_data["services"]

    try:
        # Returns (bytes, filename) — no disk file needed
        pdf_bytes, pdf_filename = generate_invoice(name, address, services)
    except Exception as e:
        logger.exception("PDF generation failed")
        await query.message.reply_text(
            f"❌ Failed to generate invoice:\n`{e}`",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Send PDF directly from memory
    await query.message.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=pdf_filename,
        caption=(
            f"📄 Invoice for *{name}*\n"
            f"Total: {CURRENCY_SYMBOL}{_total(services):,.2f}"
        ),
        parse_mode="Markdown",
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data="another:yes"),
            InlineKeyboardButton("❌ No",  callback_data="another:no"),
        ]
    ])
    await query.message.reply_text(
        "✅ Invoice sent!\n\nWould you like to create *another invoice*?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    context.user_data.clear()
    return ASK_ANOTHER


# ─────────────────────────────────────────────
# Step 4 — Another invoice?
# ─────────────────────────────────────────────

async def another_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    if query.data == "another:yes":
        context.user_data.clear()
        await query.edit_message_text(
            "🆕 Starting a new invoice!\n\nEnter the *customer's name*:",
            parse_mode="Markdown",
        )
        return ASK_NAME
    else:
        await query.edit_message_text(
            "👋 All done! Type /new whenever you need a new invoice."
        )
        return ConversationHandler.END


# ─────────────────────────────────────────────
# Fallback
# ─────────────────────────────────────────────

async def unexpected_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_allowed(update):
        return ConversationHandler.END
    await update.message.reply_text(
        "Please use the buttons above to select a service, or tap ✔️ Done.",
    )
    return PICK_SERVICE


# ─────────────────────────────────────────────
# App entry point
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("new",   new_invoice),
        ],
        states={
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_name),
            ],
            ASK_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_address),
            ],
            PICK_SERVICE: [
                CallbackQueryHandler(service_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            ],
            ASK_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_price),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_button, pattern="^confirm:"),
            ],
            ASK_ANOTHER: [
                CallbackQueryHandler(another_button, pattern="^another:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Bot started. Polling…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
