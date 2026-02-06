from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import pytz
import os

app = Client("55MexMiniGamesBot", api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627", bot_token=os.getenv("BOT_TOKEN"))

daily_winners = set()
last_reset_date = datetime.now().date()
PH_TZ = pytz.timezone("Asia/Manila")


dice_active = False
darts_active = False
slots_active = False
basketball_active = False
football_active = False

dice_attempts = {}
basketball_attempts={}
darts_attempts={}
slots_attempts=set()
football_attempts={}
basketball_success = {}
basketball_winners = set()
darts_won_first = set()
result=''
SLOT_SYMBOLS = ["🍒", "🍋", "7️⃣", "BAR"]

GAME_EMOJI_MAP = {
    "Dice": "🎲",
    "Basketball": "🏀",
    "Slots": "🎰",
    "Football": "⚽",
    "Darts":"🎯"
}

def get_active_game_emojis():
    active = []
    if dice_active:
        active.append(GAME_EMOJI_MAP["Dice"])
    if basketball_active:
        active.append(GAME_EMOJI_MAP["Basketball"])
    if slots_active:
        active.append(GAME_EMOJI_MAP["Slots"])
    if darts_active:
        active.append(GAME_EMOJI_MAP["Darts"])
    if football_active:
        active.append(GAME_EMOJI_MAP["Football"])
    return active

def is_forwarded(message: Message) -> bool:
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_sender_name
    )

def reset_daily_winners():
    global daily_winners, last_reset_date
    now_ph = datetime.now(PH_TZ)
    today_ph = now_ph.date()

    if today_ph != last_reset_date:
        daily_winners.clear()
        last_reset_date = today_ph

