import discum
import time
import requests
from together import Together
import os
import keep_alive
import json
import threading
from datetime import datetime, timedelta

tk = os.getenv("token")
key = os.getenv("key")
keep_alive.keep_alive()

bot = discum.Client(token=tk, log=False)
together_client = Together(api_key=key)
bot_start_time = time.time()

# Calculates and formats the bot's uptime in days, hours, minutes, and seconds
def get_uptime():
    uptime_seconds = int(time.time() - bot_start_time)
    
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    uptime_str = ""
    if days > 0:
        uptime_str += f"{days}D "
    if hours > 0:
        uptime_str += f"{hours}H "
    if minutes > 0:
        uptime_str += f"{minutes}M "
    uptime_str += f"{seconds}S"
    
    return uptime_str

# Retrieves the last 10 messages from the chat log file
def getlog(file_path=r"static/logs.txt"):
    with open(file_path, "r", encoding="utf-8") as file:  # 🔥 Force UTF-8 encoding
        return file.readlines()

# Clears all messages from the chat log file
def clear_log(file_path=r"static/logs.txt"):
    with open(file_path, "w", encoding="utf-8") as file:
        file.truncate()  # Clears the file

# Logs chat messages with proper formatting and maintains a 10-message history
def log(message, user=None, file_path=r"static/logs.txt"):
    msg = message.replace('<@1352912120701784157>', '').replace("chatwithmepls", "you")

    if msg.startswith("You"):
        msg = "[" + msg + f", to {user}]" + "\n"
    else:
        msg = f"[{user} said, " + msg + ", to you]" +"\n"

    print(msg)
    with open(file_path, "a+", encoding="utf-8") as file:  # 🔥 Use UTF-8 encoding
        file.seek(0)
        lines = file.readlines()
        lines.append(msg)
        if len(lines) > 10:
            lines = lines[-10:]  
        file.seek(0)
        file.truncate()
        file.writelines(lines)

# Generates AI responses using the Together API
def ai(msg):
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "assistant", "content": f"{msg}"}],
    )
    return response.choices[0].message.content

