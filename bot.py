from __future__ import annotations

import functools
import os
import platform
from typing import Any, Optional, List

import discord
from discord import ApplicationContext, DiscordException, Interaction
from discord.ext import commands
from discord.ext.commands import CommandOnCooldown
from discord.ui import Select

from modules import RateMyProfAPI
from modules.callbacks import teacher_list_view
from modules.embeds import fail_embed, prof_list_embed, get_teacher_embed


class RateMyProfBot(discord.Bot):
    """"
    Bot for reading rate my prof data

    """

    async def on_ready(self) -> None:
        """
        Send some start-up messages on Bot Ready State
        :return: None

        """

        print("-------------------")
        print(f"Logged in as {self.user.name}")
        print(f"Discord.py API version: {discord.__version__}")
        print(f"Python version: {platform.python_version()}")
        print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        print("Go for launch!")
        print("-------------------")

    @classmethod
    async def safe_function(cls, func: functools.partial) -> Optional[Any]:
        """
        Wrap any unsafe function in a try-catch to prevent errors

        :param func: The function to wrap
        :return: The result of running the function, or None if it failed
        """

        try:
            return await func()
        except:
            return None

    async def on_application_command_error(self, context: ApplicationContext, exception: DiscordException) -> Any:
        """
        Whenever there is a command error, it'll be handled here

        :param context: Context of the request
        :param exception: The error that was raised
        :return: None

        """

        # If the command cooldown is reached
        if isinstance(exception, CommandOnCooldown):
            return await context.respond(
                ephemeral=True,
                embed=fail_embed(context.user, f"You are on cooldown! Try again in `{round(exception.retry_after, 1):,}` seconds.")
            )

        raise exception


bot: RateMyProfBot = RateMyProfBot()


@bot.slash_command(name="prof", description="Search a professor on the RateMyProf website")
@commands.cooldown(3, 30, commands.BucketType.user)
@commands.cooldown(60, 3600, commands.BucketType.user)
@commands.cooldown(250, 3600, commands.BucketType.guild)
async def prof(context: ApplicationContext, name) -> Any:
    """
    Search a professor by their name

    :param context: Application context
    :param name: Name of the professor
    :return: Any, ignored by app

    """

    # Get teacher list
    teachers: Optional[List[dict]] = await bot.safe_function(functools.partial(RateMyProfAPI.search_teacher, name=name))
    if not teachers:
        return await context.respond(ephemeral=True, embed=fail_embed(context.user, "Failed to retrieve the list of teachers."))

    # Send the teacher select menu
    await context.respond(embed=prof_list_embed(), view=teacher_list_view(teachers, select_prof))


async def select_prof(select: Select, interaction: Interaction) -> None:
    """
    Select a professor given the teacher list select menu

    :param select: The select menu state
    :param interaction: The interaction context
    :return: None

    """

    # The teacher ID to search
    teacher_id: str = select.values[0]

    # Search the teacher
    teacher: Optional[dict] = await bot.safe_function(functools.partial(RateMyProfAPI.get_teacher_info, legacy_id=teacher_id))
    if not teacher:
        return await interaction.response.send_message(ephemeral=True, embed=fail_embed(interaction.user, f"Failed to retrieve teacher with ID `{teacher_id}`."))

    # Disable the select menu
    select.disabled = True
    await interaction.message.edit(
        view=discord.ui.View(select)
    )

    # Generate the teacher result embed
    embed, view, buf = get_teacher_embed(teacher)
    file: Optional[discord.File] = None

    # Attach the image if one is provided
    if buf is not None:
        file: Optional[discord.File] = discord.File(buf, filename="distribution.png")

    # Send the response
    await interaction.response.send_message(embed=embed, view=view, file=file)


if __name__ == '__main__':
    """
    Invite URL:
    https://discord.com/api/oauth2/authorize?client_id=1009311082222977114&permissions=274878024704&scope=bot%20applications.commands
    
    """

    bot.run(open("./resources/token.txt").read())
