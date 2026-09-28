# Feedback Relay Server

سيرفر Flask وسيط: يستقبل `base64_image` و`caption` من سكربت Lua، ثم يرسل الصورة إلى Telegram Bot API. الصورة تُعالج في الذاكرة ولا تُحفظ على القرص.

## مهم قبل الرفع

- لا تضع توكن Telegram أو `INGEST_KEY` داخل GitHub.
- أضف الأسرار من لوحة الاستضافة كـ Environment Variables.
- GitHub يخزن الكود فقط؛ لا يشغّل Flask بنفسه. استخدم Render أو Railway أو خدمة مشابهة.

## تشغيل محلي

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INGEST_KEY='ضع-مفتاحاً عشوائياً طويلاً'
export TELEGRAM_BOT_TOKEN='توكن البوت'
export TELEGRAM_CHAT_ID='رقم القروب أو الحساب'
python app.py
```

## نشر على Render

1. ارفع محتويات هذا المجلد إلى مستودع GitHub جديد.
2. في Render اختر **New > Web Service** ثم اربط مستودع GitHub.
3. استخدم:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. أضف Environment Variables:
   - `INGEST_KEY`: مفتاح عشوائي طويل.
   - `TELEGRAM_BOT_TOKEN`: توكن البوت.
   - `TELEGRAM_CHAT_ID`: Chat ID.
5. بعد النشر اختبر:

```text
https://YOUR-SERVICE.onrender.com/health
```

يجب أن يظهر `ok: true` و`telegram_configured: true`.

## ربط Lua

بعد حصولك على رابط Render، ضع:

```lua
ServerURL = "https://YOUR-SERVICE.onrender.com/feedback?key=INGEST_KEY"
```

الأفضل أمنياً إرسال المفتاح في Header، لكن سكربت Lua الحالي يستخدم query parameter. لا تشارك رابط `ServerURL` لأنه يحتوي على مفتاح الاستقبال.

## اختبار يدوي

```bash
IMAGE=$(printf 'test-image' | base64 -w0)
curl -X POST 'https://YOUR-SERVICE.onrender.com/feedback?key=INGEST_KEY' \
  --data-urlencode "base64_image=$IMAGE" \
  --data-urlencode "caption=اختبار"
```
