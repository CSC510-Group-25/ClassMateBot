# TODO deadline reminder for all students
# Copyright (c) 2021 War-Keeper
# This functionality provides various methods to manage reminders (in the form of creation, retrieval,
# updation and deletion)
# A user can set up a reminder, check what is due this week or what is due today.
# He/She can also check all the due homeworks based on hte coursename.
# A user can also update or delete a reminder if needed.
import os
import asyncio
from datetime import datetime, timedelta, timezone, time
from dateutil import parser
import sys
from discord.ext import commands, tasks
import discord

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db

class Deadline(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.units = {"second": 1, "minute": 60, "hour": 3600, "day": 86400, "week": 604800, "month": 2592000}

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: timenow(self, ctx, *, date: str)
    #    Description: This command lets the user get the offset needed for proper datetime reminders in UTC.
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - date: current date and 24-hour time
    #    Outputs: offset from the user's current time with UTC.
    # -----------------------------------------------------------------------------------------------------------------
    @commands.command(name="timenow",
                      help="put in current time to get offset needed for proper "
                           "datetime notifications $timenow MMM DD YYYY HH:MM ex. $timenow SEP 25 2024 17:02")
    async def timenow(self, ctx, *, date: str):
        try:
            input_time = parser.parse(date)
        except ValueError:
            await ctx.send("Due date could not be parsed")
            return

        utc_dt = datetime.utcnow()
        difference = utc_dt - input_time
        diff_in_hours = int(difference.total_seconds() / 3600)
        input_time += timedelta(hours=diff_in_hours)

        await ctx.send(f"Current time is {-diff_in_hours} hours from system time (UTC).")


    # -----------------------------------------------------------------------------------------------------------------
    #    Function: timenow_error(self, ctx, error)
    #    Description: prints error message for timenow command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @timenow.error
    async def timenow_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "To use the timenow command (with current time), do: "
                "$timenow MMM DD YYYY HH:MM ex. $timenow SEP 25 2024 17:02")
        else:
            await ctx.author.send(error)
            #await ctx.message.delete()
            print(error)

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duedate(self, ctx, coursename: str, hwcount: str, *, date: str)
    #    Description: Adds the homework to database in the specified format
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - coursename: name of the course for which homework is to be added
    #    - hwcount: name of the homework
    #    - date: due date of the assignment
    #    Outputs: returns either an error stating a reason for failure or returns a success message
    #          indicating that the reminder has been added
    # -----------------------------------------------------------------------------------------------------------------
    @commands.has_role('Instructor')
    @commands.command(name="addhw",
                      help="add homework and due-date $addhw CLASSNAME HW_NAME MMM DD YYYY optional(HH:MM) optional(TIMEZONE)"
                      "ex. $addhw CSC510 HW2 SEP 25 2024 17:02 EST")
    async def duedate(self, ctx, coursename: str, hwcount: str, *, date: str):
        author = ctx.message.author

        try:
            duedate = parser.parse(date)
        except ValueError:
            await ctx.send("Due date could not be parsed")
            return

        existing = db.query(
            'SELECT author_id FROM reminders WHERE guild_id = %s AND course = %s AND homework = %s',
            (ctx.guild.id, coursename, hwcount)
        )
        if not existing:
            db.query(
                'INSERT INTO reminders (guild_id, author_id, course, homework, due_date) VALUES (%s, %s, %s, %s, %s)',
                (ctx.guild.id, author.id, coursename, hwcount, duedate)
            )
            await ctx.send(
                f"A date has been added for: {coursename} homework named: {hwcount} "
                f"which is due on: {duedate} by {author}.")
        else:
            await ctx.send("This homework has already been added..!!")

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duedate_error(self, ctx, error)
    #    Description: prints error message for addhw command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @duedate.error
    async def duedate_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                'To use the addhw command, do: $addhw CLASSNAME HW_NAME MMM DD YYYY optional(HH:MM) optional(TIMEZONE)\n '
                '( For example: $addhw CSC510 HW2 SEP 25 2024 17:02 EST )')
        else:
            await ctx.author.send(error)
            #await ctx.message.delete()
            print(error)

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: deleteReminder(self, ctx, courseName: str, hwName: str)
    #    Description: Delete a reminder using Classname and Homework name
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - coursename: name of the course for which homework is to be added
    #    - hwName: name of the homework
    #    Outputs: returns either an error stating a reason for failure or
    #          returns a success message indicating that the reminder has been deleted
    # -----------------------------------------------------------------------------------------------------------------
    @commands.has_role('Instructor')
    @commands.command(name="deletereminder", pass_context=True,
                      help="delete a specific reminder using course name and homework name using "
                      "$deletereminder CLASSNAME HW_NAME ex. $deletereminder CSC510 HW2 ")
    async def deleteReminder(self, ctx, courseName: str, hwName: str):
        reminders_deleted = db.query(
            'SELECT course, homework, due_date FROM reminders WHERE guild_id = %s AND homework = %s AND course = %s',
            (ctx.guild.id, hwName, courseName)
        )
        db.query(
            'DELETE FROM reminders WHERE guild_id = %s AND homework = %s AND course = %s',
            (ctx.guild.id, hwName, courseName)
        )

        for course, homework, due_date in reminders_deleted:
            due = due_date.strftime("%Y-%m-%d %H:%M:%S")
            await ctx.send(f"Following reminder has been deleted: Course: {course}, "
                f"Homework Name: {homework}, Due Date: {due}")

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: deleteReminder_error(self, ctx, error)
    #    Description: prints error message for deletereminder command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @deleteReminder.error
    async def deleteReminder_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                'To use the deletereminder command, do: $deletereminder CLASSNAME HW_NAME \n '
                '( For example: $deletereminder CSC510 HW2 )')
        else:
            await ctx.author.send(error)
            #await ctx.message.delete()
            print(error)

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: changeduedate(self, ctx, classid: str, hwid: str, *, date: str)
    #    Description: Update the 'Due date' for a homework by providing the classname and homewwork name
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - classid: name of the course for which homework is to be added
    #    - hwid: name of the homework
    #    - date: due date of the assignment
    #    Outputs: returns either an error stating a reason for failure or
    #          returns a success message indicating that the reminder has been updated
    # -----------------------------------------------------------------------------------------------------------------
    @commands.has_role('Instructor')
    @commands.command(name="changeduedate", pass_context=True,
                      help="update the assignment date. $changeduedate CLASSNAME HW_NAME MMM DD YYYY optional(HH:MM) optional(TIMEZONE)"
                      "ex. $changeduedate CSC510 HW2 SEP 25 2024 17:02 EST")
    async def changeduedate(self, ctx, classid: str, hwid: str, *, date: str):
        author = ctx.message.author
        try:
            duedate = parser.parse(date)
            print(duedate)
        except ValueError:
            await ctx.send("Due date could not be parsed")
            return

        # future = (time.time() + (duedate - datetime.today()).total_seconds())
        db.query(
            'UPDATE reminders SET author_id = %s, due_date = %s WHERE guild_id = %s AND homework = %s AND course = %s',
            (author.id, duedate, ctx.guild.id, hwid, classid)
        )
        await ctx.send(f"{classid} {hwid} has been updated with following date: {duedate}")

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: changeduedate_error(self, ctx, error)
    #    Description: prints error message for changeduedate command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @changeduedate.error
    async def changeduedate_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                'To use the changeduedate command, do: $changeduedate CLASSNAME HW_NAME MMM DD YYYY optional(HH:MM) optional(TIMEZONE)\n'
                ' ( For example: $changeduedate CSC510 HW2 SEP 25 2024 17:02 EST)')
        else:
            await ctx.author.send(error)
            #await ctx.message.delete()
            print(error)

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duethisweek(self, ctx)
    #    Description: Displays all the homeworks that are due this week along with the coursename and due date
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    Outputs: returns either an error stating a reason for failure
    #             or returns a list of all the assignments that are due this week
    # -----------------------------------------------------------------------------------------------------------------
    @commands.command(name="duethisweek", pass_context=True,
                      help="check all the homeworks that are due this week $duethisweek")
    async def duethisweek(self, ctx):
        reminders = db.query(
            "SELECT course, homework, due_date "
            "FROM reminders "
            "WHERE guild_id = %s AND date_part('day', due_date - now()) <= 7 AND date_part('minute', due_date - now()) >= 0",
            (ctx.guild.id,)
        )

        curr_date = datetime.now(timezone.utc)

        for course, homework, due_date in reminders:
            delta = due_date - curr_date
            formatted_due_date = due_date.strftime("%b %d %Y %H:%M:%S%z")
            await ctx.author.send(f"{course} {homework} is due in {delta.days} days, {delta.seconds//3600}"
                            f" hours and {(delta.seconds//60)%60} minutes ({formatted_due_date})")
        await ctx.message.delete()


    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duethisweek_error(self, ctx, error)
    #    Description: prints error message for duethisweek command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @duethisweek.error
    async def duethisweek_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duetoday(self, ctx)
    #    Description: Displays all the homeworks that are due today
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    # Outputs: returns either an error stating a reason for failure or
    #          returns a list of all the assignments that are due on the day the command is run
    # -----------------------------------------------------------------------------------------------------------------
    @commands.command(name="duetoday", pass_context=True, help="check all the homeworks that are due today $duetoday")
    async def duetoday(self, ctx):
        due_today = db.query(
            "SELECT course, homework, due_date "
            "FROM reminders "
            "WHERE guild_id = %s AND date_part('day', due_date - now()) <= 1 AND date_part('minute', due_date - now()) >= 0",
            (ctx.guild.id,)
        )
        for course, homework, due_date in due_today:
            delta = due_date - datetime.now(timezone.utc)
            await ctx.author.send(f"{course} {homework} is due in {delta.days} days, {delta.seconds//3600}"
                            f" hours and {(delta.seconds//60)%60} minutes")
        if len(due_today) == 0:
            await ctx.author.send("You have no dues today..!!")
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: duetoday_error(self, ctx, error)
    #    Description: prints error message for duetoday command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @duetoday.error
    async def duetoday_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: coursedue(self, ctx, courseid: str)
    #    Description: Displays all the homeworks that are due for a specific course
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - courseid: name of the course for which homework is to be added
    #    Outputs: returns either an error stating a reason for failure or
    #          a list of assignments that are due for the provided courseid
    # -----------------------------------------------------------------------------------------------------------------
    @commands.command(name="coursedue", pass_context=True,
                      help="check all the homeworks that are due for a specific course $coursedue coursename "
                      "ex. $coursedue CSC505")
    async def coursedue(self, ctx, courseid: str):
        reminders = db.query(
            'SELECT homework, due_date FROM reminders WHERE guild_id = %s AND course = %s',
            (ctx.guild.id, courseid)
        )
        for homework, due_date in reminders:
            formatted_due_date = due_date.strftime("%b %d %Y %H:%M:%S")
            await ctx.author.send(f"{homework} is due at {formatted_due_date}")
        if len(reminders) == 0:
            await ctx.author.send(f"Rejoice..!! You have no pending homeworks for {courseid}..!!")
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: coursedue_error(self, ctx, error)
    #    Description: prints error message for coursedue command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @coursedue.error
    async def coursedue_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send(
                'To use the coursedue command, do: $coursedue CLASSNAME \n ( For example: $coursedue CSC510 )')
        else:
            await ctx.author.send(error)
            print(error)
        await ctx.message.delete()

    # ---------------------------------------------------------------------------------
    #    Function: listreminders(self, ctx)
    #    Description: Print out all the reminders
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    Outputs: returns either an error stating a reason for failure or
    #             returns a list of all the assignments
    # ---------------------------------------------------------------------------------
    @commands.command(name="listreminders", pass_context=True, help="lists all reminders")
    async def listreminders(self, ctx):
        author = ctx.message.author
        reminders = db.query(
            'SELECT course, homework, due_date FROM reminders WHERE guild_id = %s and author_id = %s and now() < due_date',
            (ctx.guild.id, author.id)
        )

        for course, homework, due_date in reminders:
            formatted_due_date = due_date.strftime("%b %d %Y %H:%M:%S%z")
            await ctx.author.send(f"{course} homework named: {homework} which is due on: {formatted_due_date} by {author.name}")
        if not reminders:
            await ctx.author.send("Mission Accomplished..!! You don't have any more dues..!!")
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: listreminders_error(self, ctx, error)
    #    Description: prints error message for listreminders command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @listreminders.error
    async def listreminders_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)
        await ctx.message.delete()

    # ---------------------------------------------------------------------------------
    #    Function: overdue(self, ctx)
    #    Description: Print out all the reminders
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    Outputs: returns either an error stating a reason for failure or
    #             returns a list of all the assignments
    # ---------------------------------------------------------------------------------
    @commands.command(name="overdue", pass_context=True, help="lists overdue reminders")
    async def overdue(self, ctx):
        author = ctx.message.author
        reminders = db.query(
            'SELECT course, homework, due_date FROM reminders WHERE guild_id = %s and author_id = %s'
            'and now() > due_date',
            (ctx.guild.id, author.id)
        )

        for course, homework, due_date in reminders:
            formatted_due_date = due_date.strftime("%b %d %Y %H:%M:%S%z")
            await ctx.author.send(f"{course} homework named: {homework} which was due on: {formatted_due_date} by {author.name}")
        if not reminders:
            await ctx.author.send("There are no overdue reminders")
        await ctx.message.delete()

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: listreminders_error(self, ctx, error)
    #    Description: prints error message for listreminders command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @overdue.error
    async def overdue_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)
        await ctx.message.delete()

    # ---------------------------------------------------------------------------------
    #    Function: clearallreminders(self, ctx)
    #    Description: Delete all the reminders
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    Outputs: returns either an error stating a reason for failure or
    #             returns a success message stating that reminders have been deleted
    # ---------------------------------------------------------------------------------

    @commands.command(name="clearreminders", pass_context=True, help="deletes all reminders")
    async def clearallreminders(self, ctx):
        db.query('DELETE FROM reminders WHERE guild_id = %s', (ctx.guild.id,))
        await ctx.send("All reminders have been cleared..!!")

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: clearallreminders_error(self, ctx, error)
    #    Description: prints error message for clearreminders command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @clearallreminders.error
    async def clearallreminders_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)


    # ---------------------------------------------------------------------------------
    #    Function: remindme(self, ctx, quantity: int, time_unit : str,*, text :str)
    #    Description: Personal remind me functionality
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - quantity - time after which the data will be erased
    #    Outputs: returns either an error stating a reason for failure or
    #             returns a success message stating that reminders have been deleted
    # ---------------------------------------------------------------------------------

    # @commands.command(name="remindme", pass_context=True, help="Request the bot to set a reminder for a due date")
    # async def remindme(self, ctx, quantity: int, time_unit: str, *, text: str):

    #     time_unit = time_unit.lower()
    #     author = ctx.message.author
    #     s = ""
    #     if time_unit.endswith("s"):
    #         time_unit = time_unit[:-1]
    #         s = "s"
    #     if not time_unit in self.units:
    #         await ctx.send("Invalid unit of time. Select from seconds/minutes/hours/days/weeks/months")
    #         return
    #     if quantity < 1:
    #         await ctx.send("Quantity must not be 0 or negative")
    #         return
    #     if len(text) > 1960:
    #         await ctx.send("Text is too long.")
    #         return

    #     seconds = self.units[time_unit] * quantity
    #     future = int(time.time() + seconds)
    #     # TODO set timestamp compatible with db

    #     db.query(
    #         'INSERT INTO reminders (guild_id, author_id, future, text) VALUES (%s, %s, %s)',
    #         (ctx.guild.id, author.id, future, text)
    #     )

    #     await ctx.send("I will remind you that in {} {}.".format(str(quantity), time_unit + s))

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     await ctx.send('Unidentified command..please use $help to get the list of available commands')

    # -----------------------------------------------------------------------------------------------------
    #    Function: clearoverdue(self)
    #    Description: checks for expired reminders and cleans them.
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: context of the command
    # -----------------------------------------------------------------------------------------------------
    @commands.command(name="clearoverdue", pass_context=True, help="deletes overdue reminders")
    async def clearoverdue(self, ctx):
        db.query('DELETE FROM reminders WHERE now() > due_date')
        await ctx.send("All overdue reminders have been cleared..!!")

    # -----------------------------------------------------------------------------------------------------------------
    #    Function: clearoverdue_error(self, ctx, error)
    #    Description: prints error message for clearoverdue command
    #    Inputs:
    #       - ctx: context of the command
    #       - error: error message
    #    Outputs:
    #       - Error details
    # -----------------------------------------------------------------------------------------------------------------
    @clearoverdue.error
    async def clearoverdue_error(self, ctx, error):
        await ctx.author.send(error)
        print(error)

    # -----------------------------------------------------------------------------------------------------
    #    Function: send_reminders_day(self)
    #    Description: task that runs once per day and sends a reminders for assignments due
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    # -----------------------------------------------------------------------------------------------------
    @tasks.loop(hours=24)
    async def send_reminders_day(self):
        channel = discord.utils.get(self.bot.get_all_channels(), name="reminders")
        if channel:
            reminders = db.query("SELECT course, homework, due_date "
                "FROM reminders "
                "WHERE due_date::date = now()::date")
            for course,homework,due_date in reminders:
                difference = due_date - datetime.now(timezone.utc)
                await channel.send(f"{homework} for {course} is due in {(difference.seconds//3600)} hours")

    # -----------------------------------------------------------------------------------------------------
    #    Function: bofore(self)
    #    Description: runs once per day and waits until 8:00 AM EST to send reminders via the send
    #       reminders day function
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    # -----------------------------------------------------------------------------------------------------
    @send_reminders_day.before_loop
    async def before(self):
        WHEN = time(13, 0, 0) # 8:00 AM eastern
        now = datetime.utcnow()
        target_time = datetime.combine(now.date(), WHEN)
        seconds_until_target = (target_time - now).total_seconds()
        if seconds_until_target < 0:
            target_time = datetime.combine(now.date()+timedelta(days=1), WHEN)
            seconds_until_target = (target_time - now).total_seconds()
        await asyncio.sleep(seconds_until_target)

    # -----------------------------------------------------------------------------------------------------
    #    Function: send_reminders_hour(self)
    #    Description: task that runs once per hours and sends a reminders for assignments due
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    # -----------------------------------------------------------------------------------------------------
    @tasks.loop(hours=1)
    async def send_reminders_hour(self):
        channel = discord.utils.get(self.bot.get_all_channels(), name="reminders")
        if channel:
            reminders = db.query("SELECT course, homework, due_date "
                "FROM reminders "
                "WHERE due_date::date = now()::date")
            for course,homework,due_date in reminders:
                difference = due_date - datetime.now(timezone.utc)
                if difference.seconds//3600 == 0:
                    await channel.send(f"{homework} for {course} is due within the hour")

# -------------------------------------
# add the file to the bot's cog system
# -------------------------------------
def setup(bot):
    n = Deadline(bot)
    n.send_reminders_day.start()    # pylint: disable=no-member
    n.send_reminders_hour.start()   # pylint: disable=no-member
    bot.add_cog(n)
