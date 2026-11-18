
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SHOPEE_DOMAINS = (
    "shopee.co.id",
    "s.shopee.co.id",
    "shp.ee",
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Selamat datang di Bot Shopee Affiliate! 🛍️\n\n"
        "Kirim nama produk dan link Shopee.\n\n"
        "Contoh:\n"
        "Tas Wanita Kekinian\n"
        "https://shopee.co.id/contoh-produk"
    )


async def convert_shopee_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message.text or ""

    match = re.search(r"https?://\S+", message)

    if not match:
        await update.message.reply_text(
            "Kirim link produk Shopee terlebih dahulu."
        )
        return

    original_url = match.group(0).rstrip(".,!?)")
    parsed = urlparse(original_url)
    hostname = (parsed.hostname or "").lower()

    if not any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in SHOPEE_DOMAINS
    ):
        await update.message.reply_text(
            "Maaf, link tersebut bukan link Shopee."
        )
        return

    product_name = message.replace(match.group(0), "").strip()

    if not product_name:
        product_name = "Produk pilihan"

    await update.message.reply_text(
        "Sedang memeriksa link dan membuat caption... ⏳"
    )

    product_url = original_url

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20
        ) as client:
            response = await client.get(
                original_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if response.is_success:
                product_url = str(response.url)

    except httpx.HTTPError:
        logging.warning("Link tidak berhasil diarahkan.")

    caption = (
        "🔥 REKOMENDASI PRODUK 🔥\n\n"
        f"✨ {product_name}\n\n"
        "Lagi cari produk menarik? Yuk cek produk ini!\n"
        "Cek detail dan harga produknya sekarang.\n\n"
        f"🛒 Link produk:\n{product_url}\n\n"
        "Jangan sampai kehabisan!\n\n"
        "#ShopeeAffiliate #ShopeeFinds "
        "#RekomendasiProduk #BelanjaOnline"
    )

    await update.message.reply_text(
        caption + "\n\n"
        "Catatan: Link di atas belum otomatis menjadi "
        "link affiliate. Generator resmi Shopee akan "
        "kita hubungkan pada tahap berikutnya."
    )


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN belum diatur di Render."
        )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            convert_shopee_link
        )
    )

    print("Bot Shopee Affiliate berjalan!")

    app.run_polling()
