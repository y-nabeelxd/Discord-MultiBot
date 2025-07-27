import os
import re
import yt_dlp
import discord
import asyncio
import random
import datetime
import logging
from samp_query import Client
from discord.ext import commands
from urllib.parse import quote
import json
import requests
import sys
import time
from datetime import timedelta
import aiohttp
import socket
import struct

# --- Configuration ---
# Verification system settings
VERIFICATION_FIVEM = False
VERIFICATION_VALO = False
VERIFICATION_SAMP = True
VERIFICATION_ROBLOX = True
CHANGE_NICKNAME = False
RIOT_API_KEY = None
FIVEM_SERVER = None  # Set your FiveM server IP:PORT
SAMP_SERVER_IP = None
SAMP_SERVER_PORT = None
VALORANT_ROLE_ID = None
FIVEM_ROLE_ID = None
SAMP_ROLE_ID = None
ROBLOX_ROLE_ID = None

REGIONS = ["americas", "europe", "asia"]  # For Valorant API

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_duration(seconds):
    if isinstance(seconds, str):
        return seconds
    try:
        seconds = int(seconds)
        return str(timedelta(seconds=seconds))
    except:
        return "N/A"

def beautiful_print(message, box_char="═", padding=1):
    terminal_width = os.get_terminal_size().columns
    box_line = box_char * terminal_width
    padding_lines = "\n" * padding
    message_lines = message.split('\n')
    
    centered_message = []
    for line in message_lines:
        if line.strip():
            centered_line = line.center(terminal_width)
            centered_message.append(centered_line)
        else:
            centered_message.append('')
    
    print(f"{padding_lines}{box_line}\n" + "\n".join(centered_message) + f"\n{box_line}{padding_lines}")

async def query_samp(ip: str, port: int):
    """Query SA-MP server using samp-query library"""
    try:
        client = Client(ip=ip, port=port)
        info = await client.info()
        players = await client.players()
        return [player.name for player in players.players]
    except Exception as e:
        print(f"Error querying SA-MP server: {str(e)}")
        return None

async def get_valorant_account(username: str, tag: str):
    if not RIOT_API_KEY:
        return None
        
    async with aiohttp.ClientSession() as session:
        for region in REGIONS:
            url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}"
            headers = {"X-Riot-Token": RIOT_API_KEY}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
    return None

async def get_fivem_players():
    if not FIVEM_SERVER:
        return []
        
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{FIVEM_SERVER}/players.json") as resp:
            if resp.status == 200:
                return await resp.json()
    return []

async def get_roblox_profile(username: str):
    """Get Roblox profile information"""
    try:
        url = "https://users.roblox.com/v1/usernames/users"
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url, json={"usernames": [username]})
            resp_data = await resp.json()
        
            if "data" not in resp_data or not resp_data["data"]:
                return None
                
            user_id = resp_data["data"][0]["id"]
            
            profile_url = f"https://users.roblox.com/v1/users/{user_id}"
            async with session.get(profile_url) as profile_resp:
                profile_data = await profile_resp.json()
            
            avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
            async with session.get(avatar_url) as avatar_resp:
                avatar_data = await avatar_resp.json()
            avatar = avatar_data["data"][0]["imageUrl"]
            
            friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
            async with session.get(friends_url) as friends_resp:
                friends_data = await friends_resp.json()
            friends_count = friends_data.get("count", 0)
            
            created = profile_data.get("created")
            if created:
                created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%B %d, %Y")
            
            return {
                "id": user_id,
                "username": profile_data.get("name"),
                "displayName": profile_data.get("displayName"),
                "description": profile_data.get("description", ""),
                "created": created,
                "avatar": avatar,
                "friends": friends_count
            }
    except Exception as e:
        print(f"Error getting Roblox profile: {e}")
        return None

async def send_to_owner(guild: discord.Guild, embed: discord.Embed):
    try:
        await guild.owner.send(embed=embed)
    except Exception as e:
        print(f"Could not DM owner: {e}")

PREFIX = "!"
intents = discord.Intents.all()

discord.utils.setup_logging(level=logging.INFO, root=False)
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)

class MyBot(commands.Bot):
    async def on_connect(self):
        clear_console()
        beautiful_print("🔌 Connecting to Discord Bot...", "─")
    
    async def on_ready(self):
        clear_console()
        login_msg = f"""
🤖 Connected to {self.user.name}
🆔 ID: {self.user.id}
⚡ Prefix: "{PREFIX}"
🔒 Verification Systems:
  • Valorant: {'✅ Enabled' if VERIFICATION_VALO and RIOT_API_KEY and VALORANT_ROLE_ID else '❌ Disabled'}
  • FiveM: {'✅ Enabled' if VERIFICATION_FIVEM and FIVEM_SERVER and FIVEM_ROLE_ID else '❌ Disabled'}
  • SA-MP: {'✅ Enabled' if VERIFICATION_SAMP and SAMP_SERVER_IP and SAMP_SERVER_PORT and SAMP_ROLE_ID else '❌ Disabled'}
  • Roblox: {'✅ Enabled' if VERIFICATION_ROBLOX and ROBLOX_ROLE_ID else '❌ Disabled'}
        """
        beautiful_print(login_msg, "═")
        await self.change_presence(activity=discord.Game(name=f"Music | {PREFIX}help"))

