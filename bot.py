import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1211555736283516938

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# MONTH OPTIONS
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


class LOAView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=300)

        self.start_month = None
        self.end_month = None

        self.add_item(StartMonthSelect())
        self.add_item(EndMonthSelect())

    @discord.ui.button(
        label="Submit LOA",
        style=discord.ButtonStyle.green
    )
    async def submit_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.start_month or not self.end_month:

            await interaction.response.send_message(
                "❌ Select both months first.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="📋 LOA Request",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="User",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Start Month",
            value=self.start_month,
            inline=True
        )

        embed.add_field(
            name="End Month",
            value=self.end_month,
            inline=True
        )

        embed.set_footer(
            text=f"Submitted by {interaction.user}"
        )

        await interaction.response.send_message(
            "✅ LOA submitted successfully.",
            ephemeral=True
        )

        await interaction.channel.send(
            content=interaction.user.mention,
            embed=embed
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
    description="Submit an LOA"
)
async def loa(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📋 LOA Request Form",
        description="Select your LOA months below.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=LOAView(),
        ephemeral=True
    )


bot.run(TOKEN)
