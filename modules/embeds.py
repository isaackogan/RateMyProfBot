import io
import re
import urllib.parse
from typing import Tuple, List

import discord
import numpy as np
from discord.ui import Item
from matplotlib import pyplot as plt

from resources import config

_alpha_only = re.compile("[^a-zA-Z0-9]")
"""Precompiled ReGex for better performance"""


def prof_list_embed() -> discord.Embed:
    """
    Generate the embed directing users to select a professor

    :return: Prof list embed

    """

    return discord.Embed(
        description="Please select a teacher from the available options.",
        colour=config.EMBED_COLOUR_INVIS
    )


def fail_embed(user: discord.User, message: str) -> discord.Embed:
    """
    Generate a fail embed whenever a user action results in an error

    :param user: The user who made the failed request
    :param message: The failure message
    :return: A discord embed describing the error

    """

    embed: discord.Embed = discord.Embed(
        description=f"{config.X_EMOJI} **Error:** {message}",
        colour=config.EMBED_COLOUR_ERROR
    )

    embed.set_author(name=str(user), icon_url=user.avatar.url)

    return embed


def get_teacher_embed(teacher: dict) -> Tuple[discord.Embed, discord.ui.View, io.BytesIO]:
    """
    A really messy function that produces the required embed with a built-in graph image and Discord View

    :param teacher: The teacher to represent as an embed
    :return: The teacher represented as an embed

    """

    # Get basic data
    school: dict = teacher.get('school', dict())
    name: str = f"{teacher.get('firstName')} {teacher.get('lastName')}"
    course_list = [f"`{course.get('course')}`" for course in teacher.get('courses')]
    search_query: str = f"{school.get('name')}, {school.get('city')}, {school.get('state')}"

    # Create Embed
    embed = discord.Embed(
        title=f"{name} - RateMyProf Profile",
        colour=config.EMBED_COLOUR_INVIS,
        description=(
            f"{name} teaches {teacher.get('department')} at "
            f"[**{school.get('name')}**](https://www.google.com/maps?q={urllib.parse.quote(search_query)}&https://www.google.com/maps/search/?api=1&query=pizza+seattle+wa&basemap=satellite) "
            f"in {school.get('city')}, {school.get('state')}."
        )

    )

    embed.add_field(name="_ _\nRating", value=f"{teacher.get('avgRating')} / 5.0")
    embed.add_field(name="_ _\nRating Count", value=f'{teacher.get("numRatings")} Ratings')
    embed.add_field(name="_ _\nDifficulty", value=f"{teacher.get('avgDifficulty')} / 5.0")

    # Get course list
    if course_list:
        embed.add_field(
            name="_ _\nCourses\n_ _",
            value=f"{', '.join(course_list)}\n_ _",
            inline=False
        )

    # Create component List
    items: List[Item] = [
        discord.ui.Button(style=discord.ButtonStyle.url, label="View Teacher Profile", url=f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={teacher.get('legacyId')}"),
        discord.ui.Button(style=discord.ButtonStyle.url, label="View School Profile", url=f"https://www.ratemyprofessors.com/campusRatings.jsp?sid=1302{school.get('legacyId')}"),
    ]

    # Format rating data
    embed.set_image(url="attachment://distribution.png")
    ratings = teacher.get("ratingsDistribution", dict())
    fixed_ratings = {
        f"Awful": ratings.get('r1'),
        f"Okay": ratings.get('r2'),
        f"Good": ratings.get('r3'),
        f"Great": ratings.get('r4'),
        f"Awesome": ratings.get('r5')
    }

    return embed, discord.ui.View(*items), generate_plot(fixed_ratings) if float(teacher.get('numRatings', 0)) > 0 else None


def generate_plot(data: dict):
    fig, ax = plt.subplots()

    # Example data
    people = tuple(data.keys())
    y_pos = np.arange(len(people))
    performance = tuple(data.values())

    ax.barh(y_pos, performance, align='center', color=(1, 1, 1, 1))
    ax.set_yticks(y_pos, labels=people)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_xaxis().set_ticks([])

    ax.set_facecolor((47 / 255, 49 / 255, 54 / 255))
    fig.set_facecolor((47 / 255, 49 / 255, 54 / 255))
    plt.tick_params(left=False)
    ax.tick_params(colors='white', which='both', labelsize=14)

    for bar, value in zip(ax.patches, performance):
        t = ax.text(0.5, bar.get_y() + bar.get_height() / 2, f"{value} Ratings", color='black', ha='left', va='center')
        t.set_bbox(dict(facecolor=(1, 1, 1, 0.5), edgecolor=(0, 0, 0, 0)))

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    return buf