bot = MyBot(command_prefix=PREFIX, intents=intents, help_command=None)

queues = {}
current_players = {}
song_queues = {}
idle_timers = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': True,
    'verbose': False
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel error',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = format_duration(data.get('duration'))
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def check_empty_vc(guild_id):
    if guild_id not in current_players:
        return True
    
    voice_client = current_players[guild_id]['voice_client']
    if not voice_client or not voice_client.is_connected():
        return True
    
    if len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        if guild_id in current_players:
            if 'control_message' in current_players[guild_id]:
                try:
                    await current_players[guild_id]['control_message'].delete()
                except:
                    pass
            del current_players[guild_id]
        if guild_id in song_queues:
            song_queues[guild_id].clear()
        return True
    return False

async def start_idle_timer(guild_id):
    if guild_id in idle_timers:
        idle_timers[guild_id].cancel()
    
    async def idle_task():
        try:
            start_time = time.time()
            while time.time() - start_time < 30:
                if guild_id in current_players and current_players[guild_id]['voice_client'].is_playing():
                    return
                await asyncio.sleep(1)
            
            if guild_id in current_players:
                voice_client = current_players[guild_id]['voice_client']
                if voice_client and not voice_client.is_playing():
                    await check_empty_vc(guild_id)
        except Exception as e:
            print(f"Error in idle timer: {e}")
    
    idle_timers[guild_id] = asyncio.create_task(idle_task())

