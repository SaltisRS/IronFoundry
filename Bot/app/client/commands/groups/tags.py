from discord.app_commands import Group


class Tags(Group):
    def __init__(self):
        super().__init__(name="tags")
