import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# =========================
# TOKEN
# =========================

TOKEN = os.getenv("TOKEN")

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

ROSTER_FILE = "roster.json"

# =========================
# RANK SYSTEM
# =========================

RANK_NAMES = {
    "0": "Trainee",
    "1": "Junior Staff",
    "2": "Staff",
    "3": "Senior Staff",
    "4": "Supervisor",
    "5": "Manager"
}

VALID_RANKS = list(RANK_NAMES.keys())

# =========================
# LOAD / SAVE FUNCTIONS
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
# READY EVENT
# =========================

@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")

    except Exception as e:
        print(e)

    print(f"✅ Logged in as {bot.user}")

# =========================
# SETUP ROSTER
# =========================

@bot.tree.command(
    name="setup_roster",
    description="Create the roster file"
)
async def setup_roster(interaction: discord.Interaction):

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
# HIRE USER
# =========================

@bot.tree.command(
    name="hire",
    description="Hire a user"
)

@app_commands.describe(
    member="User to hire",
    rank="Rank number (0-5)"
)

async def hire(
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
        "name": member.name,
        "rank": rank
    }

    save_roster(roster)

    embed = discord.Embed(
        title="✅ User Hired",
        color=discord.Color.green()
    )

    embed.add_field(
        name="User",
        value=member.mention,
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
# FIRE USER
# =========================

@bot.tree.command(
    name="fire",
    description="Fire a user"
)

async def fire(
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

    del roster[str(member.id)]

    save_roster(roster)

    await interaction.response.send_message(
        f"🔥 {member.mention} has been fired."
    )

# =========================
# PROMOTE USER
# =========================

@bot.tree.command(
    name="promote",
    description="Promote a user"
)

@app_commands.describe(
    member="User to promote",
    new_rank="New rank number (0-5)"
)

async def promote(
    interaction: discord.Interaction,
    member: discord.Member,
    new_rank: str
):

    if new_rank not in VALID_RANKS:

        await interaction.response.send_message(
            "❌ Invalid rank. Use 0-5.",
            ephemeral=True
        )

        return

    roster = load_roster()

    if str(member.id) not in roster:

        await interaction.response.send_message(
            "❌ User is not in the roster.",
            ephemeral=True
        )

        return

    roster[str(member.id)]["rank"] = new_rank

    save_roster(roster)

    await interaction.response.send_message(
        f"⬆️ {member.mention} promoted to "
        f"{new_rank} - {RANK_NAMES[new_rank]}"
    )

# =========================
# VIEW ROSTER
# =========================

@bot.tree.command(
    name="roster",
    description="View the roster"
)

async def roster(interaction: discord.Interaction):

    data = load_roster()

    if not data:

        await interaction.response.send_message(
            "📋 Roster is empty."
        )

        return

    embed = discord.Embed(
        title="📋 Company Roster",
        color=discord.Color.blue()
    )

    sorted_users = sorted(
        data.items(),
        key=lambda x: int(x[1]["rank"]),
        reverse=True
    )

    description = ""

    for user_id, info in sorted_users:

        rank_num = info["rank"]
        rank_name = RANK_NAMES.get(rank_num, "Unknown")

        description += (
            f"**{info['name']}** "
            f"• Rank {rank_num} ({rank_name})\n"
        )

    embed.description = description

    await interaction.response.send_message(
        embed=embed
    )

# =========================
# RUN BOT
# =========================

bot.run(TOKEN)
