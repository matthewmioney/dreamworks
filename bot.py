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


class LOAModal(discord.ui.Modal, title="LOA Request"):

    rank = discord.ui.TextInput(
        label="Rank",
        placeholder="Enter your rank",
        required=True,
        max_length=50
    )

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Reason for LOA",
        required=True,
        max_length=500
    )

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

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="📋 LOA Request",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Username",
            value=interaction.user.name,
            inline=False
        )

        embed.add_field(
            name="Rank",
            value=self.rank.value,
            inline=False
        )

        embed.add_field(
            name="Reason",
            value=self.reason.value,
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

        embed.set_footer(
            text=f"Submitted by {interaction.user}"
        )

        await interaction.response.send_message(
            "✅ LOA submitted successfully.",
            ephemeral=True
        )

        await interaction.channel.send(
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

    await interaction.response.send_modal(
        LOAModal()
    )


bot.run(TOKEN)