import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

DATA_FILE = "data/cwelometr.json"
CUSTOM_FILE = "data/custom_cwelometr.json"
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

class Cwelometr(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.saved_cwelometr = load_json(DATA_FILE)
        self.custom_cwelometr = load_json(CUSTOM_FILE)

    @app_commands.command(name="cwelometr", description="Sprawdź swój poziom cwelozy")
    async def cwelometr(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id in self.custom_cwelometr:
            await interaction.response.send_message(self.custom_cwelometr[user_id])
            return

        if user_id not in self.saved_cwelometr:
            self.saved_cwelometr[user_id] = random.randint(0, 100)
            save_json(DATA_FILE, self.saved_cwelometr)

        level = self.saved_cwelometr[user_id]
        await interaction.response.send_message(f"{interaction.user.mention} jest w {level}% cwelem")


    @app_commands.command(name="rankingcweli", description="Ranking top 10 największych cweli")
    async def rankingcweli(self, interaction: discord.Interaction):
        ranking = sorted(self.saved_cwelometr.items(), key=lambda x: x[1], reverse=True)

        msg = "**🏆 Ranking Cweli:**\n"
        for i, (uid, val) in enumerate(ranking[:10], start=1):
            user = await self.bot.fetch_user(int(uid))
            msg += f"{i}. {user.name} — {val}%\n"

        await interaction.response.send_message(msg)

    @app_commands.command(name="customcwel", description="Ustaw indywidualny komunikat cwelozy")
    @app_commands.describe(user="Użytkownik", tekst="Tekst do ustawienia", level = "Poziom Cwelozy")
    async def ustawcustomcwela(self, interaction: discord.Interaction, user: discord.User, tekst: str,level: int):
        if interaction.user.id not in admin_ids:
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
            return

        self.custom_cwelometr[str(user.id)] = tekst
        save_json(CUSTOM_FILE, self.custom_cwelometr)
        self.saved_cwelometr[str(user.id)] = level
        save_json(DATA_FILE, self.saved_cwelometr)
        await interaction.response.send_message(f"✅ Zmieniono komunikat cwelozy dla {user.mention}:\n> {tekst}")

    @app_commands.command(name="resetcwela", description="zresetuj dane o cwelowosci uzytkownika")
    @app_commands.describe(user="Użytkownik")
    async def resetcwela(self,interaction: discord.Interaction, user: discord.User):
        if interaction.user.id not in admin_ids:
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
            return
        user_id = str(user.id)

        if user_id in self.saved_cwelometr:
            del self.saved_cwelometr[user_id]
            save_json(DATA_FILE,self.saved_cwelometr)

        if user_id in self.custom_cwelometr:
            del self.custom_cwelometr[user_id]
            save_json(CUSTOM_FILE,self.custom_cwelometr)
        await interaction.response.send_message(f"Pomyślnie zresetowano cwela")
    @app_commands.command(name = "chcezmianycwela",description="nie podoba ci sie twoj poziom?")
    async def chcezmianycwela(self,interaction:discord.Interaction):
        await interaction.response.send_message("Nie podoba ci sie twoj poziom cwelozy?\nChciałbyś żeby ludzie wiedzieli że to ty jesteś największym cwelem?\nNie ma sprawy, za jedyne 9.99 możesz mieć indywidualny komunikat o cwelozie\n[paypal](https://www.paypal.com/paypalme/mrachwalski)", ephemeral=True)
async def setup(bot):
    cog = Cwelometr(bot)
    await bot.add_cog(cog)

