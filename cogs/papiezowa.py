
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime as dt
import asyncio
import pytz
import os
import json
POPE_DATA = "data/kanalpapieski.json"
raw_ids = os.getenv("ADMIN_IDS", "")
admin_ids = [int(id.strip()) for id in raw_ids.split(",") if id.strip()]

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

timezone = pytz.timezone("Europe/Warsaw")
class Papiez(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.pope2137.start()
        self.kanaly_papieskie = load_json(POPE_DATA)
    @app_commands.command(name="kanalpapieski", description="ustaw ten kanal jako papieski")
    @app_commands.describe(czy_pisac="Tak/Nie")
    async def ustaw_kanal_papieski(self, interaction: discord.Interaction, czy_pisac:bool):
        if interaction.user.id not in admin_ids:
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
            return
        channel_id = interaction.channel.id
        if czy_pisac==True:
            if channel_id not in self.kanaly_papieskie:
                self.kanaly_papieskie.append(channel_id)
                save_json(POPE_DATA, self.kanaly_papieskie)
            await interaction.response.send_message(f"{interaction.channel} został kanałem papieskim")
        else:
            if channel_id in self.kanaly_papieskie:
                self.kanaly_papieskie.remove(channel_id)
                save_json(POPE_DATA, self.kanaly_papieskie)
            await interaction.response.send_message(f"{interaction.channel} przestał być kanałem papieskim")

        

    @tasks.loop(minutes=1)
    async def pope2137(self):
        now = dt.datetime.now(timezone)
        if now.hour == 21 and now.minute == 37:
            for channel_id in self.kanaly_papieskie:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send("papiezowa")

    @pope2137.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60 - dt.datetime.now(timezone).second)
async def setup(bot):
    await bot.add_cog(Papiez(bot))
