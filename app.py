import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables del entorno (.env o Replit Secrets)
load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Global iPhone")
HUMAN_NUMBER = os.getenv("WHATSAPP_HUMAN_NUMBER", "")

client = OpenAI(api_key=OPENAI_API_KEY)


# --- Reglas rápidas (respuestas instantáneas) ---
def quick_rules(user_text: str):
    t = user_text.lower().strip()

    if t in ("hola", "menu", "menú", "inicio", "ayuda"):
        return (f"Hola 👋 soy el asistente de *{BUSINESS_NAME}*.\n"
                "Elegí una opción o escribí tu consulta:\n"
                "1️⃣ Precios y stock\n"
                "2️⃣ Promos & cuotas (Payway)\n"
                "3️⃣ Envíos y retiros\n"
                "4️⃣ Garantía y cambios\n"
                "5️⃣ Hablar con una persona")

    if t in ("1", "precios", "precio", "stock", "lista"):
        return ("Decime el *modelo* y si lo querés *sellado o usado* "
                "(ej: “iPhone 15 Pro 256 sellado”).")

    if t in ("2", "promos", "promo", "cuotas", "payway"):
        return (
            "Promo ⭐ *3 cuotas sin interés*.\n"
            "Con interés: 6 y 9 cuotas vía Payway.\n"
            "Decime el *monto* y la *cantidad de cuotas* y te calculo al toque."
        )

    if t in ("3", "envio", "envíos", "retiro", "retiros", "entrega"):
        return ("Entregamos en *Córdoba* y *Catamarca*. "
                "Podés retirar o pedir envío a domicilio 🚚.")

    if t in ("4", "garantia", "garantía", "cambios", "devolucion",
             "devolución"):
        return (
            "Todos nuestros equipos tienen *garantía escrita*. "
            "Si surge un problema real de fábrica, *te cambiamos el equipo*.")

    if t in ("5", "humano", "asesor", "vendedor"):
        if HUMAN_NUMBER:
            return (f"Te derivo con un asesor humano 👉 {HUMAN_NUMBER}\n"
                    "También podés seguir consultando conmigo 🤖.")
        else:
            return (
                "¡Listo! Aviso a un asesor humano para que te escriba en breve."
            )

    return None


# --- Prompt de sistema para ChatGPT ---
SYSTEM_PROMPT = f"""
Sos un asesor de ventas de {BUSINESS_NAME}. Respondé en español rioplatense, de forma clara y amable.
Objetivo: ayudar al cliente a comprar o resolver dudas sobre productos Apple.
Nunca inventes precios; pedí modelo y condición (sellado/usado) si falta información.
Podés ofrecer cuotas, garantía, envío y derivar a un humano si lo piden.
Usá emojis sobrios y viñetas si ayudan a la claridad.
"""


def ai_reply(user_text: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": SYSTEM_PROMPT
        }, {
            "role": "user",
            "content": user_text
        }],
        temperature=0.3,
    )
    return completion.choices[0].message.content.strip()


@app.route("/", methods=["GET"])
def home():
    return "Bot activo ✅"


@app.route("/webhook", methods=["GET", "POST"])
def verify_webhook():
    if request.method == "GET":
        # Token de verificación que definiste en Meta
        VERIFY_TOKEN = "globalstore123"

        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verificado correctamente con Meta")
            return challenge, 200
        else:
            print("❌ Token de verificación inválido")
            return "Token de verificación inválido", 403

    elif request.method == "POST":
        data = request.get_json()
        print("📩 Nuevo mensaje recibido:", data)
        return "EVENT_RECEIVED", 200


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    quick = quick_rules(incoming_msg)
    if quick:
        msg.body(quick)
        return str(resp)

    try:
        answer = ai_reply(incoming_msg)
    except Exception:
        answer = "Tuve un pequeño error técnico 🤖, probá de nuevo o escribí *menú*."

    msg.body(answer)
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
