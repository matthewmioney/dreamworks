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
    code TEXT,
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

ROLE_IDS = {
    "Manager": 1211555736304357429,
    "Assistant Manager": 1211555736283516945,
    "Supervisor": 1211555736283516945,
    "Sr Mechanic": 1211555736304357426,
    "Mechanic": 1211555736283516947,
    "Trainee": 1211555736283516946
}


# =========================
# BUILD ROSTER
# =========================

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
                    f"• {employee[0]} "
                    f"[{employee[1]}]\n"
                )

        else:

            text += "None\n"

        text += "\n"

    text = (
        f"## Total Employees: {total}\n\n"
        + text
    )

    return text


# =========================
# COG
# =========================

class Roster(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.roster_message = None

    async def update_roster(
        self,
        ctx
    ):

        roster_text = build_roster()

        if self.roster_message:

            await self.roster_message.edit(
                content=roster_text
            )

        else:

            self.roster_message = await ctx.send(
                roster_text
            )

    # =========================
    # SETUP ROSTER
    # =========================

    @commands.command()
    async def setup_roster(
        self,
        ctx
    ):

        await self.update_roster(
            ctx
        )

    # =========================
    # HIRE
    # =========================

    @commands.command()
    async def hire(
        self,
        ctx,
        member: discord.Member,
        code: str
    ):

        cursor.execute(
            """
            INSERT INTO roster
            VALUES (?, ?, ?)
            """,
            (
                member.name,
                code,
                "Trainee"
            )
        )

        conn.commit()

        trainee_role = ctx.guild.get_role(
            ROLE_IDS["Trainee"]
        )

        await member.add_roles(
            trainee_role
        )

        await ctx.send(
            f"✅ Hired {member.mention}"
        )

        await self.update_roster(
            ctx
        )

    # =========================
    # FIRE
    # =========================

    @commands.command()
    async def fire(
        self,
        ctx,
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

            role = ctx.guild.get_role(
                role_id
            )

            if role in member.roles:

                await member.remove_roles(
                    role
                )

        await ctx.send(
            f"🔥 Fired {member.mention}"
        )

        await self.update_roster(
            ctx
        )

    # =========================
    # PROMOTE
    # =========================

    @commands.command()
    async def promote(
        self,
        ctx,
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

            await ctx.send(
                "❌ Employee not found."
            )

            return

        current_rank = result[0]

        index = RANK_ORDER.index(
            current_rank
        )

        if index == 0:

            await ctx.send(
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

        old_role = ctx.guild.get_role(
            ROLE_IDS[current_rank]
        )

        new_role = ctx.guild.get_role(
            ROLE_IDS[new_rank]
        )

        if old_role in member.roles:

            await member.remove_roles(
                old_role
            )

        await member.add_roles(
            new_role
        )

        await ctx.send(
            f"⬆️ Promoted {member.mention} to {new_rank}"
        )

        await self.update_roster(
            ctx
        )

    # =========================
    # DEMOTE
    # =========================

    @commands.command()
    async def demote(
        self,
        ctx,
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

            await ctx.send(
                "❌ Employee not found."
            )

            return

        current_rank = result[0]

        index = RANK_ORDER.index(
            current_rank
        )

        if index == len(RANK_ORDER) - 1:

            await ctx.send(
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

        old_role = ctx.guild.get_role(
            ROLE_IDS[current_rank]
        )

        new_role = ctx.guild.get_role(
            ROLE_IDS[new_rank]
        )

        if old_role in member.roles:

            await member.remove_roles(
                old_role
            )

        await member.add_roles(
            new_role
        )

        await ctx.send(
            f"⬇️ Demoted {member.mention} to {new_rank}"
        )

        await self.update_roster(
            ctx
        )

async def setup(bot):

    await bot.add_cog(
        Roster(bot)
    )