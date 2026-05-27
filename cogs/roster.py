import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS roster (
    user_id INTEGER,
    name TEXT,
    rank TEXT
)
""")

conn.commit()

RANK_ORDER = [
    "Manager",
    "Assistant Manager",
    "Supervisor",
    "Sr Mechanic",
    "Mechanic",
    "Trainee"
]

RANK_NUMBERS = {
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


def build_roster_embed(guild):

    total = 0

    embed = discord.Embed(
        title="DreamWorks Team Roster",
        color=discord.Color.dark_gray()
    )

    for rank in RANK_ORDER:

        cursor.execute(
            "SELECT * FROM roster WHERE rank=?",
            (rank,)
        )

        employees = cursor.fetchall()

        total += len(employees)

        employee_text = ""

        if employees:

            for employee in employees:

                member = guild.get_member(
                    employee[0]
                )

                if member:

                    display_name = (
                        member.display_name
                    )

                else:

                    display_name = employee[1]

                employee_text += (
                    f"• {display_name}\n"
                )

        else:

            employee_text = "None"

        embed.add_field(
            name=f"{rank} — {len(employees)}",
            value=employee_text,
            inline=False
        )

    embed.description = (
        f"**Total Employees: {total}**"
    )

    embed.set_footer(
        text="/hire [user] [rank] • "
             "/fire [user] • "
             "/promote [user] • "
             "/demote [user] • "
             "/roster"
    )

    return embed


class Roster(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.roster_message = None

    async def update_roster(
        self,
        channel
    ):

        roster_embed = build_roster_embed(
            channel.guild
        )

        if self.roster_message:

            await self.roster_message.edit(
                embed=roster_embed
            )

        else:

            self.roster_message = await channel.send(
                embed=roster_embed
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
        name="roster",
        description="Show roster"
    )
    async def roster(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            embed=build_roster_embed(
                interaction.guild
            )
        )

    @discord.app_commands.command(
        name="hire",
        description="Hire employee"
    )
    async def hire(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        rank: int
    ):

        if rank not in RANK_NUMBERS:

            await interaction.response.send_message(
                "❌ Invalid rank.",
                ephemeral=True
            )

            return

        rank_name = RANK_NUMBERS[rank]

        cursor.execute(
            """
            INSERT INTO roster
            VALUES (?, ?, ?)
            """,
            (
                member.id,
                member.display_name,
                rank_name
            )
        )

        conn.commit()

        role = interaction.guild.get_role(
            ROLE_IDS[rank_name]
        )

        await member.add_roles(
            role
        )

        await interaction.response.send_message(
            f"✅ Hired {member.display_name} as {rank_name}",
            ephemeral=True
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
            WHERE user_id=?
            """,
            (member.id,)
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
            f"🔥 Fired {member.display_name}",
            ephemeral=True
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
            WHERE user_id=?
            """,
            (member.id,)
        )

        result = cursor.fetchone()

        if not result:

            await interaction.response.send_message(
                "❌ Employee not found.",
                ephemeral=True
            )

            return

        current_rank = result[0]

        rank_list = list(
            RANK_NUMBERS.values()
        )

        index = rank_list.index(
            current_rank
        )

        if index == len(rank_list) - 1:

            await interaction.response.send_message(
                "❌ Already highest rank.",
                ephemeral=True
            )

            return

        new_rank = rank_list[
            index + 1
        ]

        cursor.execute(
            """
            UPDATE roster
            SET rank=?
            WHERE user_id=?
            """,
            (
                new_rank,
                member.id
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
            f"⬆️ Promoted {member.display_name} to {new_rank}",
            ephemeral=True
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
            WHERE user_id=?
            """,
            (member.id,)
        )

        result = cursor.fetchone()

        if not result:

            await interaction.response.send_message(
                "❌ Employee not found.",
                ephemeral=True
            )

            return

        current_rank = result[0]

        rank_list = list(
            RANK_NUMBERS.values()
        )

        index = rank_list.index(
            current_rank
        )

        if index == 0:

            await interaction.response.send_message(
                "❌ Already lowest rank.",
                ephemeral=True
            )

            return

        new_rank = rank_list[
            index - 1
        ]

        cursor.execute(
            """
            UPDATE roster
            SET rank=?
            WHERE user_id=?
            """,
            (
                new_rank,
                member.id
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
            f"⬇️ Demoted {member.display_name} to {new_rank}",
            ephemeral=True
        )

        await self.update_roster(
            interaction.channel
        )

async def setup(bot):

    await bot.add_cog(
        Roster(bot)
    )
