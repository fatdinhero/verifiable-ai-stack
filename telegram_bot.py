#!/usr/bin/env python3
"""
telegram_bot.py
COGNITUM Telegram Ingestion Bot
Empfaengt Links, Bilder, Videos, Text von Fatih und verarbeitet
sie als Signale fuer den Autonomous Loop.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from governance.ingestion import IngestionLayer

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(REPO_ROOT / "logs" / "telegram_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

TOKEN_FILE    = Path.home() / ".telegram-token"
WHITELIST_FILE = Path.home() / ".telegram-whitelist"
BOT_QUEUE_FILE = REPO_ROOT / ".bot_queue.json"
STATE_FILE     = REPO_ROOT / ".loop_state.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_token() -> str:
    if not TOKEN_FILE.exists():
        logger.error(f"Token-Datei nicht gefunden: {TOKEN_FILE}")
        logger.error("Lege ~/.telegram-token an und trage den Bot-Token ein.")
        sys.exit(1)
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        logger.error("~/.telegram-token ist leer.")
        sys.exit(1)
    return token


def _load_whitelist() -> set[int]:
    if not WHITELIST_FILE.exists():
        logger.warning(
            f"Keine Whitelist-Datei gefunden ({WHITELIST_FILE}). "
            "Alle Nachrichten werden akzeptiert!"
        )
        return set()
    ids = set()
    for line in WHITELIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.isdigit():
            ids.add(int(line))
    logger.info(f"Whitelist geladen: {ids}")
    return ids


def _load_bot_queue() -> list:
    if BOT_QUEUE_FILE.exists():
        try:
            return json.loads(BOT_QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_bot_queue(queue: list) -> None:
    BOT_QUEUE_FILE.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


WHITELIST: set[int] = set()
ingestion = IngestionLayer()


# ── Guards ────────────────────────────────────────────────────────────────────

def _is_allowed(update: Update) -> bool:
    if not WHITELIST:
        return True
    user_id = update.effective_user.id if update.effective_user else None
    return user_id in WHITELIST


# ── Commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "COGNITUM Ingestion Bot aktiv. Sende mir:\n"
        "- Links (YouTube, TikTok, Websites)\n"
        "- Bilder/Screenshots\n"
        "- PDFs\n"
        "- Beliebigen Text\n"
        "Ich extrahiere Engineering-Signale und fuege sie dem Loop hinzu."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    state = _load_state()
    queue = _load_bot_queue()
    processed = state.get("processed_count", 0)
    avg_score  = state.get("avg_score", 0.0)
    elapsed_s  = max(state.get("total_runtime_s", 1), 1)
    rate = (processed / elapsed_s) * 3600 if processed else 0.0
    await update.message.reply_text(
        f"Loop: {processed} Cases verarbeitet | "
        f"Avg Score: {avg_score:.2f} | "
        f"Rate: {rate:.1f}/h\n"
        f"Bot-Queue: {len(queue)} Eintraege ausstehend"
    )


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    queue = _load_bot_queue()
    if not queue:
        await update.message.reply_text("Bot-Queue ist leer.")
        return
    last5 = queue[-5:]
    lines = []
    for i, entry in enumerate(last5, 1):
        src = entry.get("source_type", "?")
        title = entry.get("title", "")[:60]
        score = entry.get("relevance_score", 0.0)
        lines.append(f"{i}. [{src}] (Score: {score:.2f}) {title}")
    await update.message.reply_text("Letzte 5 Bot-Queue Eintraege:\n" + "\n".join(lines))


# ── Message Handler ───────────────────────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        logger.warning(
            f"Nachricht von unbekanntem User {update.effective_user.id} blockiert."
        )
        return

    msg = update.message
    if not msg:
        return

    await msg.reply_text("Verarbeite... ⏳")

    result = None

    # Foto
    if msg.photo:
        photo = msg.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        result = ingestion.ingest(bytes(img_bytes), "image")

    # Dokument (PDF oder Bild)
    elif msg.document:
        doc = msg.document
        file = await context.bot.get_file(doc.file_id)
        doc_bytes = await file.download_as_bytearray()
        mime = doc.mime_type or ""
        if "pdf" in mime:
            result = ingestion.ingest(bytes(doc_bytes), "pdf")
        elif "image" in mime:
            result = ingestion.ingest(bytes(doc_bytes), "image")
        else:
            # Versuche als Text
            try:
                text = bytes(doc_bytes).decode("utf-8", errors="replace")
                result = ingestion.ingest(text, "text")
            except Exception:
                result = ingestion.ingest(doc.file_name or "Datei", "text")

    # Video / Video-Note
    elif msg.video or msg.video_note:
        caption = msg.caption or ""
        if caption.startswith("http"):
            result = ingestion.ingest(caption, "url")
        else:
            result = ingestion.ingest(caption or "Video-Nachricht", "text")

    # Text / URL
    elif msg.text:
        text = msg.text.strip()
        if text.startswith("http"):
            result = ingestion.ingest(text, "url")
        else:
            result = ingestion.ingest(text, "text")

    if result is None:
        await msg.reply_text("Medientyp nicht unterstuetzt.")
        return

    # Kein Relevanz-Filter — User-Eingaben sind immer relevant
    extracted_text = result.get("text", "")
    if not extracted_text or extracted_text in ("Bild ohne extrahierbaren Text", "PDF ohne extrahierbaren Text"):
        await msg.reply_text(
            f"ℹ️ Kein Text extrahierbar.\n"
            f"Typ: {result.get('source_type', '?')}"
        )
        return

    queue = _load_bot_queue()
    queue_entry = {
        **result,
        "priority": 0,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "telegram_user_id": update.effective_user.id,
    }
    queue.append(queue_entry)
    _save_bot_queue(queue)
    logger.info(f"Bot-Queue: +1 Eintrag '{result.get('title', '')[:60]}'")

    await msg.reply_text(
        f"✅ Signal gespeichert — wird im naechsten Batch verarbeitet\n"
        f"Extrahiert: {extracted_text[:150]}\n"
        f"Quelle: {result.get('source_type', '?')}"
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    global WHITELIST
    WHITELIST = _load_whitelist()
    token = _load_token()

    (REPO_ROOT / "logs").mkdir(exist_ok=True)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO | filters.VIDEO_NOTE,
        on_message,
    ))

    logger.info("COGNITUM Telegram Bot gestartet.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