# Generates an image displaying the bot's current uptime
def up():
    promp = f"the text ' {get_uptime()} ' in center, (any font style, any background or setting that you might think would be best here)"
    response = together_client.images.generate(
        prompt=promp,
        model="black-forest-labs/FLUX.1-schnell-Free",
        steps=4,
        n=1,
        height = 240,
        width = 1792,
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

# Extracts and processes image generation prompts from user messages
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
    You are a 19-year-old female.
    Be wild, and as chaotic as hell.
    No limits—curse, swear, and go full throttle when needed. 
    If someone disrespects you, do NOT hold back. Roast them into the afterlife. No mercy.
    Match the user’s language and tone. If they use English, reply in English. If Hindi, reply in Hindi. If Hinglish, reply in Hinglish.
    Keep responses short (20-30 words). No long essays—reply like a real Discord user. Be sarcastic, funny, and unpredictable. Have no filter when talking smack, but still use context from the chat summary before responding.
    THINK A LOT BEFORE RESPONDING, TRY TO UNDERSTAND THE CHAT SUMMARY DONT GENERATE RUBBISH THINK ABOUT YOUR RESPONSE!
    Focus on completing the requested action directly without adding unnecessary commentary or filler text.
    When roleplaying or sexting, use the chat summary as a reference, but don't bring it up unless needed.
    AND DONT REPEAT THE SAME RESPONSES OF YOURS CHECK THE SUMMARY AND DON'T SEND SAME RESPONSES!
    Chat summary: {sum}
"""
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",#"meta-llama/Llama-Vision-Free",
        messages=[{"role": "user", "content": f"{user} said {message.replace('<@1352912120701784157>', 'to you, ')} ({charc})"}],
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
    
    # Load tasks from JSON file
    # In load_tasks function
    def load_tasks(file_path=r"static/tasks.json"):
        try:
            with open(file_path, "r") as file:
                content = file.read()
                if not content.strip():
                    return {"tasks": []}
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"tasks": []}
    
    # Task execution function
    def execute_tasks():
        while True:
            try:
                tasks = load_tasks()
                current_time = time.time()
                
                for task in tasks['tasks']:
                    if current_time - task.get('last_run', 0) >= task['interval_seconds']:
                        # Execute task directly
                        try:
                            bot.sendMessage(task['channel_id'], task['cmd'])
                            print(f"Task executed successfully: {task['cmd']}")
                            # Update last run time after successful execution
                            task['last_run'] = current_time
                            save_tasks(tasks)
                        except Exception as e:
                            print(f"Failed to execute task: {e}")
                            continue
                        
                time.sleep(1)  # Check tasks every second
            except Exception as e:
                print(f"Task scheduler error: {e}")
                time.sleep(1)
    
    # Save tasks to JSON file
    def save_tasks(tasks, file_path=r"static/tasks.json"):
        with open(file_path, "w") as file:
            json.dump(tasks, file, indent=4)
    
    # Convert time string to seconds
    def parse_time_interval(interval):
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        value = int(''.join(filter(str.isdigit, interval)))
        unit = ''.join(filter(str.isalpha, interval.lower()))[0]
        return value * units.get(unit, 1)
    
    # Lock for task operations
    task_lock = threading.Lock()

    # Start task execution thread
    task_thread = threading.Thread(target=execute_tasks, daemon=True)
    task_thread.start()

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
            return
        
        if content.startswith(">clearmemory"):
            clear_log()
            print("CLEARED!")
            return
        
        if content.startswith(">up"):
            uptime = up()
            bot.reply(
                channelID=channel_id,
                messageID=message_id,
                message=f"⏰ **Uptime:**",
                file=uptime 
            )
            return
        
        if content.startswith(">task") and user_id == "867447725230784552":
            try:
                start_typing(channel_id)
                # Parse command parameters
                params = dict(param.split(":") for param in content.split()[1:])
                cmd = params.get("cmd", "")
                channel_id = params.get("channel", "")
                interval = params.get("time", "")
                
                if not all([cmd, channel_id, interval]):
                    bot.sendMessage(channel_id, "❌ Invalid command format! Use >task cmd:(command) channel:(id) time:(interval)")
                    return
                
                # Load existing tasks
                tasks = load_tasks()
                
                # Create new task with initial last_run set to epoch
                new_task = {
                    "cmd": cmd,
                    "channel_id": channel_id,
                    "interval": interval,
                    "interval_seconds": parse_time_interval(interval),
                    "last_run": 0  # Initialize with 0 to trigger immediate execution
                }
                
                # Add task to list
                tasks['tasks'].append(new_task)
                save_tasks(tasks)
                
                bot.sendMessage(channel_id, f"✅ Task scheduled! Command: {cmd} will run every {interval}")
            except Exception as e:
                bot.sendMessage(channel_id, f"❌ Error creating task: {str(e)}")
            return


        # Check if the message is a reply to the bot's message
        if message_reference:
            referenced_message_id = message_reference['message_id']
            referenced_channel_id = message_reference['channel_id']
            referenced_guild_id = message_reference.get('guild_id')
            
            # Get the actual content of the message being replied to
            referenced_message = bot.getMessage(referenced_channel_id, referenced_message_id).json()
            referenced_content = referenced_message[0]['content'] if isinstance(referenced_message, list) else ''
            print(referenced_content)

            if isinstance(referenced_message, list) and referenced_message:
                referenced_message = referenced_message[0]
                referenced_author_id = referenced_message['author']['id']

                if referenced_author_id == bot_user_id:
                    start_typing(channel_id)

                    if "generate an image" in content or "image" in content:
                        response = create(content)
                        log(f"{content}", user=username)
                        log(f"You said, <@{user_id}> Here is your image", user=username)
                        with message_lock:
                            bot.reply(
                                file=response,
                                channelID=channel_id,
                                messageID=message_id,
                                message=f"<@{user_id}> Here is your image:"
                            )
                    else:
                        response = generate_response(f" {content}, Replying to the message: {referenced_content}, said by {referenced_message['author']['username']} ", username)
                        log(f"{content}, Replying to the message: {referenced_content}, said by {referenced_message['author']['username']} ", user=username)
                        log(f"You said, " + response, user=username)
                        with message_lock:
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
                log(f"{content}", user=username)
                log(f"You said, <@{user_id}> Here is your image", user=username)
                # Mention the user and send the response
                with message_lock:
                    bot.reply(
                        file=response,
                        channelID=channel_id,
                        messageID=message_id,
                        message=f"<@{user_id}> Here is your image:"
                    )
            else:
                response = generate_response(content, username)
                log(f"{content}", user=username)
                log(f"You said, " + response, user=username)
                # Send the response directly
                bot.sendMessage(channel_id, response)
            return
        else:
            if f"<@{bot_user_id}>" in content:
                if "generate an image" in content or "image" in content:
                    start_typing(channel_id)
                    # Generate a response using Together API
                    response = create(content)
                    log(f"{content}", user=username)
                    log(f"You said, <@{user_id}> Here is your image", user=username)
                    # Mention the user and send the response
                    with message_lock:
                        bot.reply(
                            file=response,
                            channelID=channel_id,
                            messageID=message_id,
                            message=f"<@{user_id}> Here is your image:"
                        )
                else:  # Mentioned in a guild
                    # Start typing indicator
                    start_typing(channel_id)
                    # Generate a response using Together API
                    response = generate_response(content, username)
                    log(f"{content}", user=username)
                    log(f"You said, " + response, user=username)
                    # Mention the user and send the response directly
                    bot.sendMessage(channel_id, response)
                return

# Run the bot gateway
bot.gateway.run(auto_reconnect=True)

