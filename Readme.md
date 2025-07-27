# Discord-MultiBot-py 🤖

A versatile Discord bot with **Roblox verification**, **music playback**, **moderation tools**, and fun commands. Designed for easy setup and customization.

---

## 🜠 Features
- **🔒 Roblox Verification** *(Working perfectly!)*  
  Verify users via Roblox profile with a secure code system.
- **🎵 Music Player**  
  Play songs from YouTube without API keys/cookies.
- **🛡️ Moderation**  
  Kick, ban, timeout, slowmode, and role management.
- **🎮 Fun & Games**  
  Rock-paper-scissors, dice rolls, coin flips, and more.
- **🚙️ Utility**  
  Polls, reminders, server/user info, and avatar commands.

> **⚠️ Note:**  
> FiveM, SA:MP, and Valorant verifications are **currently under maintenance** and will be fixed in a future update.

---

## 🛠️ Installation

1. **Clone the repository**:  
    ```
    git clone https://github.com/y-nabeelxd/Discord-MultiBot-py
    cd Discord-MultiBot-py
    ```

2. **Install dependencies**:  
    ```
    pip install -r requirements.txt
    ```

3. **Configure the bot**:  
   - Rename `.env.example` to `.env` and add your bot token:  
     ```
     DISCORD_TOKEN=your_bot_token_here
     ```
   - In `bot.py`, change the prefix (line 151):  
     ```
     PREFIX = "!"  # Change to your desired prefix
     ```

4. **Run the bot**:  
    ```bash
    python bot.py
    ```

---

## 🚙️ Configuration

### 🔧 Key Settings (in `bot.py`)
| Variable                | Description                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `PREFIX = "!"`           | Change the bot's command prefix (line 115).                     |
| `VERIFICATION_ROBLOX`  | Set to `False` to disable Roblox verification (line 13).               |
| `ROBLOX_ROLE_ID`      | Add a role ID to assign upon verification (line 22).                |
| `CHANGE_NICKNAME`     | Set to `True` to update nicknames after verification (line 16).        |

> **🔐 Token Security**: Always keep your bot token in `.env` and never share it!

---

## 🎚️ Command Categories

### 🎵 Music Commands
- `!play [song]` - Play a song or add to queue.  
- `!skip` - Skip the current song.  
- `!queue` - Show the current queue.  

### 🔒 Verification (Roblox Only)
- `!verifyroblox [username]` - Start Roblox verification.  

### 🛡️ Moderation
- `!kick @user [reason]` - Kick a member.  
- `!ban @user [reason]` - Ban a member.  
- `!slowmode 30s` - Set channel slowmode.  

### 🎮 Fun & Games
- `!rps rock` - Play rock-paper-scissors.  
- `!roll 2d20` - Roll dice.  

---

## 🚀 Future Plans
- [ ] Fix FiveM/SA:MP/Valorant verification.  
- [ ] Add more music sources (Spotify, SoundCloud).  
- [ ] Advanced moderation logs.  

---

## 📜 License
MIT © [y-nabeelxd](https://github.com/y-nabeelxd)  