# --- Verification Commands ---
class RobloxConfirmationView(discord.ui.View):
    """View for Roblox account confirmation"""
    def __init__(self, ctx, profile):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.profile = profile
        self.confirmed = None
    
    @discord.ui.button(label="✅ It's Me", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        
        self.confirmed = True
        self.stop()
        await interaction.message.delete()
        await interaction.response.send_message("✅ Verification process started! Please check your messages.", ephemeral=True)
    
    @discord.ui.button(label="❌ Not Me", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        
        self.confirmed = False
        self.stop()
        await interaction.message.delete()
        await interaction.response.send_message("❌ Account verification cancelled. Please try again with the correct username.", ephemeral=True)

@bot.command()
async def sampstatus(ctx):
    """Check SA-MP server status"""
    try:
        players = await query_samp(SAMP_SERVER_IP, SAMP_SERVER_PORT)
        if players is None:
            return await ctx.send("🔴 Server offline or unreachable")
            
        client = Client(ip=SAMP_SERVER_IP, port=SAMP_SERVER_PORT)
        info = await client.info()
        
        embed = discord.Embed(
            title=f"SA-MP Server: {info.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Players", value=f"{len(players)}/{info.max_players}", inline=True)
        embed.add_field(name="Gamemode", value=info.game_mode, inline=True)
        embed.add_field(name="Address", value=f"{SAMP_SERVER_IP}:{SAMP_SERVER_PORT}", inline=False)
        
        if players:
            player_list = "\n".join(players[:10])
            more = f"\n...and {len(players)-10} more" if len(players) > 10 else ""
            embed.add_field(name="Online Players", value=f"{player_list}{more}", inline=False)
            
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"🔴 Error checking server status: {str(e)}")

@bot.command()
async def verifyroblox(ctx, *, username: str):
    """Verify your Roblox account. Usage: !verifyroblox <username>"""
    if not VERIFICATION_ROBLOX:
        return await ctx.send("❌ Roblox verification is currently disabled.", delete_after=10)
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    msg = await ctx.send("🔍 Fetching Roblox profile...")
    profile = await get_roblox_profile(username)
    
    if not profile:
        await msg.edit(content="❌ Couldn't find that Roblox username. Please check the spelling and try again.")
        return
    
    embed = discord.Embed(
        title="🔎 Is this your Roblox account?",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=profile['avatar'])
    embed.add_field(name="Username", value=profile['username'], inline=True)
    embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
    embed.add_field(name="Account Created", value=profile['created'], inline=True)
    embed.add_field(name="Friends", value=f"{profile['friends']:,}", inline=True)
    embed.add_field(name="Description", value=profile['description'][:500] + ("..." if len(profile['description']) > 500 else "") or "No description", inline=False)
    embed.set_footer(text="Please confirm this is your account to continue verification")
    
    view = RobloxConfirmationView(ctx, profile)
    await msg.edit(content=None, embed=embed, view=view)
    
    await view.wait()
    
    if view.confirmed is None:
        await msg.edit(content="⏳ Verification timed out. Please try again.", view=None)
        return
    elif not view.confirmed:
        return
    
    code = f"Verify-{random.randint(10000, 99999)}"
    
    try:
        embed = discord.Embed(
            title="🔑 Roblox Verification",
            description=f"To verify your Roblox account **{profile['username']}**, please:\n\n"
                       f"1. Copy this verification code:\n"
                       f"```\n{code}\n```\n"
                       f"2. Paste it into your Roblox profile description\n"
                       f"3. The bot will automatically check for the code\n\n"
                       f"You have **2 minutes** to complete this.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="The bot will automatically detect when you've added the code")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Copy Verification Code",
            style=discord.ButtonStyle.primary,
            custom_id="copy_code",
            emoji="📋"
        ))
        
        dm_msg = await ctx.author.send(embed=embed, view=view)
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention} I couldn't send you a DM. Please enable DMs and try again.", delete_after=15)
        return
    
    await ctx.send(f"{ctx.author.mention} Check your DMs for verification instructions!", delete_after=15)
    
    original_desc = profile['description']
    
    start_time = time.time()
    verified = False
    
    while time.time() - start_time < 120:  # 2 minutes
        await asyncio.sleep(5)
        
        current_profile = await get_roblox_profile(username)
        if not current_profile:
            await ctx.author.send("❌ Couldn't fetch your Roblox profile anymore. Verification failed.")
            return
        
        if current_profile['description'] != original_desc:
            if code in current_profile['description']:
                verified = True
                break
            else:
                await ctx.author.send("❌ I found a description change but it doesn't contain the correct verification code. Please try again.")
                return
    
    if not verified:
        await ctx.author.send("⏳ Verification timed out. You didn't add the code in time.")
        return
    
    role = None
    if ROBLOX_ROLE_ID:
        role = ctx.guild.get_role(ROBLOX_ROLE_ID)
    else:
        for r in ctx.guild.roles:
            if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                role = r
                break
    
    if not role:
        await ctx.author.send("❌ Verification failed: No valid role found to assign. Please contact server staff.")
        return
    
    try:
        await ctx.author.add_roles(role)
        
        if CHANGE_NICKNAME:
            try:
                await ctx.author.edit(nick=profile['username'])
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"You've been verified as Roblox user **{profile['username']}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Username", value=profile['username'], inline=True)
        embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
        embed.set_thumbnail(url=profile['avatar'])
        
        await ctx.author.send(embed=embed)
        
        embed = discord.Embed(
            title="✅ Roblox Verification Complete",
            description=f"{ctx.author.mention} has been verified as Roblox user **{profile['username']}**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=profile['avatar'])
        await ctx.send(embed=embed)
        
        owner_embed = discord.Embed(
            title="Roblox Verification",
            description=f"{ctx.author} verified as {profile['username']}",
            color=discord.Color.blue()
        )
        owner_embed.add_field(name="Roblox Username", value=profile['username'], inline=True)
        owner_embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
        owner_embed.add_field(name="User ID", value=profile['id'], inline=False)
        owner_embed.set_thumbnail(url=profile['avatar'])
        await send_to_owner(ctx.guild, owner_embed)
        
    except Exception as e:
        await ctx.author.send(f"❌ Verification failed: {str(e)}")
        await ctx.send(f"❌ Failed to complete verification for {ctx.author.mention}. Please contact staff.", delete_after=15)

@bot.command()
async def verifyvalo(ctx, *, riotid: str):
    """Verify a Valorant account. Usage: !verifyvalo Username#Tag"""
    if not VERIFICATION_VALO:
        return
        
    if not RIOT_API_KEY:
        return await ctx.reply("❌ Valorant verification is currently disabled.")
    
    if "#" not in riotid:
        return await ctx.reply("❌ Invalid Riot ID. Use `Username#Tag` format.")
    
    username, tag = riotid.split("#", 1)
    msg = await ctx.reply("🔍 Verifying your Valorant account...")
    account = await get_valorant_account(username, tag)
    if not account:
        return await msg.edit(content="❌ Account not found in any region!")
    
    role = None
    if VALORANT_ROLE_ID:
        role = ctx.guild.get_role(VALORANT_ROLE_ID)
    else:
        for r in ctx.guild.roles:
            if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                role = r
                break
    
    if not role:
        return await msg.edit(content="❌ No valid role found to assign!")
    
    await ctx.author.add_roles(role)
    
    if CHANGE_NICKNAME:
        try:
            await ctx.author.edit(nick=f"{account['gameName']}#{account['tagLine']}")
        except discord.Forbidden:
            pass
    
    embed = discord.Embed(title="Valorant Verification Successful ✅", color=0x00ff88)
    embed.add_field(name="Username", value=f"{account['gameName']}#{account['tagLine']}", inline=True)
    embed.add_field(name="PUUID", value=account['puuid'], inline=False)
    embed.set_footer(text=f"Verified by {ctx.author}")

    await msg.edit(content=None, embed=embed)
    await send_to_owner(ctx.guild, embed)

@bot.command()
async def verifyfivem(ctx, *, playername: str):
    """Verify a FiveM account. Usage: !verifyfivem PlayerName"""
    if not VERIFICATION_FIVEM:
        return
        
    if not FIVEM_SERVER:
        return await ctx.reply("❌ FiveM verification is currently disabled.")
    
    msg = await ctx.reply("🔍 Checking FiveM server...")
    players = await get_fivem_players()
    player = next((p for p in players if p['name'].lower() == playername.lower()), None)
    if not player:
        return await msg.edit(content="❌ You are not currently online on the FiveM server!")
    
    role = None
    if FIVEM_ROLE_ID:
        role = ctx.guild.get_role(FIVEM_ROLE_ID)
    else:
        for r in ctx.guild.roles:
            if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                role = r
                break
    
    if not role:
        return await msg.edit(content="❌ No valid role found to assign!")
    
    await ctx.author.add_roles(role)
    
    if CHANGE_NICKNAME:
        try:
            await ctx.author.edit(nick=player['name'])
        except discord.Forbidden:
            pass
    
    identifiers = "\n".join(player.get("identifiers", []))
    ping = player.get("ping", "N/A")

    embed = discord.Embed(title="FiveM Verification Successful ✅", color=0x00aaff)
    embed.add_field(name="Player Name", value=player['name'], inline=True)
    embed.add_field(name="Ping", value=str(ping), inline=True)
    embed.add_field(name="Identifiers", value=identifiers or "No identifiers", inline=False)
    embed.set_footer(text=f"Verified by {ctx.author}")

    await msg.edit(content=None, embed=embed)
    await send_to_owner(ctx.guild, embed)

@bot.command()
async def verifysamp(ctx, *, playername: str):
    """Verify a SA-MP account. Usage: !verifysamp PlayerName"""
    if not VERIFICATION_SAMP:
        return await ctx.reply("❌ SA-MP verification is currently disabled.")
    
    if not SAMP_SERVER_IP or not SAMP_SERVER_PORT:
        return await ctx.reply("❌ SA-MP verification is not properly configured.")
    
    msg = await ctx.reply(f"🔍 Checking SA-MP server at {SAMP_SERVER_IP}:{SAMP_SERVER_PORT}...")
    
    try:
        players = await query_samp(SAMP_SERVER_IP, SAMP_SERVER_PORT)
        
        if players is None:
            return await msg.edit(content="❌ Could not connect to the SA-MP server. Please ensure:\n"
                                      "1. The server is online\n"
                                      "2. The IP and port are correct\n"
                                      "3. The server allows connections from this bot")
        
        player = next((p for p in players if p.lower() == playername.lower()), None)
        
        if not player:
            player_list = "\n".join(players[:10])
            more = f"\n...and {len(players)-10} more" if len(players) > 10 else ""
            return await msg.edit(content=f"❌ Could not find '{playername}' on the server.\n\nCurrent players:\n{player_list}{more}")
        
        role = None
        if SAMP_ROLE_ID:
            role = ctx.guild.get_role(SAMP_ROLE_ID)
        else:
            for r in ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                    role = r
                    break
        
        if not role:
            return await msg.edit(content="❌ No valid role found to assign!")
        
        await ctx.author.add_roles(role)
        
        if CHANGE_NICKNAME:
            try:
                await ctx.author.edit(nick=player)
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="✅ SA-MP Verification Successful",
            description=f"{ctx.author.mention} has been verified as `{player}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Server", value=f"{SAMP_SERVER_IP}:{SAMP_SERVER_PORT}", inline=False)
        embed.set_footer(text=f"Verified at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        await msg.edit(content=None, embed=embed)
        
        owner_embed = discord.Embed(
            title="SA-MP Verification Log",
            description=f"{ctx.author} verified as {player}",
            color=discord.Color.blue()
        )
        await send_to_owner(ctx.guild, owner_embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ An error occurred: {str(e)}")

# --- Music Player Commands ---
class SongSelect(discord.ui.Select):
    def __init__(self, results, ctx):
        self.results = results
        self.ctx = ctx
        
        options = [
            discord.SelectOption(
                label=f"{idx+1}. {video['title'][:90]}",
                description=f"{video.get('duration', 'N/A')}",
                value=str(idx)
            ) for idx, video in enumerate(results[:10])
        ]
        
        super().__init__(
            placeholder="Select a song to play...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You didn't request this song selection!", ephemeral=True)
        
        selected = int(self.values[0])
        video_url = self.results[selected]['url']
        song_title = self.results[selected]['title']
        
        await interaction.response.defer()
        await interaction.message.delete()
        
        voice_client = self.ctx.voice_client
        
        if self.ctx.guild.id not in song_queues:
            song_queues[self.ctx.guild.id] = []
        
        if voice_client.is_playing() or voice_client.is_paused():
            song_queues[self.ctx.guild.id].append({'url': video_url, 'title': song_title})
            await self.ctx.send(f"Added to queue: **{song_title}**")
        else:
            await play_song(self.ctx, video_url, song_title)

class SongSelectView(discord.ui.View):
    def __init__(self, results, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.add_item(SongSelect(results, ctx))
    
    async def on_timeout(self):
        try:
            await self.message.delete()
        except:
            pass

class ControlButtons(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
    
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸ Playback paused", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label="Resume", style=discord.ButtonStyle.primary, emoji="▶️")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶ Playback resumed", ephemeral=True)
        else:
            await interaction.response.send_message("Playback is not paused!", ephemeral=True)
    
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await interaction.response.send_message("⏭️ Song skipped", ephemeral=True)
            await play_next(self.ctx)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="🛑")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client:
            if interaction.guild.id in song_queues:
                song_queues[interaction.guild.id].clear()
            if interaction.guild.id in current_players:
                if 'control_message' in current_players[interaction.guild.id]:
                    try:
                        await current_players[interaction.guild.id]['control_message'].delete()
                    except:
                        pass
                del current_players[interaction.guild.id]
            await voice_client.disconnect()
            await interaction.response.send_message("⏹ Playback stopped and queue cleared", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)

async def play_next(ctx):
    if ctx.guild.id in song_queues and song_queues[ctx.guild.id]:
        next_song = song_queues[ctx.guild.id].pop(0)
        await play_song(ctx, next_song['url'], next_song['title'])
    else:
        await start_idle_timer(ctx.guild.id)

async def play_song(ctx, url, title):
    voice_client = ctx.voice_client
    
    if ctx.guild.id in idle_timers:
        idle_timers[ctx.guild.id].cancel()
    
    try:
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        
        current_players[ctx.guild.id] = {
            'voice_client': voice_client,
            'player': player,
            'ctx': ctx,
            'last_activity': time.time()
        }
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{player.title}]({url})",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=player.thumbnail)
        
        if player.duration:
            embed.add_field(name="Duration", value=player.duration, inline=True)
            
        view = ControlButtons(ctx)
        control_message = await ctx.send(embed=embed, view=view)
        
        current_players[ctx.guild.id]['control_message'] = control_message
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            
        voice_client.play(player, after=after_playing)
        
    except Exception as e:
        await ctx.send(f"Error playing song: {e}")
        await play_next(ctx)

def search_youtube(query):
    search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print("Failed to fetch YouTube results")
            return []
        
        html = response.text
        initial_data = {}
        try:
            start = html.index('var ytInitialData = ') + len('var ytInitialData = ')
            end = html.index('};</script>', start) + 1
            json_str = html[start:end]
            initial_data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            print("Failed to parse YouTube data:", e)
            return []
        
        videos = []
        contents = initial_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [])
        
        for content in contents:
            if 'videoRenderer' in content:
                video = content['videoRenderer']
                video_id = video.get('videoId')
                title = video.get('title', {}).get('runs', [{}])[0].get('text')
                duration_text = video.get('lengthText', {}).get('simpleText', '')
                
                if video_id and title:
                    videos.append({
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'duration': duration_text,
                        'thumbnail': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                    })
                if len(videos) >= 10:
                    break
        return videos
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

