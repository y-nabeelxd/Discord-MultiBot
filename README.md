# Discord MultiBot (Python)

**Author:** [y-nabeelxd](https://github.com/y-nabeelxd) 
A **feature-rich Discord bot** made with **Python** and **discord.py**.

This bot comes with **music playback**, **Roblox verification**, **FiveM verification**, **moderation tools**, and **fun commands**.
> ⚠️ *Valorant and SA:MP verifications are under maintenance (fix coming soon).*

---

## ✨ Features
- **🎵 Music Player** — Play songs from YouTube (no cookies, API keys, or tokens needed)
- **🛡️ Moderation Tools** — Ban, kick, timeout, slowmode, set nicknames, and manage roles
- **🔒 Verification Systems** — Roblox and FiveM verification with role assignment
- **🎮 Fun & Mini Games** — Rock-Paper-Scissors, Dice rolls, Coin flips, Guessing game
- **📊 Owo Economy Games** — Slots, Coinflip, Daily rewards with coin system
- **📆 Polls & Utilities** — Create polls, reminders, server info, and user info
- **📌 FiveM Server Status** — Live server status updates with `!fivemserverlive`
- **🚀 Future Plans** — More useful and better commands will be added soon!

---

## 📂 Project Structure
```
Discord-MultiBot-py/
├── bot.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation
1. **Clone the repository:**
```
git clone https://github.com/y-nabeelxd/Discord-MultiBot-py
cd Discord-MultiBot-py
```
2. **Install dependencies:**
```
pip install -r requirements.txt
```
3. **Edit bot configuration:**
- **Bot Token:** 
Open `bot.py` and replace:
```
TOKEN = os.getenv('DISCORD_TOKEN') or 'BOT_TOKEN'
```
with your bot token inside 'BOT_TOKEN' or set DISCORD_TOKEN as an environment variable.
- **Prefix:**
Change the command prefix:
```
PREFIX = "!"
```
(This is around line **41** in `bot.py`)

4. **Run the bot:**
```
python bot.py
```

---

## 🎵 Music Commands
- `!play <song>` — Play a song or add to queue 
- `!skip` — Skip current song 
- `!pause` — Pause playback 
- `!resume` — Resume playback 
- `!queue` — Show current queue 
- `!stop` — Stop playback and clear queue 
- `!leave` — Make the bot leave the voice channel 

---

## 🛡️ Moderation Commands
- `!ban @user [reason]` — Ban a member 
- `!kick @user [reason]` — Kick a member 
- `!timeout @user 30m [reason]` — Timeout a member 
- `!slowmode 30s` — Set channel slowmode 
- `!addrole @user @Role` — Add a role 
- `!removerole @user @Role` — Remove a role 
- `!setnick @user NewName` — Change nickname 
- `!lock [#channel] [@role]` — Lock a channel 
- `!unlock [#channel] [@role]` — Unlock a channel

---

## 🔒 Verification
- **Roblox**: `!verifyroblox <username>` (Working ✅) 
- **FiveM**: `!verifyfivem <username>` (Working ✅) 
- **FiveM Server Status**: `!fivemserverlive [#channel]` (New ✨)
- **SA:MP**: `!verifysamp <username>` (Under Maintenance ❌) 
- **Valorant**: `!verifyvalo <Username#Tag>` (Under Maintenance ❌) 

---

## 🎮 Owo Economy Games
- `owo coinflip <amount> [heads/tails]` - Flip a coin with your coins
- `owo slots <amount>` - Play slots with your coins
- `owo daily` - Claim your daily coins (300-5000)
- `owo balance [@user]` - Check coin balance

---

## ⚠️ Current Status
- **Roblox Verification**: **Working Perfectly** ✅ 
- **FiveM Verification**: **Working (Improved)** ✅ 
- **SA:MP, Valorant**: **Currently unavailable (fix in progress)** ❌ 

---

## 🚀 Future Updates
- Advanced moderation tools 
- New verification systems 
- More fun commands & games 
- Economy system improvements

---

## 👤 Author
**[y-nabeelxd](https://github.com/y-nabeelxd)** 
_If you like this project, star ⭐ the repository!_
