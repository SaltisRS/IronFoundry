import discord
from discord import app_commands
import json



DATA_FILE = "app/client/commands/foundry_trials.json"
event_data = None


async def team_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    if event_data is None or not event_data.get("teams"):
        return []
    
    teams = event_data["teams"]
    return [
        app_commands.Choice(name=team["teamName"], value=team["teamName"])
        for team in teams
        if current.lower() in team["teamName"].lower()
    ][:25]
    
def load_data():
    global event_data
    try:
        with open(DATA_FILE, 'r') as f:
            event_data = json.load(f)
    except FileNotFoundError:
        event_data = None

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(event_data, f, indent=2)

def is_host(user_id: int) -> bool:
    if event_data is None:
        return False
    return str(user_id) in event_data.get("hosts", [])

def get_user_team(user_id: int):
    if event_data is None:
        return None
    
    for team in event_data["teams"]:
        if str(user_id) in team["members"]:
            return team
    return None

def get_task_template():
    return {
        "sardine_1": {
            "name": "Team Photo",
            "tier": "sardine",
            "description": "Take a screenshot of every team member on the same boat",
            "completed": False,
        },
        "sardine_2": {
            "name": "Rainbow Crabs",
            "tier": "sardine",
            "description": "Obtain 500 rainbow crab meat",
            "completed": False
        },
        "sardine_3": {
            "name": "Course Completions",
            "tier": "sardine",
            "description": "Complete 200 Marlin courses",
            "completed": False
        },
        "sardine_4": {
            "name": "Coral Farmers",
            "tier": "sardine",
            "description": "Each team member plants a bed of coral and takes a screenshot",
            "completed": False
        },
        "swordfish_1": {
            "name": "Salvage Uniques",
            "tier": "swordfish",
            "description": "Obtain 5 different uniques from salvage that awards kudos",
            "completed": False
        },
        "swordfish_2": {
            "name": "Bell's Folly",
            "tier": "swordfish",
            "description": "Obtain Bell's Folly",
            "completed": False
        },
        "swordfish_3": {
            "name": "Squid Beaks",
            "tier": "swordfish",
            "description": "Obtain 4 squid beaks",
            "completed": False
        },
        "swordfish_4": {
            "name": "Albatross Feathers",
            "tier": "swordfish",
            "description": "Obtain 16 swift albatross feathers",
            "completed": False
        },
        "shark_1": {
            "name": "Deep Sea Fishing",
            "tier": "shark",
            "description": "Obtain 5000 deep sea trawling fish",
            "completed": False
        },
        "shark_2": {
            "name": "Rare Fish",
            "tier": "shark",
            "description": "Obtain any rare deep sea trawling fish",
            "completed": False
        },
        "shark_3": {
            "name": "Sailing Experience",
            "tier": "shark",
            "description": "Gain 10 mil sailing exp (WiseOldMan)",
            "completed": False
        },
        "shark_4": {
            "name": "Bottled Storm",
            "tier": "shark",
            "description": "Obtain a bottled storm",
            "completed": False
        },
        "marlin_1": {
            "name": "Dragon Sheets",
            "tier": "marlin",
            "description": "Obtain 20 dragon sheets",
            "completed": False
        },
        "marlin_2": {
            "name": "Speed Records",
            "tier": "marlin",
            "description": "Beat every marlin course by 10 seconds (20 seconds Rosewood Hulls)",
            "completed": False,
        },
        "marlin_3": {
            "name": "Dragon Cannon",
            "tier": "marlin",
            "description": "Obtain a broken dragon cannon",
            "completed": False
        },
        "marlin_4": {
            "name": "Dragon Hook",
            "tier": "marlin",
            "description": "Obtain a broken dragon hook",
            "completed": False
        }
    }

@app_commands.command(name="initialize_event", description="Initialize the Foundry Trials event")
async def initialize_event(interaction: discord.Interaction):
    global event_data
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is not None:
        await interaction.response.send_message(
            "⚠️ Event already initialized! Use `/reset_event` to start over.",
            ephemeral=True
        )
        return

    event_data = {
        "pointValues": {
            "sardine": 1,
            "swordfish": 2,
            "shark": 3,
            "marlin": 4
        },
        "hosts": [],
        "teams": []
    }
    
    save_data()
    await interaction.response.send_message(
        "✅ The Foundry Trials event has been initialized!",
        ephemeral=True
    )

