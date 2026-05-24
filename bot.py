import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import os

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
leaderboard_entries = []

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    name TEXT
)
""")

default_employees = [
    "Matthew Wright",
    "Braxton Chrisp",
    "Cameron White",
    "Malik White",
    "Myla Chester",
    "Olivia Love",
    "Tommy Williams",
    "Landon Black",
    "Donny Winter",
    "Alan Duke",
    "Amon Demon",
    "Folabi White",
    "Jay Clayton",
    "Kevin Flenory",
    "Pauly Devini",
    "Ryan Thomas",
    "Scrim Wright",
    "Teiko Lucenti-Price",
    "Timothy Walker",
    "Xavier Saint",
    "Clover Duke"
]

for employee in default_employees:

    cursor.execute(
        "SELECT * FROM employees WHERE name=?",
        (employee,)
    )

    existing = cursor.fetchone()

    if not existing:

        cursor.execute(
            "INSERT INTO employees VALUES (?)",
            (employee,)
        )

conn.commit()


def get_rank(member):

    for role_id, rank_name in RANK_ROLES.items():

        role = member.guild.get_role(role_id)

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

        active_loas[interaction.user.id] = msg.id

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

        for user_id in active_loas:

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


# =========================
# EMPLOYEE SELECT
# =========================

class EmployeeSelect(discord.ui.Select):

    def __init__(self):

        cursor.execute(
            "SELECT name FROM employees"
        )

        employees = cursor.fetchall()

        options = []

        for employee in employees[:25]:

            options.append(
                discord.SelectOption(
                    label=employee[0],
                    value=employee[0]
                )
            )

        super().__init__(
            placeholder="Select Employee",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        selected_name = self.values[0]

        await interaction.response.send_modal(
            AmountModal(selected_name)
        )


# =========================
# AMOUNT MODAL
# =========================

class AmountModal(discord.ui.Modal):

    def __init__(
        self,
        employee_name
    ):

        super().__init__(
            title=f"{employee_name} Sales"
        )

        self.employee_name = employee_name

        current_amount = ""

        for name, amount in leaderboard_entries:

            if name == employee_name:

                current_amount = str(amount)

        self.amount_input = discord.ui.TextInput(
            label="Sales Amount",
            placeholder="5079200",
            default=current_amount,
            required=True,
            max_length=20
        )

        self.add_item(self.amount_input)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            amount = int(
                self.amount_input.value.replace(",", "")
            )

        except:

            await interaction.response.send_message(
                "❌ Invalid amount.",
                ephemeral=True
            )

            return

        global leaderboard_entries

        leaderboard_entries = [
            entry for entry in leaderboard_entries
            if entry[0] != self.employee_name
        ]

        leaderboard_entries.append(
            (
                self.employee_name,
                amount
            )
        )

        await interaction.response.send_message(
            f"✅ Updated {self.employee_name} to ${amount:,}",
            ephemeral=True
        )


# =========================
# LEADERBOARD VIEW
# =========================

class LeaderboardView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=600
        )

        self.add_item(
            EmployeeSelect()
        )

        self.leaderboard_message = None

    @discord.ui.button(
        label="Edit Sales",
        style=discord.ButtonStyle.blurple
    )
    async def edit_sales(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "Select the employee again from the dropdown to edit their sales.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Finish Leaderboard",
        style=discord.ButtonStyle.green
    )
    async def finish_board(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        global leaderboard_entries

        if not leaderboard_entries:

            await interaction.response.send_message(
                "❌ No entries added.",
                ephemeral=True
            )

            return

        sorted_entries = sorted(
            leaderboard_entries,
            key=lambda x: x[1],
            reverse=True
        )

        leaderboard_text = "# SALES LEADERS\n\n"

        for index, (name, amount) in enumerate(
            sorted_entries,
            start=1
        ):

            leaderboard_text += (
                f"**{index}. {name} "
                f"----- "
                f"${amount:,}**\n\n"
            )

        if self.leaderboard_message:

            await self.leaderboard_message.edit(
                content=leaderboard_text
            )

            await interaction.response.send_message(
                "✅ Leaderboard updated.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                leaderboard_text
            )

            self.leaderboard_message = await interaction.original_response()

    @discord.ui.button(
        label="Clear All",
        style=discord.ButtonStyle.red
    )
    async def clear_board(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        global leaderboard_entries

        leaderboard_entries.clear()

        if self.leaderboard_message:

            await self.leaderboard_message.delete()

            self.leaderboard_message = None

        await interaction.response.send_message(
            "🗑️ Cleared leaderboard entries.",
            ephemeral=True
        )


# =========================
# ADD EMPLOYEE
# =========================

@bot.tree.command(
    name="addemployee",
    description="Add employee to dropdown"
)
async def addemployee(
    interaction: discord.Interaction,
    name: str
):

    cursor.execute(
        "SELECT * FROM employees WHERE name=?",
        (name,)
    )

    existing = cursor.fetchone()

    if existing:

        await interaction.response.send_message(
            f"❌ {name} already exists.",
            ephemeral=True
        )

        return

    cursor.execute(
        "INSERT INTO employees VALUES (?)",
        (name,)
    )

    conn.commit()

    await interaction.response.send_message(
        f"✅ Added {name}",
        ephemeral=True
    )


# =========================
# REMOVE EMPLOYEE
# =========================

@bot.tree.command(
    name="removeemployee",
    description="Remove employee from dropdown"
)
async def removeemployee(
    interaction: discord.Interaction,
    name: str
):

    cursor.execute(
        "DELETE FROM employees WHERE name=?",
        (name,)
    )

    conn.commit()

    await interaction.response.send_message(
        f"✅ Removed {name}",
        ephemeral=True
    )


# =========================
# LEADERBOARD COMMAND
# =========================

@bot.tree.command(
    name="leaderboardcreate",
    description="Create leaderboard"
)
async def leaderboardcreate(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="Sales Leaderboard",
        description=(
            "Select employees from the dropdown.\n"
            "Enter or edit sales amount.\n"
            "Press Finish when done."
        ),
        color=0x2b2d31
    )

    await interaction.response.send_message(
        embed=embed,
        view=LeaderboardView(),
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
