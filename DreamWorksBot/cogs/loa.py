import discord
from discord.ext import commands, tasks
from datetime import datetime
import sqlite3

ADMIN_ROLE_ID = 1211555736304357429

RANK_ROLES = {
    1287680549137420401: "Owner",
    1211555736304357429: "Manager",
    1211555736283516945: "Supervisor",
    1211555736304357426: "Sr. Mechanic",
    1211555736283516947: "Mechanic",
    1211555736283516946: "Trainee"
}

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS loas (
    user_id TEXT,
    end_date TEXT,
    message_id TEXT,
    channel_id TEXT
)
""")

conn.commit()

active_loas = {}

def get_rank(member):

    for role_id, rank_name in RANK_ROLES.items():

        role = member.guild.get_role(
            role_id
        )

        if role in member.roles:

            return rank_name

    return "Unknown"


# =========================
# LOA MODAL
# =========================

class LOAModal(
    discord.ui.Modal,
    title="Leave Of Absence Form"
):

    start_date = discord.ui.TextInput(
        label="Start Date",
        placeholder="MM/DD/YYYY",
        required=True
    )

    end_date = discord.ui.TextInput(
        label="End Date",
        placeholder="MM/DD/YYYY",
        required=True
    )

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        rank = get_rank(
            interaction.user
        )

        embed = discord.Embed(
            title="📋 Leave Of Absence",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Employee",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Rank",
            value=rank,
            inline=False
        )

        embed.add_field(
            name="Start Date",
            value=self.start_date.value,
            inline=True
        )

        embed.add_field(
            name="End Date",
            value=self.end_date.value,
            inline=True
        )

        embed.add_field(
            name="Reason",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="Status",
            value="LOA Active",
            inline=False
        )

        current_date = datetime.now().strftime(
            "%m/%d/%Y"
        )

        embed.set_footer(
            text=f"Submitted on {current_date}"
        )

        admin_role = f"<@&{ADMIN_ROLE_ID}>"

        msg = await interaction.channel.send(
            content=f"{interaction.user.mention} {admin_role}",
            embed=embed
        )

        active_loas[
            interaction.user.id
        ] = msg.id

        cursor.execute(
            """
            INSERT INTO loas (
                user_id,
                end_date,
                message_id,
                channel_id
            ) VALUES (?, ?, ?, ?)
            """,
            (
                str(interaction.user.id),
                self.end_date.value,
                str(msg.id),
                str(interaction.channel.id)
            )
        )

        conn.commit()

        await interaction.response.send_message(
            "✅ LOA submitted successfully.",
            ephemeral=True
        )


# =========================
# ADMIN PANEL
# =========================

class AdminPanel(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="View Active LOAs",
        style=discord.ButtonStyle.blurple
    )
    async def view_loas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not active_loas:

            await interaction.response.send_message(
                "❌ No active LOAs.",
                ephemeral=True
            )

            return

        text = ""

        for user_id in active_loas:

            user = await interaction.client.fetch_user(
                user_id
            )

            text += f"• {user.name}\n"

        embed = discord.Embed(
            title="📋 Active LOAs",
            description=text,
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="Clear All LOAs",
        style=discord.ButtonStyle.red
    )
    async def clear_loas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        active_loas.clear()

        embed = discord.Embed(
            title="🛑 LOAs Cleared",
            description="All active LOAs removed.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================
# COG
# =========================

class LOA(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        if not self.check_expired_loas.is_running():
            self.check_expired_loas.start()

    @tasks.loop(minutes=30)
    async def check_expired_loas(self):

        now = datetime.now()

        cursor.execute(
            "SELECT * FROM loas"
        )

        rows = cursor.fetchall()

        for row in rows:

            user_id = int(row[0])
            end_date = row[1]
            message_id = int(row[2])
            channel_id = int(row[3])

            try:

                end = datetime.strptime(
                    end_date,
                    "%m/%d/%Y"
                )

                if now >= end:

                    channel = self.bot.get_channel(
                        channel_id
                    )

                    message = await channel.fetch_message(
                        message_id
                    )

                    embed = message.embeds[0]

                    new_embed = discord.Embed(
                        title=embed.title,
                        color=discord.Color.red()
                    )

                    for field in embed.fields:

                        if field.name == "Status":

                            new_embed.add_field(
                                name="Status",
                                value="LOA Ended",
                                inline=False
                            )

                        else:

                            new_embed.add_field(
                                name=field.name,
                                value=field.value,
                                inline=field.inline
                            )

                    await message.edit(
                        embed=new_embed
                    )

                    await channel.send(
                        f"<@{user_id}> your LOA has ended."
                    )

                    cursor.execute(
                        "DELETE FROM loas WHERE user_id=?",
                        (str(user_id),)
                    )

                    conn.commit()

            except:
                pass

    @discord.app_commands.command(
        name="loa",
        description="Submit a Leave of Absence request"
    )
    async def loa(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_modal(
            LOAModal()
        )

    @discord.app_commands.command(
        name="loacancel",
        description="Cancel your active LOA"
    )
    async def loacancel(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id not in active_loas:

            await interaction.response.send_message(
                "❌ You do not have an active LOA.",
                ephemeral=True
            )

            return

        del active_loas[
            interaction.user.id
        ]

        await interaction.response.send_message(
            "✅ LOA cancelled.",
            ephemeral=True
        )

    @discord.app_commands.command(
        name="panel",
        description="Open LOA admin panel"
    )
    async def panel(
        self,
        interaction: discord.Interaction
    ):

        role = interaction.guild.get_role(
            ADMIN_ROLE_ID
        )

        if role not in interaction.user.roles:

            await interaction.response.send_message(
                "❌ You are not authorized.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="⚙️ LOA Admin Panel",
            description="Manage active LOAs.",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(
            embed=embed,
            view=AdminPanel(),
            ephemeral=True
        )

async def setup(bot):

    await bot.add_cog(
        LOA(bot)
    )