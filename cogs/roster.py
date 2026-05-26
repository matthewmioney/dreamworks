import discord
from discord.ext import commands

leaderboard_entries = []
employee_list = []


class EmployeeSelect(discord.ui.Select):

    def __init__(self):

        options = []

        for employee in employee_list:

            options.append(
                discord.SelectOption(
                    label=employee
                )
            )

        if not options:

            options.append(
                discord.SelectOption(
                    label="No employees added"
                )
            )

        super().__init__(
            placeholder="Select employee",
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        selected_employee = self.values[0]

        modal = SalesModal(
            selected_employee
        )

        await interaction.response.send_modal(
            modal
        )


class SalesModal(discord.ui.Modal):

    def __init__(
        self,
        employee_name
    ):

        super().__init__(
            title=f"{employee_name} Sales"
        )

        self.employee_name = employee_name

        self.sales_input = discord.ui.TextInput(
            label="Sales Amount",
            placeholder="Enter amount"
        )

        self.add_item(
            self.sales_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        amount = int(
            self.sales_input.value
        )

        found = False

        for index, entry in enumerate(
            leaderboard_entries
        ):

            if entry[0] == self.employee_name:

                leaderboard_entries[index] = (
                    self.employee_name,
                    amount
                )

                found = True

                break

        if not found:

            leaderboard_entries.append(
                (
                    self.employee_name,
                    amount
                )
            )

        sorted_entries = sorted(
            leaderboard_entries,
            key=lambda x: x[1],
            reverse=True
        )

        leaderboard_text = (
            "# SALES LEADERS\n\n"
        )

        for index, (name, amount) in enumerate(
            sorted_entries,
            start=1
        ):

            leaderboard_text += (
                f"**{index}. {name} "
                f"----- "
                f"${amount:,}**\n"
            )

        await interaction.response.edit_message(
            content=leaderboard_text,
            view=LeaderboardView()
        )


class LeaderboardView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            EmployeeSelect()
        )


class Leaderboard(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

    @discord.app_commands.command(
        name="leaderboardcreate",
        description="Create leaderboard"
    )
    async def leaderboardcreate(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            "# SALES LEADERS\n\nNo entries yet.",
            view=LeaderboardView()
        )

    @discord.app_commands.command(
        name="addemployee",
        description="Add employee"
    )
    async def addemployee(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        if member.display_name not in employee_list:

            employee_list.append(
                member.display_name
            )

            await interaction.response.send_message(
                f"✅ Added {member.display_name}"
            )

        else:

            await interaction.response.send_message(
                "❌ Employee already exists."
            )

    @discord.app_commands.command(
        name="removeemployee",
        description="Remove employee"
    )
    async def removeemployee(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        if member.display_name in employee_list:

            employee_list.remove(
                member.display_name
            )

            await interaction.response.send_message(
                f"🗑️ Removed {member.display_name}"
            )

        else:

            await interaction.response.send_message(
                "❌ Employee not found."
            )

async def setup(bot):

    await bot.add_cog(
        Leaderboard(bot)
    )
