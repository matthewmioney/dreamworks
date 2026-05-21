import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import sqlite3
import os
import json
import re
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")

ADMIN_ROLE_ID = 1211555736304357429

RANK_ROLES = {
    1287680549137420401: "Owner",
    1211555736304357429: "Manager",
    1211555736283516945: "Supervisor",
    1211555736304357426: "Sr. Mechanic",
    1211555736283516947: "Mechanic",
    1211555736283516946: "Trainee"
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

active_loas = {}

# =========================
# SALES SYSTEM
# =========================

SALES_FILE = "sales_data.json"
CHANNELS_FILE = "sales_channels.json"


def load_json(file, default):

    if not os.path.exists(file):

        with open(file, "w") as f:
            json.dump(default, f)

    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):

    with open(file, "w") as f:
        json.dump(data, f, indent=4)


sales_data = load_json(
    SALES_FILE,
    {}
)

sales_channels = load_json(
    CHANNELS_FILE,
    []
)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("database.db")
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

            user = await bot.fetch_user(
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
            description="All active LOAs were removed.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================
# CHECK EXPIRED LOAS
# =========================

@tasks.loop(minutes=30)
async def check_expired_loas():

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

                channel = bot.get_channel(
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


# =========================
# SALES TRACKER
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id in sales_channels:

        content = message.content.strip()

        match = re.search(
            r"\$?([\d,]+)",
            content
        )

        if match:

            amount = int(
                match.group(1).replace(",", "")
            )

            user_id = str(
                message.author.id
            )

            username = str(
                message.author
            )

            if user_id not in sales_data:

                sales_data[user_id] = {
                    "name": username,
                    "sales": 0
                }

            sales_data[user_id][
                "name"
            ] = username

            sales_data[user_id][
                "sales"
            ] += amount

            save_json(
                SALES_FILE,
                sales_data
            )

    await bot.process_commands(
        message
    )


# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} commands globally."
        )

    except Exception as e:

        print(e)

    if not check_expired_loas.is_running():
        check_expired_loas.start()

    print(
        f"Logged in as {bot.user}"
    )


# =========================
# SALES COMMANDS
# =========================

@bot.tree.command(
    name="addsaleschannel",
    description="Add a sales tracking channel"
)
async def addsaleschannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ You must be an admin.",
            ephemeral=True
        )

        return

    if channel.id in sales_channels:

        await interaction.response.send_message(
            "❌ Channel already monitored.",
            ephemeral=True
        )

        return

    sales_channels.append(
        channel.id
    )

    save_json(
        CHANNELS_FILE,
        sales_channels
    )

    await interaction.response.send_message(
        f"✅ Now monitoring {channel.mention}"
    )


@bot.tree.command(
    name="sales",
    description="Check your sales"
)
async def sales(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    if member is None:
        member = interaction.user

    user_id = str(member.id)

    if user_id not in sales_data:

        await interaction.response.send_message(
            f"❌ {member.mention} has no sales."
        )

        return

    total = sales_data[user_id][
        "sales"
    ]

    embed = discord.Embed(
        title="💰 Sales Totals",
        color=discord.Color.green()
    )

    embed.add_field(
        name=member.display_name,
        value=f"${total:,}",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


@bot.tree.command(
    name="topsales",
    description="View sales leaderboard"
)
async def topsales(
    interaction: discord.Interaction
):

    if not sales_data:

        await interaction.response.send_message(
            "❌ No sales recorded."
        )

        return

    sorted_sales = sorted(
        sales_data.items(),
        key=lambda x: x[1]["sales"],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 Top Sales",
        color=discord.Color.gold()
    )

    text = ""

    for index, (_, data) in enumerate(
        sorted_sales[:10],
        start=1
    ):

        text += (
            f"**#{index}** "
            f"{data['name']} — "
            f"${data['sales']:,}\n"
        )

    embed.description = text

    await interaction.response.send_message(
        embed=embed
    )


# =========================
# LOA COMMANDS
# =========================

@bot.tree.command(
    name="loa",
    description="Submit a Leave of Absence request"
)
async def loa(
    interaction: discord.Interaction
):

    await interaction.response.send_modal(
        LOAModal()
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

        current_date = datetime.now().strftime(
            "%m/%d/%Y"
        )

        new_embed.set_footer(
            text=f"Cancelled on {current_date}"
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
async def panel(
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
        description="Manage active LOAs below.",
        color=discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed,
        view=AdminPanel(),
        ephemeral=True
    )


bot.run(TOKEN)
