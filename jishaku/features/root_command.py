# -*- coding: utf-8 -*-

"""
jishaku.features.root_command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The jishaku root command.

"""

import sys
import typing
import os
import zipfile
import discord
from discord.ext import commands
from jishaku.features.baseclass import Feature
from jishaku.math import natural_size
from jishaku.modules import package_version
from jishaku.paginators import PaginatorInterface
from jishaku.types import ContextA

try:
    import psutil
except ImportError:
    psutil = None


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

    @Feature.Command(parent="jsk", name="hide")
    async def jsk_hide(self, ctx: ContextA):
        if self.jsk.hidden:
            return await ctx.send("Aniflax is already in stealth mode.")

        self.jsk.hidden = True
        await ctx.send("Aniflax is tucked away and hidden.")

    @Feature.Command(parent="jsk", name="show")
    async def jsk_show(self, ctx: ContextA):
        if not self.jsk.hidden:
            return await ctx.send("Aniflax is already visible")

        self.jsk.hidden = False
        await ctx.send("Aniflax is now visible.")

    @Feature.Command(parent="jsk", name="tasks")
    async def jsk_tasks(self, ctx: ContextA):
        if not self.tasks:
            return await ctx.send("No currently running tasks.")

        paginator = commands.Paginator(max_size=1980)

        for task in self.tasks:
            if task.ctx.command:
                paginator.add_line(f"{task.index}: `{task.ctx.command.qualified_name}`, invoked at "
                                   f"{task.ctx.message.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            else:
                paginator.add_line(f"{task.index}: unknown, invoked at "
                                   f"{task.ctx.message.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    @Feature.Command(parent="jsk", name="cancel")
    async def jsk_cancel(self, ctx: ContextA, *, index: typing.Union[int, str]):
        if not self.tasks:
            return await ctx.send("No tasks to cancel.")

        if index == "~":
            task_count = len(self.tasks)
            for task in self.tasks:
                if task.task:
                    task.task.cancel()
            self.tasks.clear()
            return await ctx.send(f"Cancelled {task_count} tasks.")

        if isinstance(index, str):
            raise commands.BadArgument('Literal for "index" not recognized.')

        if index == -1:
            task = self.tasks.pop()
        else:
            task = discord.utils.get(self.tasks, index=index)
            if task:
                self.tasks.remove(task)
            else:
                return await ctx.send("Unknown task.")

        if task.task:
            task.task.cancel()

        if task.ctx.command:
            await ctx.send(f"Cancelled task {task.index}: `{task.ctx.command.qualified_name}`,"
                           f" invoked {discord.utils.format_dt(task.ctx.message.created_at, 'R')}")
        else:
            await ctx.send(f"Cancelled task {task.index}: unknown,"
                           f" invoked {discord.utils.format_dt(task.ctx.message.created_at, 'R')}")

    @Feature.Command(parent="jsk", name="leave")
    async def jsk_leave(self, ctx: ContextA, server_id: int):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            return await ctx.send(f"The bot is not in a server with ID {server_id}.")

        await guild.leave()
        await ctx.send(f"Successfully left the server: {guild.name} (ID: {server_id})")

    @Feature.Command(parent="jsk", name="backup")
    async def jsk_backup(self, ctx: ContextA):
        zip_filename = "backup.zip"

        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for foldername, subfolders, filenames in os.walk("."):
                for filename in filenames:
                    if filename.endswith(".py"):
                        file_path = os.path.join(foldername, filename)
                        zipf.write(file_path, os.path.relpath(file_path, "."))

        with open(zip_filename, "rb") as file:
            await ctx.send("Here Is Your Source Code", file=discord.File(file, zip_filename))

        os.remove(zip_filename)

    @Feature.Command(parent="jsk", name="memory")
    async def jsk_memory(self, ctx: ContextA):
        if psutil:
            proc = psutil.Process()
            mem_info = proc.memory_full_info()
            memory_summary = (
                f"RSS: {natural_size(mem_info.rss)}\n"
                f"VMS: {natural_size(mem_info.vms)}\n"
                f"Shared: {natural_size(mem_info.shared)}\n"
                f"Text: {natural_size(mem_info.text)}\n"
                f"Lib: {natural_size(mem_info.lib)}\n"
                f"Data: {natural_size(mem_info.data)}\n"
                f"Dirty: {natural_size(mem_info.dirty)}"
            )
            await ctx.send(f"Memory Info:\n```\n{memory_summary}\n```")
        else:
            await ctx.send("psutil is not available, cannot retrieve memory info.")

        import gc
        gc.collect()
        await ctx.send("Garbage collection run.")
