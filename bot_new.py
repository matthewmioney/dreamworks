import discord
from discord.ext import commands
from dotenv import load_dotenv
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


class LOAModal(discord.ui.Modal, title="LOA Details"):

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Reason for LOA",
        required=True,
        max_length=500
    )

    end_day = discord.ui.TextInput(
        label="End Day",
        placeholder="Example: 21",
        required=True,
        max_length=2
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

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
            name="Start Month",
            value=view.start_month,
            inline=True
        )

        embed.add_field(
            name="Start Year",
            value=view.start_year,
            inline=True
        )

        embed.add_field(
            name="End Month",
            value=view.end_month,
            inline=True
        )

        embed.add_field(
            name="End Year",
            value=view.end_year,
            inline=True
        )

        embed.add_field(
            name="End Day",
            value=self.end_day.value,
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

        embed.set_footer(
            text=f"Submitted by {interaction.user}"
        )

        admin_role = f"<@&{ADMIN_ROLE_ID}>"

        msg = await interaction.channel.send(
            content=f"{interaction.user.mention} {admin_role}",
            embed=embed
        )

        active_loas[interaction.user.id] = msg.id

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


@bot.event
async def on_ready():

    guild = discord.Object(
        id=GUILD_ID
    )

    bot.tree.copy_global_to(
        guild=guild
    )

    synced = await bot.tree.sync(
        guild=guild
    )

    print(
        f"Synced {len(synced)} command(s)"
    )

    print(
        f"Logged in as {bot.user}"
    )


@bot.tree.command(
    name="loa",
    description="Submit a Leave of Absence request"
)
async def loa(
    interaction: discord.Interaction
):

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
async def loacancel(
    interaction: discord.Interaction
):

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


bot.active_views = {}

bot.run(TOKEN)
