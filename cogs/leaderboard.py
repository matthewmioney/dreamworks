import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

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

leaderboard_entries = []


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

        self.add_item(
            self.amount_input
        )

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
            "Select the employee again from the dropdown to edit sales.",
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
# COG
# =========================

class Leaderboard(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @discord.app_commands.command(
        name="addemployee",
        description="Add employee"
    )
    async def addemployee(
        self,
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

    @discord.app_commands.command(
        name="removeemployee",
        description="Remove employee"
    )
    async def removeemployee(
        self,
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

    @discord.app_commands.command(
        name="leaderboardcreate",
        description="Create leaderboard"
    )
    async def leaderboardcreate(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="Sales Leaderboard",
            description=(
                "Select employees.\n"
                "Enter or edit sales.\n"
                "Press Finish when done."
            ),
            color=0x2b2d31
        )

        await interaction.response.send_message(
            embed=embed,
            view=LeaderboardView(),
            ephemeral=True
        )

async def setup(bot):

    await bot.add_cog(
        Leaderboard(bot)
    )