@bot.command(aliases=['p'])
async def play(ctx, *, query: str):
    """Play a song or add to queue. Usage: !play <song name/url>"""
    voice_client = ctx.voice_client
    
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to play music!")
        return
    
    if voice_client and voice_client.is_connected():
        if voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
    else:
        voice_client = await ctx.author.voice.channel.connect()
    
    if ctx.guild.id in idle_timers:
        idle_timers[ctx.guild.id].cancel()
    
    results = search_youtube(query)
    if not results:
        await ctx.send("No results found!")
        return
    
    embed = discord.Embed(title="🔍 Search Results", description=f"Results for: {query}", color=0x00ff00)
    for idx, video in enumerate(results[:10], 1):
        embed.add_field(
            name=f"{idx}. {video['title']}",
            value=f"Duration: {video.get('duration', 'N/A')}",
            inline=False
        )
    
    view = SongSelectView(results, ctx)
    view.message = await ctx.send(embed=embed, view=view)

@bot.command()
async def skip(ctx):
    """Skip the current song. Usage: !skip"""
    voice_client = ctx.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("⏭️ Song skipped")
        await play_next(ctx)
    else:
        await ctx.send("Nothing is playing to skip!")

@bot.command()
async def queue(ctx):
    """Show the current queue. Usage: !queue"""
    if ctx.guild.id in song_queues and song_queues[ctx.guild.id]:
        queue_list = [f"{idx+1}. {song['title']}" for idx, song in enumerate(song_queues[ctx.guild.id])]
        embed = discord.Embed(
            title="🎶 Current Queue",
            description="\n".join(queue_list),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def clearqueue(ctx):
    """Clear the current queue. Usage: !clearqueue"""
    if ctx.guild.id in song_queues:
        song_queues[ctx.guild.id].clear()
        await ctx.send("Queue cleared!")
    else:
        await ctx.send("The queue is already empty.")

@bot.command()
async def pause(ctx):
    """Pause the current song. Usage: !pause"""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸ Playback paused")
    else:
        await ctx.send("Nothing is playing!")

@bot.command()
async def resume(ctx):
    """Resume the current song. Usage: !resume"""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶ Playback resumed")
    else:
        await ctx.send("Playback is not paused!")

@bot.command()
async def stop(ctx):
    """Stop playback and clear queue. Usage: !stop"""
    voice_client = ctx.voice_client
    if voice_client:
        if ctx.guild.id in song_queues:
            song_queues[ctx.guild.id].clear()
        if ctx.guild.id in current_players:
            if 'control_message' in current_players[ctx.guild.id]:
                try:
                    await current_players[ctx.guild.id]['control_message'].delete()
                except:
                    pass
            del current_players[ctx.guild.id]
        await voice_client.disconnect()
        await ctx.send("⏹ Playback stopped and queue cleared")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def leave(ctx):
    """Make the bot leave the voice channel. Usage: !leave"""
    await stop(ctx)

# --- Moderation Commands ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server. Usage: !ban @user [reason]"""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned by {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to ban member: {e}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server. Usage: !kick @user [reason]"""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked by {ctx.author.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to kick member: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def timeout(ctx, member: discord.Member, duration: str, *, reason="No reason provided"):
    """Timeout a member (format: 1h, 30m, 2d). Usage: !timeout @user 30m [reason]"""
    try:
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        duration_lower = duration.lower()
        if duration_lower[-1] not in time_units:
            raise ValueError("Invalid time unit. Use s, m, h, or d")
        
        time_value = int(duration_lower[:-1])
        time_unit = duration_lower[-1]
        seconds = time_value * time_units[time_unit]
        
        timeout_duration = datetime.timedelta(seconds=seconds)
        await member.timeout(timeout_duration, reason=reason)
        
        embed = discord.Embed(
            title="⏳ Member Timed Out",
            description=f"{member.mention} has been timed out by {ctx.author.mention}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Duration", value=duration)
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to timeout member: {e}\nUsage: `{PREFIX}timeout @user 30m [reason]`")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, duration: str):
    """Set slowmode for the channel (format: 1h, 30m, 2d). Usage: !slowmode 30s"""
    try:
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        duration_lower = duration.lower()
        if duration_lower[-1] not in time_units:
            raise ValueError("Invalid time unit. Use s, m, h, or d")
        
        time_value = int(duration_lower[:-1])
        time_unit = duration_lower[-1]
        seconds = time_value * time_units[time_unit]
        
        if seconds > 21600:
            await ctx.send("Slowmode cannot be longer than 6 hours!")
            return
        
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏳ Slowmode set to {duration} in this channel.")
    except Exception as e:
        await ctx.send(f"❌ Failed to set slowmode: {e}\nUsage: `{PREFIX}slowmode 30s`")

@bot.command(aliases=['nick'])
@commands.has_permissions(manage_nicknames=True)
async def setnick(ctx, member: discord.Member, *, nickname: str):
    """Set a member's nickname. Usage: !setnick @user NewNickname"""
    try:
        old_nick = member.display_name
        await member.edit(nick=nickname)
        embed = discord.Embed(
            title="📝 Nickname Changed",
            description=f"{member.mention}'s nickname has been updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Before", value=old_nick, inline=True)
        embed.add_field(name="After", value=nickname, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to change nickname: {e}")

@bot.command()
async def getroles(ctx, member: discord.Member = None):
    """Get a member's roles. Usage: !getroles [@user]"""
    target = member or ctx.author
    roles = [role.mention for role in target.roles if role.name != "@everyone"]
    
    if not roles:
        await ctx.send(f"{target.display_name} has no roles.")
        return
    
    embed = discord.Embed(
        title=f"🎭 Roles for {target.display_name}",
        description=" ".join(roles),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role: discord.Role):
    """Add a role to a member. Usage: !addrole @user @Role"""
    try:
        if role in member.roles:
            await ctx.send(f"{member.display_name} already has the {role.name} role!")
            return
            
        await member.add_roles(role)
        embed = discord.Embed(
            title="➕ Role Added",
            description=f"{role.mention} has been added to {member.mention}",
            color=role.color
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to add role: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role: discord.Role):
    """Remove a role from a member. Usage: !removerole @user @Role"""
    try:
        if role not in member.roles:
            await ctx.send(f"{member.display_name} doesn't have the {role.name} role!")
            return
            
        await member.remove_roles(role)
        embed = discord.Embed(
            title="➖ Role Removed",
            description=f"{role.mention} has been removed from {member.mention}",
            color=role.color
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to remove role: {e}")

# --- Game Commands ---
@bot.command(aliases=['rockpaperscissors'])
async def rps(ctx, choice: str):
    """Play Rock Paper Scissors. Usage: !rps rock|paper|scissors"""
    choices = ["rock", "paper", "scissors"]
    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    bot_choice = random.choice(choices)
    user_choice = choice.lower()
    
    if user_choice not in choices:
        await ctx.send("Please choose rock, paper, or scissors!")
        return
    
    if user_choice == bot_choice:
        result = "It's a tie! 🤝"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win! 🎉"
    else:
        result = "I win! 😎"
    
    embed = discord.Embed(
        title="🪨 📄 ✂️ Rock Paper Scissors",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Your Choice", value=f"{emojis[user_choice]} {user_choice.capitalize()}", inline=True)
    embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}", inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    await ctx.send(embed=embed)

@bot.command(aliases=['dice'])
async def roll(ctx, dice: str = "1d6"):
    """Roll dice in NdN format (e.g., 2d20). Usage: !roll 2d20"""
    try:
        rolls, limit = map(int, dice.split('d'))
        if rolls > 20 or limit > 100:
            await ctx.send("Maximum 20 dice with 100 sides each!")
            return
            
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling {dice}",
            color=discord.Color.random()
        )
        embed.add_field(name="Results", value=", ".join(map(str, results)), inline=True)
        embed.add_field(name="Total", value=total, inline=True)
        
        if rolls == 1 and limit == 20:
            if results[0] == 20:
                embed.set_footer(text="Nat 20! Critical success! 🎯")
            elif results[0] == 1:
                embed.set_footer(text="Critical fail! 💀")
        
        await ctx.send(embed=embed)
    except Exception:
        await ctx.send(f'Format must be NdN! Example: `{PREFIX}roll 2d20`')

@bot.command(aliases=['flip'])
async def coinflip(ctx):
    """Flip a coin. Usage: !coinflip"""
    result = random.choice(["Heads", "Tails"])
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"The coin landed on... **{result}**!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, number: int):
    """Guess a number between 1 and 10. Usage: !guess 5"""
    if number < 1 or number > 10:
        await ctx.send("Please guess a number between 1 and 10!")
        return
        
    secret = random.randint(1, 10)
    if number == secret:
        message = f"🎉 Congratulations! You guessed it! The number was {secret}."
        color = discord.Color.green()
    else:
        message = f"❌ Sorry, the number was {secret}. Try again!"
        color = discord.Color.red()
    
    embed = discord.Embed(
        title="🔢 Number Guessing Game",
        description=message,
        color=color
    )
    await ctx.send(embed=embed)

# --- Fun Commands ---
@bot.command()
async def slap(ctx, member: discord.Member):
    """Slap someone! Usage: !slap @user"""
    gif_url = "https://c.tenor.com/XiYuU9h44-AAAAAC/tenor.gif"
    reactions = ["(╯°□°）╯︵ ┻━┻", "⊙﹏⊙", "(ﾉ｀Д´)ﾉ", "ಠ_ಠ", "(•̀o•́)ง"]
    
    embed = discord.Embed(
        color=discord.Color.red()
    )
    embed.set_author(name=f"{ctx.author.display_name} slapped {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def kiss(ctx, member: discord.Member):
    """Kiss someone! Usage: !kiss @user"""
    gif_url = "https://www.icegif.com/wp-content/uploads/2022/08/icegif-1235.gif"
    reactions = ["(づ￣ ³￣)づ", "(*˘︶˘*).｡.:*♡", "(っ˘ω˘ς )", "♡(˃͈ દ ˂͈ ༶ )", "(´∀｀)♡"]
    
    embed = discord.Embed(
        color=discord.Color.pink()
    )
    embed.set_author(name=f"{ctx.author.display_name} kissed {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def hug(ctx, member: discord.Member):
    """Hug someone! Usage: !hug @user"""
    gif_url = "https://usagif.com/wp-content/uploads/gif/anime-hug-59.gif"
    reactions = ["(⊃｡•́‿•̀｡)⊃", "(っ´▽｀)っ", "⊂((・▽・))⊃", "(つ≧▽≦)つ", "╰(*´︶`*)╯"]
    
    embed = discord.Embed(
        color=discord.Color.gold()
    )
    embed.set_author(name=f"{ctx.author.display_name} hugged {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, question: str, *options: str):
    """Create a poll. Usage: !poll "Question" "Option1" "Option2" ..."""
    if len(options) < 2:
        return await ctx.send("Please provide at least 2 options for the poll.")
    if len(options) > 10:
        return await ctx.send("You can only have up to 10 options.")
    
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    description = []
    for i, option in enumerate(options):
        description.append(f"{emojis[i]} {option}")
    
    embed = discord.Embed(
        title=f"📊 Poll: {question}",
        description="\n".join(description),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Poll created by {ctx.author.display_name}")
    
    message = await ctx.send(embed=embed)
    
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Get a user's avatar. Usage: !avatar [@user]"""
    target = member or ctx.author
    embed = discord.Embed(
        title=f"{target.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=target.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Get server information. Usage: !serverinfo"""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"Server Info: {guild.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Channels", value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Get user information. Usage: !userinfo [@user]"""
    target = member or ctx.author
    embed = discord.Embed(
        title=f"User Info: {target.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.avatar.url)
    
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
    embed.add_field(name="Created", value=target.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Joined", value=target.joined_at.strftime("%B %d, %Y"), inline=True)
    
    roles = [role.mention for role in target.roles if role.name != "@everyone"]
    embed.add_field(
        name=f"Roles ({len(roles)})", 
        value=" ".join(roles) if roles else "None", 
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def remind(ctx, time: str, *, reminder: str):
    """Set a reminder. Usage: !remind 1h30m Do homework"""
    try:
        seconds = 0
        time_lower = time.lower()
        
        if 'd' in time_lower:
            days = int(time_lower.split('d')[0])
            seconds += days * 86400
            time_lower = time_lower.split('d')[1]
        if 'h' in time_lower:
            hours = int(time_lower.split('h')[0])
            seconds += hours * 3600
            time_lower = time_lower.split('h')[1]
        if 'm' in time_lower:
            minutes = int(time_lower.split('m')[0])
            seconds += minutes * 60
            time_lower = time_lower.split('m')[1]
        if 's' in time_lower:
            secs = int(time_lower.split('s')[0])
            seconds += secs
        
        if seconds <= 0:
            return await ctx.send("Please provide a valid time greater than 0 seconds.")
        
        await ctx.send(f"⏰ I'll remind you in {time} about: {reminder}")
        
        await asyncio.sleep(seconds)
        
        embed = discord.Embed(
            title="⏰ Reminder",
            description=reminder,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"You set this reminder {time} ago")
        
        await ctx.author.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to set reminder: {e}\nUsage: `{PREFIX}remind 1h30m Do homework`")

# --- Help Command ---
class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            'help': 'Shows help about the bot, a command, or a category'
        })

    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed(
            title=f"{bot.user.name} Help",
            description=f"Use `{PREFIX}help <command>` for more info on a command.",
            color=discord.Color.blue()
        )
        
        # Music commands
        music_commands = [
            'play', 'skip', 'queue', 'clearqueue', 
            'pause', 'resume', 'stop', 'leave'
        ]
        music_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in music_commands)
        embed.add_field(name="🎵 Music Commands", value=music_desc, inline=False)
        
        # Verification commands
        verification_commands = []
        if VERIFICATION_VALO and RIOT_API_KEY:
            verification_commands.append('verifyvalo')
        if VERIFICATION_FIVEM and FIVEM_SERVER:
            verification_commands.append('verifyfivem')
        if VERIFICATION_SAMP and SAMP_SERVER_IP and SAMP_SERVER_PORT:
            verification_commands.append('verifysamp')
        if VERIFICATION_ROBLOX:
            verification_commands.append('verifyroblox')
            
        if verification_commands:
            verif_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in verification_commands)
            embed.add_field(name="🔒 Verification Commands", value=verif_desc, inline=False)
        
        # Moderation commands
        mod_commands = [
            'ban', 'kick', 'timeout', 'slowmode',
            'setnick', 'addrole', 'removerole', 'getroles'
        ]
        mod_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in mod_commands)
        embed.add_field(name="🛡️ Moderation Commands", value=mod_desc, inline=False)
        
        # Game commands
        game_commands = ['rps', 'roll', 'coinflip', 'guess']
        game_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in game_commands)
        embed.add_field(name="🎮 Game Commands", value=game_desc, inline=False)
        
        # Fun commands
        fun_commands = ['slap', 'kiss', 'hug']
        fun_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in fun_commands)
        embed.add_field(name="😂 Fun Commands", value=fun_desc, inline=False)
        
        # Utility commands
        utility_commands = ['poll', 'avatar', 'serverinfo', 'userinfo', 'remind']
        utility_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in utility_commands)
        embed.add_field(name="🔧 Utility Commands", value=utility_desc, inline=False)
        
        await ctx.send(embed=embed)

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(
            title=f"Command: {PREFIX}{command.name}",
            description=command.help or "No description available",
            color=discord.Color.green()
        )
        
        if command.help and "Usage:" in command.help:
            usage = command.help.split("Usage:")[1].strip()
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in command.aliases), inline=False)
        
        if command.name in ['slap', 'kiss', 'hug', 'poll', 'avatar', 'userinfo']:
            example = f"Example: `{PREFIX}{command.name} @user`"
            embed.add_field(name="Example", value=example, inline=False)
        
        await ctx.send(embed=embed)

    async def send_error_message(self, error):
        ctx = self.context
        embed = discord.Embed(
            title="Error",
            description=error,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

bot.help_command = HelpCommand()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`\nUsage: `{PREFIX}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: {error}\nUsage: `{PREFIX}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
    else:
        print(f"Ignoring exception in command {ctx.command}:", error)
        await ctx.send(f"⚠ An unexpected error occurred while executing that command.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return
    
    for guild_id, player_data in current_players.items():
        voice_client = player_data['voice_client']
        if voice_client and voice_client.is_connected():
            if len(voice_client.channel.members) == 1:
                beautiful_print(f"🔇 Voice channel empty. Disconnecting...", "─")
                await voice_client.disconnect()
                if guild_id in current_players:
                    if 'control_message' in current_players[guild_id]:
                        try:
                            await current_players[guild_id]['control_message'].delete()
                        except:
                            pass
                    del current_players[guild_id]
                if guild_id in song_queues:
                    song_queues[guild_id].clear()

# --- Run the Bot ---
TOKEN = os.getenv('DISCORD_TOKEN') or 'BOT_TOKEN'

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        beautiful_print(f"❌ Failed to start bot: {e}", "!")
        sys.exit(1)
