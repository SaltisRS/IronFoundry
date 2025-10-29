from discord.app_commands import Group


class System(Group):
    def __init__(self):
        super().__init__(name="system")
        """
        System commands group, parent command group for all system commands.
        
        Only the system owner can use these commands.
        """
