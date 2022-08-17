from typing import Callable, List

import discord
from discord import Interaction
from discord.ui import Select


def teacher_list_view(teachers: List[dict], callback: Callable) -> discord.ui.View:
    """
    Generate a teacher list view for searching teachers

    :param teachers: Teacher list
    :param callback: Function to run on select interaction
    :return: A UI View with the requested options

    """

    options: List[discord.SelectOption] = []

    # Build select options (only first 24 due to Select limitations)
    for teacher in teachers[:24]:
        options.append(discord.SelectOption(
            value=str(teacher.get("id")),
            description=teacher.get("school"),
            label=f"{teacher.get('first_name')} {teacher.get('last_name')}"
        ))

    # Create view
    class TeacherList(discord.ui.View):
        """
        Create the view

        """

        @discord.ui.select(placeholder="Choose a Teacher", min_values=1, max_values=1, options=options)
        async def select_callback(self, select: Select, interaction: Interaction):
            select.disabled = True
            await callback(select, interaction)

    # Instantiate and return view
    return TeacherList()
