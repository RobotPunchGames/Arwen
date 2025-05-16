Arwen Discord Bot

Ahoy Captain! Welcome aboard the Arwen Discord Bot, your playful and witty GPT-powered assistant with a dash of dark humor. Arwen serves as the secretary to the Robot Punch indie VR game studio and is always ready to lend a hand—whether it’s chatting, generating images, or fetching crypto stats.

📝 Features

GPT-4.1 Chat: Engages users with context-aware conversations and persistent memory stored in memory.json.

Image Generation: Use !createimage [description] to summon vivid DALL·E 3 images right in Discord.

Crypto Market Report: !crypto fetches the top 20 cryptocurrencies’ latest prices and 24h changes via CoinMarketCap API.

Custom Greetings: !greet delivers Arwen’s signature salutation.

User Whitelisting: Only approved usernames can DM Arwen (configured in users_allowed_to_DM_Arwen).

⚙️ Configuration

Create a .env file in the project root with the following keys:

OPENAI_API_KEY=your_openai_api_key
DISCORD_TOKEN=your_discord_bot_token
CHANNEL_ID=the_numeric_id_of_your_discord_channel
COINMARKET_API_KEY=your_coinmarketcap_api_key

OPENAI_API_KEY: Grants access to GPT-4.1 and DALL·E 3.

DISCORD_TOKEN: Your Discord bot token.

CHANNEL_ID: The ID of the channel where Arwen listens.

COINMARKET_API_KEY: For pulling crypto data.

🛠️ Commands Summary

Command

Description

!greet

Arwen sends a personalized greeting.

!createimage [desc]

Generate an image via DALL·E 3 using your prompt.

!crypto

Print top-20 cryptocurrencies’ 24h performance.

Chat (plain text)

General conversation powered by GPT-4.1.
