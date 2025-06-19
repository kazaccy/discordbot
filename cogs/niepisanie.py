
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import pytz
import os
import json
BANNED_DATA = "data/lista_zakazanych.json"
raw_ids = os.getenv("ADMIN_IDS", "")
admin_ids = [int(id.strip()) for id in raw_ids.split(",") if id.strip()]

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Zakazani(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.lista_zakazanych = load_json(BANNED_DATA)
    @app_commands.command(name="blokuj_uzytkownika", description="frajer se juz nie napisze")
    @app_commands.describe(user="Użytkownik",powod="Powód zablokowania")
    async def blokuj_uzytkownika(self, interaction: discord.Interaction,user:discord.User,powod:str):
            if interaction.user.id not in admin_ids:
                await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
                return
            self.lista_zakazanych[str(user.id)] = powod
            save_json(BANNED_DATA, self.lista_zakazanych)
            await interaction.response.send_message(f"Zablokowano {user}. Powod: {powod}",ephemeral=True)
    @app_commands.command(name="odblokuj_uzytkownika", description="udkupiono grzechy, mozna pisac")
    @app_commands.describe(user="Użytkownik")
    async def odblokuj_uzytkownika(self, interaction: discord.Interaction,user:discord.User):
            if interaction.user.id not in admin_ids:
                await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
                return
            if str(user.id) in self.lista_zakazanych:
                del self.lista_zakazanych[str(user.id)]
                save_json(BANNED_DATA, self.lista_zakazanych)
            await interaction.response.send_message(f"Odblokowano {user}",ephemeral=True)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        user_id = str(message.author.id)
        if user_id in self.lista_zakazanych:
            try:
                await message.delete()
                reply = await message.channel.send(
                    f"{message.author.mention}, masz bana na pisanie.\n**Powód:** {self.lista_zakazanych[user_id]}"
                )
                await reply.delete(delay=5)
            except discord.Forbidden:
                print("❌ Brak uprawnień do usunięcia wiadomości lub napisania odpowiedzi.")
            except Exception as e:
                print("⚠️ Błąd w on_message:", e)

async def setup(bot):
    cog = Zakazani(bot)
    await bot.add_cog(cog)