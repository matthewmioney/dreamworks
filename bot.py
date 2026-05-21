import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1211555736283516938

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

LOA_FILE = "loas.json"


# Create loa file if missing
if not os.path.exists(LOA_FILE):
    with open(LOA_FILE, "w") as f:
        json.dump([], f)


def load_loas():
    with open(LOA_FILE, "r") as f:
        return json.load(f)


def save_loas(data):
    with open(LOA_FILE, "w") as f:
        json.dump(data, f, indent=4)


class LOAModal(discord.ui.Modal, title="LOA Request"):

    username = discord.ui.TextInput(
        label="Username",
        placeholder="Enter your username",
        required=True,
        max_length=50
    )

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

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📋 LOA Request",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Username",
            value=self.username.value,
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

        embed.set_footer(text=f"Submitted by {interaction.user}")

        # Save LOA
        loas = load_loas()

        loas.append({
            "user_id": interaction.user.id,
            "username": self.username.value,
            "end_date": self.end_date.value
        })

        save_loas(loas)

        await interaction.response.send_message(
            "✅ LOA submitted successfully.",
            ephemeral=True
        )

        await interaction.channel.send(embed=embed)


@tasks.loop(minutes=1)
async def check_loas():

    loas = load_loas()
    updated_loas = []

    today = datetime.now().strftime("%m/%d/%Y")

    for loa in loas:

        if loa["end_date"] == today:

            try:
                user = await bot.fetch_user(loa["user_id"])

                await user.send(
                    f"✅ Your LOA has ended as of today ({today})."
                )

            except Exception as e:
                print(f"Could not DM user: {e}")

        else:
            updated_loas.append(loa)

    save_loas(updated_loas)


@bot.event
async def on_ready():

    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)

    print(f"Synced {len(synced)} command(s)")
    print(f"Logged in as {bot.user}")

    check_loas.start()


@bot.tree.command(
    name="loa",
    description="Submit an LOA"
)
async def loa(interaction: discord.Interaction):

    await interaction.response.send_modal(LOAModal())


bot.run(TOKEN)
