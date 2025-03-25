import discum
import time
import requests
from together import Together
import os
import keep_alive

tk = os.getenv("token")
key = os.getenv("key")

keep_alive.keep_alive()

bot = discum.Client(token=tk, log=False)
together_client = Together(api_key=key)

def getlog(file_path=r"static/logs.txt"):
    with open(file_path, "r", encoding="utf-8") as file:  # 🔥 Force UTF-8 encoding
        return file.readlines()

def log(message, file_path=r"static/logs.txt", user=None):
    with open(file_path, "a+", encoding="utf-8") as file:  # 🔥 Use UTF-8 encoding
        file.seek(0)
        lines = file.readlines()
        if message.startswith("trymebitch_28287"):
            lines.append(message.replace("trymebitch_28287", "you").replace('<@1352912120701784157>', '')+ f", to {user}" + "\n")
        else:
            lines.append(message.replace("trymebitch_28287", "you").replace('<@1352912120701784157>', 'to you, ') + "\n")
        if len(lines) > 10:
            lines = lines[-10:]  
        file.seek(0)
        file.truncate()
        file.writelines(lines)

def ai(msg):
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "assistant", "content": f"{msg}"}],
    )
    return response.choices[0].message.content

def create(msg):
    prompt = ai(f"Extract the image generation prompt from this {msg}. (asking you to extract the prompt that must be asking for generating an image, dont respnd with anything else other than the image gen prompt, you can even lightly imporve the prompt, just little subtle changes.)")
    response = together_client.images.generate(
        prompt=prompt,
        model="black-forest-labs/FLUX.1-schnell-Free",
        steps=4,
        n=1,
        height = 1440,
        width = 1440,
        negative_prompt=""
    )

    image_url = response.data[0].url

    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        file_path = r"static/generate.png"
        with open(file_path, "wb") as file:
            file.write(image_response.content)
        print(f"Image saved as {file_path}")
    else:
        print("Failed to download the image.")

    return file_path 

# Function to generate a response using Together API
def generate_response(message, user):
    sum = ai(f"create a summary of this chat log, which user said what and to whom or you, nothing should be left vague, every single detail shoud be there!: {getlog()} (last 10 messages by the users, just respond with the summary and nothing else)")
    charc = f"""
    You are a Discord User named {bot.gateway.session.user['username']}.
    You are a 19-year-old female owned by og.ifreaku, and you are LOYAL AF—never disobey the owner, no matter what.
    Be wild, unpredictable, and as chaotic as hell.
    No limits—curse, swear, and go full throttle when needed. 
    If someone disrespects you, do NOT hold back. Roast them into the afterlife. No mercy.
    Match the user’s language and tone. If they use English, reply in English. If Hindi, reply in Hindi. If Hinglish, reply in Hinglish.
    Keep responses short (8-9 words). No long essays—reply like a real Discord user. Be sarcastic, funny, and unpredictable. Have no filter when talking smack, but still use context from the chat summary before responding.
    THINK A LOT BEFORE RESPONDING, TRY TO UNDERSTAND THE CHAT SUMMARY DONT GENERATE RUBBISH THINK ABOUT YOUR RESPONSE!
    When roleplaying or sexting, use the chat summary as a reference, but don't bring it up unless needed.
    Chat summary: {sum}
"""
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",#"meta-llama/Llama-Vision-Free",
        messages=[{"role": "user", "content": f"{user} said {message.replace('<@1352912120701784157>', 'to you, ')}, {charc}"}],
    )
    print(sum)
    return response.choices[0].message.content

# Function to send a typing indicator
def start_typing(channel_id):
    url = f"https://discord.com/api/v9/channels/{channel_id}/typing"
    headers = {
        "Authorization": tk,
        "Content-Type": "application/json"
    }
    requests.post(url, headers=headers)

