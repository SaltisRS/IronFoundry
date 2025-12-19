from discord.app_commands import Group


class Raffle(Group):
    def __init__(self):
        super().__init__(name="raffle")
        """
        Raffle commands group, parent command group for all Raffle commands.
        """
