import discord
from discord.ext import commands
import sys
import os
import zipfile
import typing

from jishaku.features.baseclass import Feature
from jishaku.math import natural_size
from jishaku.modules import package_version
from jishaku.types import ContextA

try:
    import psutil
except ImportError:
    psutil = None  # This sets psutil to None if it cannot be imported

class RootCommand(Feature):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.jsk.hidden = True

    @Feature.Command(name="aniflax", aliases=["ani"], invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: ContextA):
        jishaku_version = package_version("jishaku").split("a")[0]
        discord_version = package_version("discord").split("a")[0]
        
        summary = [
            f"Aniflax v{jishaku_version}, discord `{discord_version}`, `Python {sys.version.split()[0]}` on `{sys.platform}`",
            f"Process started at <t:{int(self.load_time.timestamp())}:R>, bot was ready at <t:{int(self.start_time.timestamp())}:R>.\n"
        ]

        if psutil:
            proc = psutil.Process()
            with proc.oneshot():
                mem = proc.memory_full_info()
                summary.append(f"Using {natural_size(mem.rss)} at this process.")
                summary.append(f"Running on PID {proc.pid}\n")
        else:
            summary.append("`psutil` library is not available, cannot retrieve runtime stats.")

        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        summary.append(f"This bot is not sharded and can see {guild_count} guild{'s' if guild_count != 1 else ''} and {user_count} user{'s' if user_count != 1 else ''}.")

        intent_summary = {
            'GuildPresences': 'enabled' if self.bot.intents.presences else 'disabled',
            'GuildMembers': 'enabled' if self.bot.intents.members else 'disabled',
            'MessageContent': 'enabled' if self.bot.intents.message_content else 'disabled',
        }
        summary.extend([f"`{intent}` intent is {status}" for intent, status in intent_summary.items()])

        summary.append(f"Average websocket latency: {round(self.bot.latency * 1000)}ms")
        await ctx.send("\n".join(summary))
    
