import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1211555736283516938
ADMIN_ROLE_ID = 1211555736304357429

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

active_loas = {}

months = [
    discord.SelectOption(label=month)
    for month in [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]
]

years = [
    discord.SelectOption(label=str(year))
    for year in range(2026, 2031)
]

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS loas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    username TEXT,
    reason TEXT,
    start_month TEXT,
    start_year TEXT,
    end_month TEXT,
    end_year TEXT,
    end_day TEXT,
    status TEXT,
    message_id TEXT,
    channel_id TEXT
)
""")

conn.commit()


class LOAModal(discord.ui.Modal, title="LOA Details"):

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    end_day = discord.ui.TextInput(
        label="End Day",
        placeholder="Example: 21",
        required=True,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):

        view = interaction.client.active_views.get(
            interaction.user.id
        )

        if not view:

            await interaction.response.send_message(
                "❌ LOA session expired.",
                ephemeral=True
            )

            return

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
            name="Reason",
            value=self.reason.value,
            inline=False
        )

        embed.add_field(
            name="Start",
            value=f"{view.start_month} {view.start_year}",
            inline=True
        )

        embed.add_field(
            name="End",
            value=f"{view.end_month} {self.end_day.value}, {view.end_year}",
            inline=True
        )

        embed.add_field(
            name="Status",
            value="LOA Active",
            inline=False
        )

        admin_role = f"<@&{ADMIN_ROLE_ID}>"

        msg = await interaction.channel.send(
            content=f"{interaction.user.mention} {admin_role}",
            embed=embed
        )

        active_loas[interaction.user.id] = msg.id

        cursor.execute(
            """
            INSERT INTO loas (
                user_id,
                username,
                reason,
                start_month,
                start_year,
                end_month,
                end_year,
                end_day,
                status,
                message_id,
                channel_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(interaction.user.id),
                interaction.user.name,
                self.reason.value,
                view.start_month,
                view.start_year,
                view.end_month,
                view.end_year,
                self.end_day.value,
                "Active",
                str(msg.id),
                str(interaction.channel.id)
            )
        )

        conn.commit()

        await interaction.response.send_message(
            "✅ LOA submitted successfully.",
            ephemeral=True
        )


class StartMonthSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="Select Start Month",
            options=months
        )

    async def callback(self, interaction):

        self.view.start_month = self.values[0]

        await interaction.response.defer()


class EndMonthSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="Select End Month",
            options=months
        )

    async def callback(self, interaction):

        self.view.end_month = self.values[0]

        await interaction.response.defer()


class StartYearSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="Select Start Year",
            options=years
        )

    async def callback(self, interaction):

        self.view.start_year = self.values[0]

        await interaction.response.defer()


class EndYearSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="Select End Year",
            options=years
        )

    async def callback(self, interaction):

        self.view.end_year = self.values[0]

        await interaction.response.defer()


class LOAView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=300)

        self.start_month = None
        self.end_month = None
        self.start_year = None
        self.end_year = None

        self.add_item(StartMonthSelect())
        self.add_item(StartYearSelect())
        self.add_item(EndMonthSelect())
        self.add_item(EndYearSelect())

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.green
    )
    async def continue_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not all([
            self.start_month,
            self.end_month,
            self.start_year,
            self.end_year
        ]):

            await interaction.response.send_message(
                "❌ Select all dates first.",
                ephemeral=True
            )

            return

        interaction.client.active_views[
            interaction.user.id
        ] = self

        await interaction.response.send_modal(
            LOAModal()
        )


class AdminPanel(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

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

        for user_id, message_id in active_loas.items():

            user = await bot.fetch_user(user_id)

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
            description="All active LOAs were removed.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


@bot.event
async def on_ready():

    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    print(f"Logged in as {bot.user}")


@bot.tree.command(
    name="loa",
    description="Submit a Leave of Absence request"
)
async def loa(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📋 LOA Request Form",
        description="Select your LOA dates below.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=LOAView(),
        ephemeral=True
    )


@bot.tree.command(
    name="loacancel",
    description="Cancel your active LOA"
)
async def loacancel(interaction: discord.Interaction):

    if interaction.user.id not in active_loas:

        await interaction.response.send_message(
            "❌ You do not have an active LOA.",
            ephemeral=True
        )

        return

    try:

        message_id = active_loas[
            interaction.user.id
        ]

        channel = interaction.channel

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
                    value="LOA Cancelled",
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

        del active_loas[
            interaction.user.id
        ]

        await interaction.response.send_message(
            "✅ Your LOA has been cancelled.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Error cancelling LOA: {e}",
            ephemeral=True
        )


@bot.tree.command(
    name="panel",
    description="Open the admin LOA panel"
)
async def panel(interaction: discord.Interaction):

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
        description="Manage active LOAs below.",
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed,
        view=AdminPanel(),
        ephemeral=True
    )


bot.active_views = {}

bot.run(TOKEN)# Paste your working bot.py from chat here