@app_commands.command(name="add_host", description="Add a host who can manage the event")
async def add_host(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized! Use `/initialize_event` first.",
            ephemeral=True
        )
        return

    if str(member.id) in event_data["hosts"]:
        await interaction.response.send_message(
            f"❌ {member.mention} is already a host!",
            ephemeral=True
        )
        return

    event_data["hosts"].append(str(member.id))
    save_data()
    
    await interaction.response.send_message(
        f"✅ {member.mention} has been added as a host!",
        ephemeral=True
    )

@app_commands.command(name="remove_host", description="Remove a host")
async def remove_host(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    if str(member.id) not in event_data["hosts"]:
        await interaction.response.send_message(
            f"❌ {member.mention} is not a host!",
            ephemeral=True
        )
        return

    event_data["hosts"].remove(str(member.id))
    save_data()
    
    await interaction.response.send_message(
        f"✅ {member.mention} has been removed as a host!",
        ephemeral=True
    )

@app_commands.command(name="create_team", description="Create a new team")
async def create_team(interaction: discord.Interaction, team_name: str):
    if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
        await interaction.response.send_message(
            "❌ You need host permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized! Use `/initialize_event` first.",
            ephemeral=True
        )
        return

    for team in event_data["teams"]:
        if team["teamName"].lower() == team_name.lower():
            await interaction.response.send_message(
                f"❌ Team '{team_name}' already exists!",
                ephemeral=True
            )
            return

    new_team = {
        "teamName": team_name,
        "members": [],
        "totalPoints": 0,
        "tasks": get_task_template()
    }

    event_data["teams"].append(new_team)
    save_data()
    
    await interaction.response.send_message(
        f"✅ Team '{team_name}' has been created!",
        ephemeral=True
    )

@app_commands.command(name="add_member", description="Add a member to a team")
@app_commands.autocomplete(team_name=team_name_autocomplete)
async def add_member(interaction: discord.Interaction, team_name: str, member: discord.Member):
    if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
        await interaction.response.send_message(
            "❌ You need host permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    team = None
    for t in event_data["teams"]:
        if t["teamName"].lower() == team_name.lower():
            team = t
            break

    if team is None:
        await interaction.response.send_message(
            f"❌ Team '{team_name}' not found!",
            ephemeral=True
        )
        return

    for t in event_data["teams"]:
        if str(member.id) in t["members"]:
            await interaction.response.send_message(
                f"❌ {member.mention} is already on team '{t['teamName']}'!",
                ephemeral=True
            )
            return

    if len(team["members"]) >= 4:
        await interaction.response.send_message(
            f"❌ Team '{team_name}' is full (max 4 members)!",
            ephemeral=True
        )
        return

    team["members"].append(str(member.id))
    save_data()

    await interaction.response.send_message(
        f"✅ Added {member.mention} to team '{team_name}'!",
        ephemeral=True
    )

@app_commands.command(name="remove_member", description="Remove a member from their team")
async def remove_member(interaction: discord.Interaction, member: discord.Member):
    if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
        await interaction.response.send_message(
            "❌ You need host permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    for team in event_data["teams"]:
        if str(member.id) in team["members"]:
            team["members"].remove(str(member.id))
            save_data()
            await interaction.response.send_message(
                f"✅ Removed {member.mention} from team '{team['teamName']}'!",
                ephemeral=True
            )
            return

    await interaction.response.send_message(
        f"❌ {member.mention} is not on any team!",
        ephemeral=True
    )

@app_commands.command(name="view_team", description="View team information")
@app_commands.autocomplete(team_name=team_name_autocomplete)
async def view_team(interaction: discord.Interaction, team_name: str):
    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    team = None
    for t in event_data["teams"]:
        if t["teamName"].lower() == team_name.lower():
            team = t
            break

    if team is None:
        await interaction.response.send_message(
            f"❌ Team '{team_name}' not found!",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🏴☠️ {team['teamName']}",
        color=discord.Color.blue()
    )

    members_list = []
    for member_id in team["members"]:
        member = interaction.guild.get_member(int(member_id))
        if member:
            members_list.append(member.mention)
        else:
            members_list.append(f"<@{member_id}>")
    
    embed.add_field(
        name="Members",
        value="\n".join(members_list) if members_list else "No members",
        inline=False
    )

    tier_stats = {
        "sardine": {"completed": 0, "total": 0},
        "swordfish": {"completed": 0, "total": 0},
        "shark": {"completed": 0, "total": 0},
        "marlin": {"completed": 0, "total": 0}
    }

    for task in team["tasks"].values():
        tier = task["tier"]
        tier_stats[tier]["total"] += 1
        if task["completed"]:
            tier_stats[tier]["completed"] += 1

    progress_text = ""
    for tier, stats in tier_stats.items():
        progress_text += f"**{tier.capitalize()}**: {stats['completed']}/{stats['total']}\n"

    embed.add_field(name="Progress", value=progress_text, inline=False)
    embed.add_field(name="Total Points", value=str(team["totalPoints"]), inline=False)

    await interaction.response.send_message(embed=embed)

@app_commands.command(name="leaderboard", description="View the event leaderboard")
async def leaderboard(interaction: discord.Interaction):
    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    if not event_data["teams"]:
        await interaction.response.send_message(
            "❌ No teams created yet!",
            ephemeral=True
        )
        return

    sorted_teams = sorted(
        event_data["teams"],
        key=lambda x: x["totalPoints"],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 The Foundry Trials Leaderboard",
        color=discord.Color.gold()
    )

    for i, team in enumerate(sorted_teams, 1):
        completed_tasks = sum(
            1 for task in team["tasks"].values() if task["completed"]
        )
        total_tasks = len(team["tasks"])
        
        embed.add_field(
            name=f"{i}. {team['teamName']}",
            value=f"Points: {team['totalPoints']} | Tasks: {completed_tasks}/{total_tasks}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@app_commands.command(name="list_teams", description="List all teams")
async def list_teams(interaction: discord.Interaction):
    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    if not event_data["teams"]:
        await interaction.response.send_message(
            "❌ No teams created yet!",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📋 All Teams",
        color=discord.Color.blue()
    )

    for team in event_data["teams"]:
        member_count = len(team["members"])
        embed.add_field(
            name=team["teamName"],
            value=f"Members: {member_count}/4",
            inline=True
        )

    await interaction.response.send_message(embed=embed)

class SubmissionView(discord.ui.View):
    def __init__(self, team_name: str, task_id: str, submitter: discord.Member):
        super().__init__(timeout=None)
        self.team_name = team_name
        self.task_id = task_id
        self.submitter = submitter

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_submission")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
            await interaction.response.send_message(
                "❌ Only hosts can accept submissions!",
                ephemeral=True
            )
            return

        # Find the team
        team = None
        for t in event_data["teams"]:
            if t["teamName"].lower() == self.team_name.lower():
                team = t
                break

        if team is None:
            await interaction.response.send_message(
                "❌ Team not found!",
                ephemeral=True
            )
            return

        # Update task
        if self.task_id in team["tasks"]:
            task = team["tasks"][self.task_id]
            task["completed"] = True
            
            # Update total points
            tier = task["tier"]
            points = event_data["pointValues"][tier]
            team["totalPoints"] += points
            
            save_data()

            # Update the embed
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.add_field(
                name="Status",
                value=f"✅ Accepted by {interaction.user.mention}",
                inline=False
            )

            # Disable buttons
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(embed=embed, view=self)
            
            # Send confirmation
            await interaction.followup.send(
                f"✅ Accepted submission for **{task['name']}** from team **{self.team_name}**!\n"
                f"Team awarded **{points} points**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Task not found!",
                ephemeral=True
            )

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="deny_submission")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
            await interaction.response.send_message(
                "❌ Only hosts can deny submissions!",
                ephemeral=True
            )
            return

        # Update the embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(
            name="Status",
            value=f"❌ Denied by {interaction.user.mention}",
            inline=False
        )

        # Disable buttons
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        
        await interaction.followup.send(
            f"❌ Denied submission from team **{self.team_name}**.",
            ephemeral=True
        )

async def task_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    if event_data is None:
        return []
    
    # Get the user's team
    team = get_user_team(interaction.user.id)
    if team is None:
        return []
    
    # Get incomplete tasks
    tasks = []
    for task_id, task in team["tasks"].items():
        if not task["completed"]:
            task_name = f"{task['name']} ({task['tier'].capitalize()})"
            if current.lower() in task_name.lower():
                tasks.append(app_commands.Choice(name=task_name, value=task_id))
    
    return tasks[:25]

@app_commands.command(name="submit", description="Submit a task completion for review")
@app_commands.autocomplete(task=task_autocomplete)
async def submit(
    interaction: discord.Interaction,
    task: str,
    evidence: discord.Attachment
):
    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    # Get the user's team
    team = get_user_team(interaction.user.id)
    if team is None:
        await interaction.response.send_message(
            "❌ You are not on a team!",
            ephemeral=True
        )
        return

    # Check if task exists and is not completed
    if task not in team["tasks"]:
        await interaction.response.send_message(
            "❌ Invalid task!",
            ephemeral=True
        )
        return

    task_obj = team["tasks"][task]
    
    if task_obj["completed"]:
        await interaction.response.send_message(
            "❌ This task has already been completed!",
            ephemeral=True
        )
        return

    # Create embed
    embed = discord.Embed(
        title="📝 Task Submission",
        color=discord.Color.blue()
    )
    embed.add_field(name="Team", value=team["teamName"], inline=True)
    embed.add_field(name="Task", value=task_obj["name"], inline=True)
    embed.add_field(name="Tier", value=task_obj["tier"].capitalize(), inline=True)
    embed.add_field(name="Description", value=task_obj["description"], inline=False)
    
    if evidence:
        embed.add_field(name="Evidence", value=evidence, inline=False)
    
    embed.add_field(name="Submitted By", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"Task ID: {task}")

    # Create view
    view = SubmissionView(team["teamName"], task, interaction.user)

    await interaction.response.send_message(embed=embed, view=view)
    
@app_commands.command(name="delete_team", description="Delete a team")
@app_commands.describe(team_name="The team to delete")
@app_commands.autocomplete(team_name=team_name_autocomplete)
async def delete_team(interaction: discord.Interaction, team_name: str):
    if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
        await interaction.response.send_message(
            "❌ You need host permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    # Find and remove the team
    for i, team in enumerate(event_data["teams"]):
        if team["teamName"].lower() == team_name.lower():
            event_data["teams"].pop(i)
            save_data()
            await interaction.response.send_message(
                f"✅ Team '{team_name}' has been deleted!",
                ephemeral=True
            )
            return

    await interaction.response.send_message(
        f"❌ Team '{team_name}' not found!",
        ephemeral=True
    )

@app_commands.command(name="rename_team", description="Rename a team")
@app_commands.describe(
    old_name="Current team name",
    new_name="New team name"
)
@app_commands.autocomplete(old_name=team_name_autocomplete)
async def rename_team(interaction: discord.Interaction, old_name: str, new_name: str):
    if not (interaction.user.guild_permissions.administrator or is_host(interaction.user.id)):
        await interaction.response.send_message(
            "❌ You need host permissions to use this command!",
            ephemeral=True
        )
        return

    if event_data is None:
        await interaction.response.send_message(
            "❌ Event not initialized!",
            ephemeral=True
        )
        return

    # Find the team with old name
    team = None
    for t in event_data["teams"]:
        if t["teamName"].lower() == old_name.lower():
            team = t
            break

    if team is None:
        await interaction.response.send_message(
            f"❌ Team '{old_name}' not found!",
            ephemeral=True
        )
        return

    # Check if new name already exists
    for t in event_data["teams"]:
        if t["teamName"].lower() == new_name.lower():
            await interaction.response.send_message(
                f"❌ Team '{new_name}' already exists!",
                ephemeral=True
            )
            return

    # Update the name
    team["teamName"] = new_name
    save_data()

    await interaction.response.send_message(
        f"✅ Team '{old_name}' has been renamed to '{new_name}'!",
        ephemeral=True
    )
    
    
async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(submit, guild=guild)
    client.tree.add_command(add_host, guild=guild)
    client.tree.add_command(remove_host, guild=guild)
    client.tree.add_command(initialize_event, guild=guild)
    client.tree.add_command(add_member, guild=guild)
    client.tree.add_command(remove_member, guild=guild)
    client.tree.add_command(create_team, guild=guild)
    client.tree.add_command(view_team, guild=guild)
    client.tree.add_command(list_teams, guild=guild)
    client.tree.add_command(leaderboard, guild=guild)
    client.tree.add_command(rename_team, guild=guild)
    client.tree.add_command(delete_team, guild=guild)