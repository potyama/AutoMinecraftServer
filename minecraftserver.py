import discord
from discord.ext import commands, tasks
import asyncio
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
PREFIX = '/'
AUTHORIZED_ROLES = ['マイクラ部']

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True  # リアクションのイベントを受け取るための権限を追加

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

class MinecraftServerController:
    def __init__(self):
        self.server_process = None

    def start_server(self):
        if not self.is_server_running():
            self.server_process = subprocess.Popen(["java", "-Xmx4G", "-Xms4G", "-jar", "server.1.20.2.jar"], shell=False)
            return "サーバーを起動しました。"
        else:
            return "サーバーは既に起動しています。"

    def stop_server(self):
        if self.is_server_running():
            self.server_process.terminate()
            return "サーバーを停止しました。"
        else:
            return "サーバーは既に停止しています。"

    def is_server_running(self):
        try:
            result = subprocess.check_output(['ps', 'aux'], text=True)
            return 'server.1.20.2.jar' in result
        except:
            return False

    def get_online_players(self):
        if not self.is_server_running():
            return "サーバーは現在、停止中です。"
        players= []
        with open('logs/latest.log', 'r') as f:
            for line in f:
                if 'joined the game' in line:
                    player = line.split(' ')[3]
                    if player not in players:
                        players.append(player)
                elif 'left the game' in line:
                    player = line.split(' ')[3]
                    if player in players:
                        players.remove(player)
    
        return players
server_controller = MinecraftServerController()

def has_permission(roles):
    return any(role.name in AUTHORIZED_ROLES for role in roles)

@bot.command()
async def start(ctx):
    if not has_permission(ctx.author.roles):
        await ctx.send("許可されていない操作です。")
        return
    response = server_controller.start_server()
    await ctx.send(response)

@bot.command()
async def stop(ctx):
    if not has_permission(ctx.author.roles):
        await ctx.send("許可されていない操作です。")
        return

    # 警告メッセージを送信
    message = await ctx.send("本当にサーバーを止めますか？")
    # リアクションを追加
    for emoji in ("✅", "❌"):
        await message.add_reaction(emoji)

    # ユーザーのリアクションを待つ
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("タイムアウトしました。サーバーは停止されません。")
    else:
        if str(reaction.emoji) == "✅":
            response = server_controller.stop_server()
            await ctx.send(response)
        else:
            await ctx.send("サーバーの停止をキャンセルしました。")

@bot.command()
async def status(ctx):
    if server_controller.is_server_running():
        await ctx.send("サーバーは現在、起動中です。")
    else:
        await ctx.send("サーバーは現在、停止中です。")

@bot.command()
async def people(ctx):
    if not has_permission(ctx.author.roles):
        await ctx.send("許可されていない操作です。")
        return

    players = server_controller.get_online_players()
    if isinstance(players, str):
        await ctx.send(players)
    elif players:
        await ctx.send("現在オンラインのプレイヤーは以下の通りです：\n" + '\n'.join(players))
    else:
        await ctx.send("現在オンラインのプレイヤーはいません。")

bot.run(TOKEN)
