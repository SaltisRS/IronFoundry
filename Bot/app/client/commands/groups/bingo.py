from discord.app_commands import Group


class Bingo(Group):
    def __init__(self):
        super().__init__(name="bingo")
        """
        Bingo commands group, parent command group for all bingo commands.
        """
        