def decode_slot(value: int):
    n = value - 1
    s1 = SLOT_SYMBOLS[n % 4]
    s2 = SLOT_SYMBOLS[(n // 4) % 4]
    s3 = SLOT_SYMBOLS[(n // 16) % 4]
    return s1, s2, s3


def calculate_slot_payout(s1, s2, s3):
    if s1 == s2 == s3:
        return "¡¡¡BOTE!!!", 50
    if s1 == s2 or s1 == s3 or s2 == s3:
        return "¡Lindo! ¡Golpeas 2 iguales!", 15
    return "¡Bien hecho!", 5


async def is_admin(client, message):
    # Ignore non-group
    if not message.chat:
        return False

    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True

    if message.from_user:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status.value in ("administrator", "owner")

    return False

@app.on_message(filters.command(["startdice", "stopdice", "startdarts", "stopdarts", "startslots", "stopslots", "startbasket", "stopbasket", "startfoot", "stopfoot"]) & filters.group)
async def game_control(client, message: Message):
    if not await is_admin(client, message):
        await message.delete()
        await client.send_message(message.chat.id,"🎮Envía el emoji adecuado del juego que está actualmente activo.🎮")
        return

    cmd = message.text.lower()

    global dice_active, darts_active, slots_active, basketball_active, football_active, bowling_active

    if cmd == "/startdice":
        dice_active = True
        await message.reply("¡El juego de dados ya está activo! Envía un emoji de 🎲 para participar")
        await app.send_dice(chat_id=message.chat.id,emoji="🎲")
    elif cmd == "/stopdice":
        dice_active = False
        dice_attempts.clear()
        await message.reply("El juego de dados se detuvo.❌")

    elif cmd == "/startdarts":
        darts_active = True
        await message.reply("¡El juego de dardos ya está activo! Envía un emoji de 🎯 para participar.")
        await app.send_dice(chat_id=message.chat.id,emoji="🎯")
    elif cmd == "/stopdarts":
        darts_active = False
        darts_attempts.clear()
        darts_won_first.clear()
        await message.reply("El juego de dardos se detuvo.❌")

    elif cmd == "/startslots":
        slots_active = True
        await message.reply("¡La máquina tragamonedas ya está activa! Envía un emoji de 🎰 para participar.")
        await app.send_dice(chat_id=message.chat.id,emoji="🎰")        
    elif cmd == "/stopslots":
        slots_active = False
        slots_attempts.clear()
        await message.reply("La máquina tragamonedas se detuvo.❌")

    elif cmd == "/startbasket":
        basketball_active = True
        await message.reply("¡El juego de baloncesto ya está activo! Envía un emoji de 🏀 para participar.")
        await app.send_dice(chat_id=message.chat.id,emoji="🏀")
    elif cmd == "/stopbasket":
        basketball_active = False
        basketball_attempts.clear()
        basketball_success.clear()
        await message.reply("El partido de baloncesto se detuvo.❌")

    elif cmd == "/startfoot":
        football_active = True
        await message.reply("¡El juego de fútbol ya está activo! Envía un emoji de ⚽️ para participar.")
        await app.send_dice(chat_id=message.chat.id,emoji="⚽️")
    elif cmd == "/stopfoot":
        football_active = False
        football_attempts.clear()
        await message.reply("El partido de fútbol se detuvo.❌")
    
@app.on_message(filters.group)
async def detect_mini_game(client, message: Message):
    if message.sticker:
        await message.reply("¡Es una pegatina! Si quieres participar, envía el emoji correcto.")
        return
    
    if message.dice:    
        if await is_admin(client, message):
            return

        emoji = message.dice.emoji
        value = message.dice.value          
        user = message.from_user.username or message.from_user.first_name
        user_id = message.from_user.id
        reset_daily_winners()

        if emoji.startswith("🎲") and not dice_active:
            active_games = get_active_game_emojis()
            if active_games: 
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("🎲 El juego de dados no está activo actualmente.. ❌", quote=True)
            return

        if emoji.startswith("🎯") and not darts_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("🎯 El juego de dardos no está activo actualmente.. ❌", quote=True)
            return

        if emoji.startswith("🎰") and not slots_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                ) 
            else:
                await message.reply("🎰 La máquina tragamonedas no está activa actualmente.. ❌", quote=True)
            return

        if emoji.startswith("🏀") and not basketball_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                ) 
            else:
                await message.reply("🏀 El juego de baloncesto no está activo actualmente. ❌", quote=True)
            return

        if emoji.startswith("⚽") and not football_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **Este juego no está activo.**\n\n"
                    "🎮 Juegos activos que puedes jugar:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Envía el emoji del juego que quieres jugar.",
                    quote=True
                )
            else:
                await message.reply("⚽ El juego de fútbol no está activo actualmente.. ❌", quote=True)
            return

        if emoji.startswith("🎲"):   # Dice
            if is_forwarded(message):
                await message.reply("🚫 ¡No se permite reenviar un emoji!", quote=True)
                return


            attempts = dice_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("¡No tienes más posibilidades de tirar los dados en esta ronda! ❌", quote=True)
                return

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya ganaste en otro juego hoy! ¡Vuelve mañana! 😊", quote=True)
                return

            current_attempt = attempts + 1
            dice_attempts[user_id] = current_attempt

            await message.reply(f"@{user} sacó {value} en 🎲 - (posibilidades {attempts + 1}/2)")
            if value == 6:
                daily_winners.add(user_id)
                await message.reply(f"@{user} ¡¡GANA 20 Mexican pesos!! (perfecto 6) 🎉\n\n"
                                    f"captura de pantalla de su depósito de 10MXN hoy junto con su ID de jugador para reclamar su premio.\n\n"
                                    "NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO")
                if current_attempt == 1:
                    await message.reply("¡Ganaste en tu primer intento, tu segunda oportunidad ha sido eliminada!", quote=True)
                
                dice_attempts[user_id] = 2

        elif emoji.startswith("🎯"): # Darts
            if is_forwarded(message):
                await message.reply("🚫 ¡No se permite reenviar un emoji!", quote=True)
                return

            attempts = darts_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("¡No te quedan posibilidades en esta ronda!", quote=True)
                return

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya ganaste en otro juego hoy! ¡Vuelve mañana! 😊", quote=True)
                return

            attempts += 1
            darts_attempts[user_id] = attempts

            score = message.dice.value

            if score == 6:  
                prize = "20MXN"
                msg =f"¡¡Felicitaciones!! @{user} gana {prize} ¡Foto perfecta!\n\n"
                f"Envíe una captura de pantalla de su depósito de 100MXN hoy junto con su ID de jugador para reclamar su premio.\n\n"
                f"NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO"
                # If won on first try → block second attempt
                daily_winners.add(user_id)
                if attempts == 1:
                    darts_attempts[user_id] = 2
                    msg += "\n¡Ganaste en tu PRIMER lanzamiento, segunda oportunidad eliminada!"

            elif score > 1:  # Hit the board
                prize = "5MXN"
                msg = f"¡Buen golpe! @{user} gana {prize}**\n\nEnvíe una captura de pantalla de su depósito de 100MXN hoy junto con su ID de jugador para reclamar su premio.\n\nNOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO"

                daily_winners.add(user_id)
                if attempts == 1:
                    darts_attempts[user_id] = 2
                    msg += "\n¡Ganaste en tu PRIMER lanzamiento, segunda oportunidad eliminada!"

            else:  # score == 0 → missed
                msg = f"¡Ay! ¡{user} se perdió el tablero por completo!\n¡Más suerte en tu próximo lanzamiento!"

            await message.reply(msg, quote=True)

        elif emoji.startswith("🎰"): # Slot Machine
            if is_forwarded(message):
                await message.reply("🚫 ¡No se permite reenviar un emoji!", quote=True)
                return

            if user_id in slots_attempts:
                await message.reply("¡Ya usaste tu 1 giro de tragamonedas en esta ronda!", quote=True)
                return

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya ganaste en otro juego hoy! ¡Vuelve mañana! 😊", quote=True)
                return

            slots_attempts.add(user_id)
            
            s1, s2, s3 = decode_slot(value)

            status, payout = calculate_slot_payout(s1, s2, s3) 

            msg = (
                f"🎰 **Slot Machine** 🎰\n"
                f"**{status}**\n"
                f"Reward: {payout}MXN\n\n"
                "Envíe una captura de pantalla de su depósito de 300MXN hoy junto con su ID de jugador para reclamar su premio.\n\n"
                "NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO"
            )
            await message.reply(msg, quote=True)
            daily_winners.add(user_id)

        elif emoji.startswith("🏀"): # Basketball
            if is_forwarded(message):
                await message.reply("🚫 ¡No se permite reenviar un emoji!", quote=True)
                return

            attempts = basketball_attempts.get(user_id, 0)
            success = basketball_success.get(user_id, 0)
            value = message.dice.value

            if attempts >= 2:
                await message.reply("¡Ya usaste tus 2 oportunidades de baloncesto en esta ronda! ❌", quote=True)
                return

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya ganaste en otro juego hoy! ¡Vuelve mañana! 😊", quote=True)
                return

            attempts += 1
            basketball_attempts[user_id] = attempts

            made_this_shot = 1 if value >= 4 else 0
            success += made_this_shot
            basketball_success[user_id] = success

            goals_this_shot = "2 goles" if value == 5 else "1 gol" if value == 4 else "fallado"
            await message.reply(f"@{user} → Disparo {attempts}/2: {goals_this_shot}")


            if made_this_shot:
                await message.reply("¡SWISH! ¡Hice el tiro!", quote=True)
            else:
                await message.reply("Airball…¡fallado!", quote=True)

            if attempts == 1 and made_this_shot:
                daily_winners.add(user_id)
                await message.reply(
                    f"@{user} ¡GANA 10MXN en el primer tiro! 🎉\n"
                    "¡Aún tienes 1 intento más, dispara de nuevo!",
                    quote=True
                )
                return 

            if attempts == 2:
                if success == 2:
                    # Won both shots
                    daily_winners.add(user_id)
                    await message.reply(
                        f"**🤴¡¡¡LEYENDA DEL BALONCESTO!!! 🤴**\n\n"
                        f"¡@{user} anotó en AMBOS tiros!**\n"
                        f"** Ganas 10MXN + título de estrella del baloncesto**\n\n"
                        "Envíe una captura de pantalla de su depósito de 100MXN hoy junto con su ID de jugador para reclamar su premio.\n\n"
                        "NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO",
                        quote=True
                    )

                elif success == 1:
                    # Won exactly one shot
                    daily_winners.add(user_id)
                    await message.reply(
                        f"¡Buen partido! @{user} **acertó 1 de 2 tiros**.\n"
                        f"**Ganas 10MXN**\n\n"
                        "Envíe una captura de pantalla de su depósito de 100MXN hoy junto con su ID de jugador para reclamar su premio."
                        "NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO",
                        quote=True
                    )

                else:
                    # Missed both shots
                    await message.reply(
                        f"Mala suerte, @{user}… **0/2 tiros acertados**\n"
                        "Esta ronda no tiene premio. ¡Mejor suerte la próxima!",
                        quote=True
                    )

        elif emoji.startswith("⚽"): # Football
            if is_forwarded(message):
                await message.reply("🚫 ¡No se permite reenviar un emoji!", quote=True)
                return

            attempts = football_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("¡Ya no tienes más posibilidades de gol en esta ronda! ❌", quote=True)
                return

            if user_id in daily_winners:
                await message.reply("🚫 ¡Ya ganaste en otro juego hoy! ¡Vuelve mañana! 😊", quote=True)
                return

            current_attempt = attempts + 1
            football_attempts[user_id] = current_attempt

            await message.reply(f"@{user} expulsado - oportunidad ({attempts + 1}/2)")
            if value in (4, 5, 6):
                daily_winners.add(user_id)
                await message.reply("⚽GOL⚽\n\n"
                                    f"@{user}GANA 10 Mexican Pesos!!🎉 🎉\n\n"
                                    f"Envía una captura de pantalla de tu depósito de 100MXN hoy junto con tu ID de jugador para reclamar tu premio.\n\n"
                                    "NOTA: EL DEPÓSITO DEBE REALIZARSE ANTES DE HABER JUGADO EL JUEGO, NO DESPUÉS DE JUGARLO")
                if current_attempt == 1:
                    await message.reply("¡Ganaste en tu primer intento, tu segunda oportunidad ha sido eliminada!", quote=True)
                    football_attempts[user_id] = 2
            else:
                await message.reply("¡Mejor suerte la próxima vez!", quote=True)             

app.run()
