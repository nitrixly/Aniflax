# -*- coding: utf-8 -*-

"""
jishaku.features.root_command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The jishaku root command.

:copyright: (c) 2021 Devon (scarletcafe) R
:license: MIT, see LICENSE for more details.

"""

import sys
import typing

try:
    from importlib.metadata import distribution, packages_distributions
except ImportError:
    from importlib_metadata import distribution, packages_distributions

import discord
from discord.ext import commands

from jishaku.features.baseclass import Feature
from jishaku.math import natural_size
from jishaku.modules import package_version
from jishaku.types import ContextA

try:
    import psutil
except ImportError:
    psutil = None


class RootCommand(Feature):
    """
    Feature containing the root jsk command
    """

    @Feature.Command(name="aniflax", aliases=["ani"],
                     invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: ContextA):
        """
        The Jishaku debug and diagnostic commands.

        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """

        # Get the discord package version
        distributions = [
            dist for dist in packages_distributions().get('discord', [])
            if any(file.parts == ('discord', '__init__.py') for file in distribution(dist).files)
        ]

        dist_version = f'{distributions[0]} `{package_version(distributions[0])}`' if distributions else f'unknown `{discord.__version__}`'

        # System and library info
        summary = [
            f"Aniflax v{package_version('jishaku')}, `Python {sys.version.split()[0]}` on `{sys.platform}`",
            f"Process started at <t:{int(self.load_time.timestamp())}:R>, bot was ready at <t:{int(self.start_time.timestamp())}:R>.\n"
        ]

        # Memory usage and PID details
        if psutil:
            proc = psutil.Process()
            with proc.oneshot():
                mem = proc.memory_full_info()
                summary.append(f"Using {natural_size(mem.rss)} at this process.")
                summary.append(f"Running on PID {proc.pid}\n")

        # Guild and user count
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        summary.append(f"This bot is not sharded and can see {guild_count} guild{'s' if guild_count != 1 else ''} and {user_count} user{'s' if user_count != 1 else ''}.")

        # Intent statuses
        intent_summary = {
            'GuildPresences': 'enabled' if self.bot.intents.presences else 'disabled',
            'GuildMembers': 'enabled' if self.bot.intents.members else 'disabled',
            'MessageContent': 'enabled' if self.bot.intents.message_content else 'disabled',
        }
        summary.extend([f"`{intent}` intent is {status}" for intent, status in intent_summary.items()])

        # WebSocket latency
        summary.append(f"Average websocket latency: {round(self.bot.latency * 1000)}ms")

        # Send the formatted output
        await ctx.send("\n".join(summary))

    # Hide and show commands for Jishaku
    @Feature.Command(parent="jsk", name="hide")
    async def jsk_hide(self, ctx: ContextA):
        """
        Hides Jishaku from the help command.
        """
        if self.jsk.hidden:  # type: ignore
            return await ctx.send("Jishaku is already hidden.")

        self.jsk.hidden = True  # type: ignore
        await ctx.send("Jishaku is now hidden.")

    @Feature.Command(parent="jsk", name="show")
    async def jsk_show(self, ctx: ContextA):
        """
        Shows Jishaku in the help command.
        """
        if not self.jsk.hidden:  # type: ignore
            return await ctx.send("Jishaku is already visible.")

        self.jsk.hidden = False  # type: ignore
        await ctx.send("Jishaku is now visible.")

    # Tasks command to show running tasks
    @Feature.Command(parent="jsk", name="tasks")
    async def jsk_tasks(self, ctx: ContextA):
        """
        Shows the currently running jishaku tasks.
        """
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

    # Cancel command to cancel tasks by index
    @Feature.Command(parent="jsk", name="cancel")
    async def jsk_cancel(self, ctx: ContextA, *, index: typing.Union[int, str]):
        """
        Cancels a task with the given index.

        If the index passed is -1, will cancel the last task instead.
        """
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
