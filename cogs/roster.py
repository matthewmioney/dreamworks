import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS roster (
    name TEXT,
    rank TEXT
)
""")

conn.commit()

RANK_ORDER = {
    0: "Trainee",
    1: "Mechanic",
    2: "Sr Mechanic",
    3: "Supervisor",
    4: "Assistant Manager",
    5: "Manager"
}

ROLE_IDS = {
    "Manager": 1211555736304357429,
    "Assistant Manager": 1211555736283516945,
    "Supervisor": 1211555736283516945,
    "Sr Mechanic": 1211555736304357426,
    "Mechanic": 1211555736283516947,
    "Trainee": 1211555736283516946
}

def build_roster():

    text = "# 👥 DreamWorks Employee Roster\n\n"

    total = 0

    for rank in RANK_ORDER:

        cursor.execute(
            "SELECT * FROM roster WHERE rank=?",
            (rank,)
        )

        employees = cursor.fetchall()

        total += len(employees)

        text += (
            f"## **{rank} — {len(employees)}**\n"
        )

        if employees:

            for employee in employees:

                text += (
                    f"• {employee[0]}\n"
                )

        else:

            text += "None\n"

        text += "\n"

    text = (
        f"## Total Employees: {total}\n\n"
        + text
    )

    return text


class Roster(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.roster_message = None

    async def update_roster(
        self,
        channel
    ):

        roster_text = build_roster()

        if self.roster_message:

            await self.roster_message.edit(
                content=roster_text
            )

        else:

            self.roster_message = await channel.send(
                roster_text
            )

    @discord.app_commands.command(
        name="setup_roster",
        description="Setup roster"
    )
    async def setup_roster(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            "✅ Roster created.",
            ephemeral=True
        )

        await self.update_roster(
            interaction.channel
        )

    @discord.app_commands.command(
        name="hire",
        description="Hire employee"
    )
    async def hire(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        rank: str
    ):

        valid_ranks = [
            "Manager",
            "Assistant Manager",
            "Supervisor",
            "Sr Mechanic",
            "Mechanic",
            "Trainee"
        ]

        if rank not in valid_ranks:

            await interaction.response.send_message(
                "❌ Invalid rank.",
                ephemeral=True
            )

            return

        cursor.execute(
            """
            INSERT INTO roster
            VALUES (?, ?)
            """,
            (
                member.name,
                rank
            )
        )

        conn.commit()

        role = interaction.guild.get_role(
            ROLE_IDS[rank]
        )

        await member.add_roles(
            role
        )

        await interaction.response.send_message(
            f"✅ Hired {member.mention} as {rank}"
        )

        await self.update_roster(
            interaction.channel
        )

    @discord.app_commands.command(
        name="fire",
        description="Fire employee"
    )
    async def fire(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        cursor.execute(
            """
            DELETE FROM roster
            WHERE name=?
            """,
            (member.name,)
        )

        conn.commit()

        for role_id in ROLE_IDS.values():

            role = interaction.guild.get_role(
                role_id
            )

            if role in member.roles:

                await member.remove_roles(
                    role
                )

        await interaction.response.send_message(
            f"🔥 Fired {member.mention}"
        )

        await self.update_roster(
            interaction.channel
        )

    @discord.app_commands.command(
        name="promote",
        description="Promote employee"
    )
    async def promote(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        cursor.execute(
            """
            SELECT rank FROM roster
            WHERE name=?
            """,
            (member.name,)
        )

        result = cursor.fetchone()

        if not result:

            await interaction.response.send_message(
                "❌ Employee not found."
            )

            return

        current_rank = result[0]

        index = RANK_ORDER.index(
            current_rank
        )

        if index == 0:

            await interaction.response.send_message(
                "❌ Already highest rank."
            )

            return

        new_rank = RANK_ORDER[
            index - 1
        ]

        cursor.execute(
            """
            UPDATE roster
            SET rank=?
            WHERE name=?
            """,
            (
                new_rank,
                member.name
            )
        )

        conn.commit()

        old_role = interaction.guild.get_role(
            ROLE_IDS[current_rank]
        )

        new_role = interaction.guild.get_role(
            ROLE_IDS[new_rank]
        )

        if old_role in member.roles:

            await member.remove_roles(
                old_role
            )

        await member.add_roles(
            new_role
        )

        await interaction.response.send_message(
            f"⬆️ Promoted {member.mention} to {new_rank}"
        )

        await self.update_roster(
            interaction.channel
        )

    @discord.app_commands.command(
        name="demote",
        description="Demote employee"
    )
    async def demote(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        cursor.execute(
            """
            SELECT rank FROM roster
            WHERE name=?
            """,
            (member.name,)
        )

        result = cursor.fetchone()

        if not result:

            await interaction.response.send_message(
                "❌ Employee not found."
            )

            return

        current_rank = result[0]

        index = RANK_ORDER.index(
            current_rank
        )

        if index == len(RANK_ORDER) - 1:

            await interaction.response.send_message(
                "❌ Already lowest rank."
            )

            return

        new_rank = RANK_ORDER[
            index + 1
        ]

        cursor.execute(
            """
            UPDATE roster
            SET rank=?
            WHERE name=?
            """,
            (
                new_rank,
                member.name
            )
        )

        conn.commit()

        old_role = interaction.guild.get_role(
            ROLE_IDS[current_rank]
        )

        new_role = interaction.guild.get_role(
            ROLE_IDS[new_rank]
        )

        if old_role in member.roles:

            await member.remove_roles(
                old_role
            )

        await member.add_roles(
            new_role
        )

        await interaction.response.send_message(
            f"⬇️ Demoted {member.mention} to {new_rank}"
        )

        await self.update_roster(
            interaction.channel
        )

async def setup(bot):

    await bot.add_cog(
        Roster(bot)
    )
