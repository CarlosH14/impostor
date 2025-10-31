from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Sandbox por defecto

# Cliente de Twilio
twilio_client = None

def get_twilio_client():
    """Obtener cliente de Twilio"""
    global twilio_client
    if not twilio_client and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return twilio_client


async def send_word_via_whatsapp(phone_number: str, player_name: str, word: str, is_impostor: bool):
    """
    Envía la palabra del juego al jugador por WhatsApp
    
    Args:
        phone_number: Número de teléfono con formato +52XXXXXXXXXX
        player_name: Nombre del jugador
        word: Palabra asignada
        is_impostor: Si el jugador es el impostor
    """
    client = get_twilio_client()
    
    if not client:
        print("⚠️ Twilio no configurado. No se enviará mensaje de WhatsApp.")
        return False
    
    try:
        # Formatear número para WhatsApp
        if not phone_number.startswith("whatsapp:"):
            phone_number = f"whatsapp:{phone_number}"
        
        # Crear mensaje personalizado
        if is_impostor:
            message_body = f"""🎮 *Juego del Impostor*

Hola {player_name}! 👋

⚠️ *¡Eres el IMPOSTOR!* ⚠️

Tu palabra es: *{word}*

Intenta descubrir la palabra real sin ser descubierto. 🕵️

¡Buena suerte!"""
        else:
            message_body = f"""🎮 *Juego del Impostor*

Hola {player_name}! 👋

Tu palabra es: *{word}*

Recuerda que hay un impostor entre ustedes. 🤔

¡Buena suerte!"""
        
        # Enviar mensaje
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_FROM,
            to=phone_number
        )
        
        print(f"✅ WhatsApp enviado a {player_name}: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando WhatsApp a {player_name}: {e}")
        return False


async def send_game_started_notification(phone_number: str, player_name: str, game_id: str):
    """
    Notifica al jugador que el juego ha iniciado
    """
    client = get_twilio_client()
    
    if not client:
        return False
    
    try:
        if not phone_number.startswith("whatsapp:"):
            phone_number = f"whatsapp:{phone_number}"
        
        message_body = f"""🎮 *Juego del Impostor*

¡Hola {player_name}!

El juego está por comenzar. 🚀
Código de partida: {game_id}

En un momento recibirás tu palabra secreta."""
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_FROM,
            to=phone_number
        )
        
        print(f"✅ Notificación enviada a {player_name}: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación a {player_name}: {e}")
        return False
