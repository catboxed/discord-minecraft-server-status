import discord, json
from discord.ext import tasks
from mcstatus import JavaServer
from datetime import datetime

with open('config.json', 'r') as file:
    config = json.load(file)
    constants = config["constants"]
    messages = config["messages"]

# Constants
TOKEN = constants['BOT_TOKEN']
CHANNEL_ID = int(constants['CHANNEL_ID'])
SERVER_ADDRESS = constants['MINECRAFT_SERVER']
SERVER_PORT = int(constants['MINECRAFT_SERVER_PORT'])
DELAY = constants['DELAY']
SERVER_OFFLINE = messages["SERVER_OFFLINE"]
SERVER_ONLINE = messages["SERVER_ONLINE"]
PLAYER_JOINED = messages["PLAYER_JOINED"]
PLAYER_LEFT = messages["PLAYER_LEFT"]

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
server_down = False
players_changed = False
online_players = []

@client.event
async def on_ready():
    print("Connected to Discord!")
    update_status.start()

@tasks.loop(seconds=DELAY)
async def update_status():
    global server_down, players_changed, online_players

    date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    try:
        server = JavaServer.lookup(f"{SERVER_ADDRESS}:{SERVER_PORT}")
        server_status = server.status()

    except Exception as error:
        if not server_down:
            server_down = True
            await send_message(SERVER_OFFLINE)
        return

    if server_down:
        server_down = False
        await send_message(SERVER_ONLINE)

    if server_status.players.online == 0 and not online_players:
        return

    players = []
    if server_status.players.sample:
        players = [player.name for player in server_status.players.sample]

    if players == online_players:
        return

    for player in players:
        if player not in online_players:
            await add_player(player)
            players_changed = True

    for player in online_players[:]:
        if player not in players:
            await remove_player(player)
            players_changed = True

    if players_changed:
        players_changed = False
        print(f"{date} :: Online Players = {online_players}")

async def add_player(player):
    global online_players
    online_players.append(player)
    await send_message(PLAYER_JOINED.format(player=player))

async def remove_player(player):
    global online_players
    online_players.remove(player)
    await send_message(PLAYER_LEFT.format(player=player))

async def send_message(message):
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)

client.run(TOKEN)