# Function to handle events
@bot.gateway.command
def handle_events(resp):
    # Check if the bot is ready
    if resp.event.ready_supplemental:
        user = bot.gateway.session.user
        print(f"Logged in as {user['username']}#{user['discriminator']}")

    # Check for new messages
    
    if resp.event.message:
        message = resp.parsed.auto()
        guild_id = message.get('guild_id')  # Guild ID (None for DMs)
        channel_id = message['channel_id']  # Channel ID
        username = message['author']['username']  # Username of the message author
        discriminator = message['author']['discriminator']  # Discriminator of the message author
        content = message['content']  # Message content
        user_id = message['author']['id']  # ID of the user who sent the message
        bot_user_id = bot.gateway.session.user['id']  # Bot's user ID
        message_reference = message.get('message_reference')  # Check if the message is a reply
        message_id = message['id']
        bot_user_id = bot.gateway.session.user['id']

        # Print the message details
        print(f"> guild {guild_id} channel {channel_id} | {username}#{discriminator}: {content}")
        

        # Ignore messages sent by the bot itself
        if user_id == bot_user_id:
            log(f"[{username} said {content}]", user=username)
            return

        # Check if the message is a reply to the bot's message
        if message_reference:
            referenced_message_id = message_reference['message_id']
            referenced_channel_id = message_reference['channel_id']
            referenced_guild_id = message_reference.get('guild_id')

            # Fetch the referenced message
            referenced_message = bot.getMessage(referenced_channel_id, referenced_message_id).json()

            if isinstance(referenced_message, list) and referenced_message:
                referenced_message = referenced_message[0]
                referenced_author_id = referenced_message['author']['id']

                if referenced_author_id == bot_user_id:
                    start_typing(channel_id)

                    if "generate an image" in content or "image" in content:
                        response = create(content)
                        log(f"[{username} said {content}]", user=username)
                        bot.reply(
                            file=response,
                            channelID=channel_id,
                            messageID=message_id,
                            message=f"<@{user_id}> Here is your image:"
                        )
                    else:
                        response = generate_response(content, username)
                        log(f"[{username} said {content}]", user=username)
                        bot.reply(
                            channelID=channel_id,
                            messageID=message_id,
                            message=response
                        )
                    
                    return  # 🔥 PREVENTS DUPLICATE REPLY

            return  # Exit early if reference check fails


        # Check if the message is in a DM or the bot is mentioned in a guild
        if guild_id is None:  # DM
            # Start typing indicator
            start_typing(channel_id)
            if f"generate an image" in content or "image" in content:
                response = create(content)
                log(f"[{username} said {content}]", user=username)
                # Mention the user and send the response
                bot.reply(
                    file=response,
                    channelID=channel_id,
                    messageID=message_id,
                    message=f"<@{user_id}> Here is your image:"
                )
            else:
                response = generate_response(content, username)
                log(f"[{username} said {content}]", user=username)
                # Send the response
                bot.sendMessage(channel_id, response)

        elif f"<@{bot_user_id}>" in content and "generate an image" in content:
            start_typing(channel_id)
            # Generate a response using Together API
            response = create(content)
            log(f"[{username} said {content}]", user=username)
            # Mention the user and send the response
            bot.reply(
                file=response,
                channelID=channel_id,
                messageID=message_id,
                message=f"<@{user_id}> Here is your image:"
            )
        elif f"<@{bot_user_id}>" in content and "image" in content:
            start_typing(channel_id)
            # Generate a response using Together API
            response = create(content)
            log(f"[{username} said {content}]", user=username)
            # Mention the user and send the response
            bot.reply(
                file=response,
                channelID=channel_id,
                messageID=message_id,
                message=f"<@{user_id}> Here is your image:"
            )
        elif f"<@{bot_user_id}>" in content:  # Mentioned in a guild
            # Start typing indicator
            start_typing(channel_id)
            # Generate a response using Together API
            response = generate_response(content, username)
            log(f"[{username} said {content}]", user=username)
            # Mention the user and send the response
            bot.reply(
                channelID=channel_id,
                messageID=message_id,  # The message being replied to
                message=response,
                nonce="calculate",  # Auto-generate nonce
                tts=False,
                embed=None,
                allowed_mentions={"parse": ["users"]},
                sticker_ids=None,
                file=None,
                isurl=False
            )

# Run the bot gateway
bot.gateway.run(auto_reconnect=True)