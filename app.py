import base64
import os
import time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_BODY_BYTES", str(12 * 1024 * 1024)))

INGEST_KEY = os.getenv("INGEST_KEY", "mhand")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8700151329:AAHroecXrLhkUgAL_jfr3GYap4N2bzp9TWA")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6550748735")


def authorized(req):
    supplied = req.headers.get("X-Ingest-Key", "")
    if not supplied:
        supplied = req.args.get("key", "")
    return bool(INGEST_KEY) and supplied == INGEST_KEY


def send_to_telegram(image_bytes: bytes, caption: str):
    if not BOT_TOKEN or not CHAT_ID:
        return {"sent": False, "reason": "Telegram is not configured"}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "caption": caption[:1024]},
        files={"photo": ("match.jpg", image_bytes, "image/jpeg")},
        timeout=30,
    )
    response.raise_for_status()
    return {"sent": True}


@app.get("/health")
def health():
    return jsonify({"ok": True, "telegram_configured": bool(BOT_TOKEN and CHAT_ID)})


@app.post("/feedback")
def feedback():
    if not authorized(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    image_b64 = request.form.get("base64_image", "")
    caption = request.form.get("caption", "")
    if not image_b64:
        return jsonify({"ok": False, "error": "base64_image is required"}), 400

    # Accept both raw Base64 and data-URL style input.
    if "," in image_b64 and image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    image_b64 = image_b64.replace("%2B", "+").replace("%2F", "/").replace("%3D", "=")

    try:
        image = base64.b64decode(image_b64, validate=False)
    except Exception:
        return jsonify({"ok": False, "error": "invalid base64_image"}), 400

    if not image:
        return jsonify({"ok": False, "error": "empty image"}), 400

    try:
        result = send_to_telegram(image, caption)
    except requests.RequestException as exc:
        app.logger.warning("Telegram request failed: %s", exc)
        return jsonify({"ok": False, "error": "telegram delivery failed"}), 502

    # Do not save the screenshot or log the UID/caption.
    return jsonify({"ok": True, "bytes": len(image), "telegram": result, "ts": int(time.time())})


@app.errorhandler(413)
def too_large(_):
    return jsonify({"ok": False, "error": "payload too large"}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
