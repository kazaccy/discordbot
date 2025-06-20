import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
from collections import deque

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(PROJECT_ROOT, "bin", "ffmpeg", "ffmpeg.exe")
COOKIES_FILE = os.getenv("YTDLP_COOKIEFILE", "data/cookies.txt")

class Muzyka(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues: dict[str, deque] = {}

    def get_queue(self, guild_id: str) -> deque:
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    @app_commands.command(name="play", description="Zagraj muzykę z YouTube ")
    @app_commands.describe(song_query="Nazwa lub URL")
    async def play(self, interaction: discord.Interaction, song_query: str):
        voice = interaction.user.voice
        if not voice or not voice.channel:
            return await interaction.response.send_message(
                "❌ Musisz być na kanale głosowym!", ephemeral=True
            )

        await interaction.response.defer()

        guild_id = str(interaction.guild_id)
        vc: discord.VoiceClient = interaction.guild.voice_client
        if vc is None:
            vc = await voice.channel.connect()
        elif vc.channel != voice.channel:
            await vc.move_to(voice.channel)

        ydl_opts = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": False,  
            "cookiefile": COOKIES_FILE,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
        }

 
        is_url = song_query.startswith(("http://", "https://","www."))

        try:
            if is_url:
                info = await self._search_ytdlp_async(song_query, ydl_opts)
            else:
                query = f"ytsearch1:{song_query}"
                info = await self._search_ytdlp_async(query, ydl_opts)
        except Exception as e:
            return await interaction.followup.send(f"❌ Błąd yt_dlp: {e}")

        tracks = []
        if "entries" in info and info["entries"]:
            for entry in info["entries"]:
                if entry:
                    url = entry.get("url")
                    title = entry.get("title","Untitled")
                    tracks.append((url,title))
        else:
            url = info.get("url")
            title = info.get("title","Untitled")
            tracks.append((url,title))
        if not tracks:
            return await interaction.followup.send("Nie znaleziono żadnych utworów")


        queue = self.get_queue(guild_id)
        for url, title in tracks:
            queue.append((url,title))

        if not vc.is_playing() and not vc.is_paused():
            await self._play_next(interaction.channel, vc, guild_id)
        else:
            await interaction.followup.send(f" Dodano do kolejki: **{len(tracks)}**")

    @app_commands.command(name="skip", description="Pomiń aktualny utwór")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ Pominięto utwór.")
        else:
            await interaction.response.send_message("❌ Nic nie jest odtwarzane.", ephemeral=True)

    @app_commands.command(name="pause", description="Wstrzymaj odtwarzanie")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Bot nie jest na kanale.", ephemeral=True)
        if not vc.is_playing():
            return await interaction.response.send_message("❌ Nic nie jest odtwarzane.", ephemeral=True)
        vc.pause()
        await interaction.response.send_message("⏸️ Odtwarzanie wstrzymane.")

    @app_commands.command(name="resume", description="Wznów odtwarzanie")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Bot nie jest na kanale.", ephemeral=True)
        if not vc.is_paused():
            return await interaction.response.send_message("❌ Nie jest wstrzymane.", ephemeral=True)
        vc.resume()
        await interaction.response.send_message("▶️ Odtwarzanie wznowione.")

    @app_commands.command(name="stop", description="Zatrzymaj i wyczyść kolejkę")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        guild_id = str(interaction.guild_id)
        if not vc:
            return await interaction.response.send_message("❌ Bot nie jest na kanale.", ephemeral=True)

        self.get_queue(guild_id).clear()
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("■ Odtwarzanie zatrzymane, bot odłączony.")

    @app_commands.command(name="queue", description="Pokaż nadchodzącą kolejkę")
    async def queue(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        queue = self.get_queue(guild_id)
        if not queue:
            return await interaction.response.send_message("ℹ️ Kolejka jest pusta.", ephemeral=True)
        msg = "**Kolejka odtwarzania:**\n"
        for i, (_, title) in enumerate(queue, start=1):
            msg += f"{i}. {title}\n"
        await interaction.response.send_message(msg, ephemeral=True)

    async def _search_ytdlp_async(self, query, opts):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._extract(query, opts))

    def _extract(self, query, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(query, download=False)

    async def _play_next(self, channel: discord.abc.Messageable, vc: discord.VoiceClient, guild_id: str):
        queue = self.get_queue(guild_id)
        if not queue:
            await vc.disconnect()
            return

        audio_url, title = queue.popleft()
        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_opts, executable=FFMPEG_PATH)

        def _after_play(err):
            if err:
                print(f"❌ Błąd odtwarzania {title}: {err}")
            fut = self._play_next(channel, vc, guild_id)
            asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

        vc.play(source, after=_after_play)
        await channel.send(f"▶️ Teraz gra: **{title}**")

async def setup(bot):
    await bot.add_cog(Muzyka(bot))
