import discord
from discord.ext import commands
from discord import app_commands
import json
import os

ROSTER_FILE = "roster.json"

# =========================
# RANKS
# =========================

RANK_NAMES = {
    "0": "Trainee",
    "1": "Mechanic",
    "2": "Sr Mechanic",
    "3": "Supervisor",
    "4": "Assistant Manager",
    "5": "Manager"
}

VALID_RANKS = list(RANK_NAMES.keys())

# =========================
# ROLE IDS
# =========================

ROLE_IDS = {
    "5": 1211555736304357428
}

# =========================
# LOAD / SAVE
# =========================

def load_roster():

    if not os.path.exists(ROSTER_FILE):
        return {}

    with open(ROSTER_FILE, "r") as f:
        return json.load(f)


def save_roster(data):

    with open(ROSTER_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# COG
# =========================

class Roster(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # SETUP ROSTER
    # =========================

    @app_commands.command(
        name="setup_roster",
        description="Create the roster file"
    )
    async def setup_roster(self, interaction: discord.Interaction):

        if not os.path.exists(ROSTER_FILE):

            save_roster({})

            await interaction.response.send_message(
                "✅ Roster created.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "⚠️ Roster already exists.",
                ephemeral=True
            )

    # =========================
    # HIRE
    # =========================

    @app_commands.command(
        name="hire",
        description="Hire a user"
    )

    @app_commands.describe(
        member="User to hire",
        rank="Rank number (0-5)"
    )

    async def hire(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        rank: str
    ):

        if rank not in VALID_RANKS:

            await interaction.response.send_message(
                "❌ Invalid rank. Use 0-5.",
                ephemeral=True
            )

            return

        roster = load_roster()

        roster[str(member.id)] = {
            "name": member.display_name,
            "rank": rank
        }

        save_roster(roster)

        # GIVE ROLE

        if rank in ROLE_IDS:

            role = interaction.guild.get_role(
                ROLE_IDS[rank]
            )

            if role:
                await member.add_roles(role)

        embed = discord.Embed(
            title="✅ User Hired",
            color=discord.Color.green()
        )

        embed.add_field(
            name="User",
            value=member.display_name,
            inline=True
        )

        embed.add_field(
            name="Rank",
            value=f"{rank} - {RANK_NAMES[rank]}",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )

    # =========================
    # FIRE
    # =========================

    @app_commands.command(
        name="fire",
        description="Fire a user"
    )

    async def fire(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        roster = load_roster()

        if str(member.id) not in roster:

            await interaction.response.send_message(
                "❌ User is not in the roster.",
                ephemeral=True
            )

            return

        old_rank = roster[str(member.id)]["rank"]

        # REMOVE ROLE

        if old_rank in ROLE_IDS:

            role = interaction.guild.get_role(
                ROLE_IDS[old_rank]
            )

            if role:
                await member.remove_roles(role)

        del roster[str(member.id)]

        save_roster(roster)

        await interaction.response.send_message(
            f"🔥 {member.display_name} has been fired."
        )

    # =========================
    # PROMOTE
    # =========================

    @app_commands.command(
        name="promote",
        description="Promote a user"
    )

    async def promote(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        roster = load_roster()

        if str(member.id) not in roster:

            await interaction.response.send_message(
                "❌ User is not in the roster.",
                ephemeral=True
            )

            return

        current_rank = int(
            roster[str(member.id)]["rank"]
        )

        if current_rank >= 5:

            await interaction.response.send_message(
                "❌ User is already max rank.",
                ephemeral=True
            )

            return

        new_rank = str(current_rank + 1)
        old_rank = str(current_rank)

        # REMOVE OLD ROLE

        if old_rank in ROLE_IDS:

            old_role = interaction.guild.get_role(
                ROLE_IDS[old_rank]
            )

            if old_role:
                await member.remove_roles(old_role)

        # GIVE NEW ROLE

        if new_rank in ROLE_IDS:

            new_role = interaction.guild.get_role(
                ROLE_IDS[new_rank]
            )

            if new_role:
                await member.add_roles(new_role)

        roster[str(member.id)]["rank"] = new_rank

        save_roster(roster)

        await interaction.response.send_message(
            f"⬆️ {member.display_name} promoted to "
            f"{new_rank} - {RANK_NAMES[new_rank]}"
        )

    # =========================
    # DEMOTE
    # =========================

    @app_commands.command(
        name="demote",
        description="Demote a user"
    )

    async def demote(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        roster = load_roster()

        if str(member.id) not in roster:

            await interaction.response.send_message(
                "❌ User is not in the roster.",
                ephemeral=True
            )

            return

        current_rank = int(
            roster[str(member.id)]["rank"]
        )

        if current_rank <= 0:

            await interaction.response.send_message(
                "❌ User is already lowest rank.",
                ephemeral=True
            )

            return

        new_rank = str(current_rank - 1)
        old_rank = str(current_rank)

        # REMOVE OLD ROLE

        if old_rank in ROLE_IDS:

            old_role = interaction.guild.get_role(
                ROLE_IDS[old_rank]
            )

            if old_role:
                await member.remove_roles(old_role)

        # GIVE NEW ROLE

        if new_rank in ROLE_IDS:

            new_role = interaction.guild.get_role(
                ROLE_IDS[new_rank]
            )

            if new_role:
                await member.add_roles(new_role)

        roster[str(member.id)]["rank"] = new_rank

        save_roster(roster)

        await interaction.response.send_message(
            f"⬇️ {member.display_name} demoted to "
            f"{new_rank} - {RANK_NAMES[new_rank]}"
        )

    # =========================
    # VIEW ROSTER
    # =========================

    @app_commands.command(
        name="roster",
        description="View the team roster"
    )

    async def roster(self, interaction: discord.Interaction):

        data = load_roster()

        role_order = {
            "5": "Manager",
            "4": "Assistant Manager",
            "3": "Supervisor",
            "2": "Sr Mechanic",
            "1": "Mechanic",
            "0": "Trainee"
        }

        grouped = {
            "5": [],
            "4": [],
            "3": [],
            "2": [],
            "1": [],
            "0": []
        }

        for user_id, info in data.items():

            rank = info["rank"]

            if rank in grouped:
                grouped[rank].append(info["name"])

        total_employees = len(data)

        embed = discord.Embed(
            title="# 👥 DREAMWORKS\n# TEAM ROSTER",
            description=f"### Total Employees: {total_employees}\n\u200b",
            color=discord.Color.dark_gray()
        )

        embed.set_footer(
            text=(
                "/hire [user] [rank] • "
                "/fire [user] • "
                "/promote [user] • "
                "/demote [user] • "
                "/roster"
            )
        )

        for rank in ["5", "4", "3", "2", "1", "0"]:

            users = grouped[rank]

            role_name = role_order[rank]

            count = len(users)

            if users:

                user_list = "\n".join(
                    [f"• {u}" for u in users]
                )

            else:

                user_list = "None"

            embed.add_field(
                name=f"{role_name} — {count}",
                value=user_list,
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Roster(bot))
