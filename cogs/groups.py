# Copyright (c) 2021 War-Keeper
import discord
from discord.ext import commands
import os
import csv


# -----------------------------------------------------------
# This File contains commands for joining a group, leaving a group,
# and displaying which groups are available
# -----------------------------------------------------------
class Groups(commands.Cog):
    student_pool = {}
    groups = {}

    # -----------------------------------------------------------
    # initialize
    # -----------------------------------------------------------
    def __init__(self, bot):
        self.bot = bot

    # -------------------------------------------------------------------------------------------------------
    #    Function: join(self, ctx, arg='group', arg2='-1')
    #    Description: joins the user to the given group
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - arg: the name of the group
    #    - arg2: the number of the group
    #    Outputs: adds the user to the given group or returns an error if the group is invalid or in case of
    #             syntax errors
    # -------------------------------------------------------------------------------------------------------
    @commands.command(name='join', help='To use the join command, do: $join \'Group\' <Num> \n \
    ( For example: $join Group 0 )', pass_context=True)
    async def join(self, ctx, arg='group', arg2='-1'):
        # load the groups from the csv
        groups = load_groups()

        # get the name of the caller
        member_name = ctx.message.author.display_name.upper()

        # get the arguments for the group to join
        group_num = arg.upper() + ' ' + arg2

        # if the the group is a valid option
        if group_num in groups:

            # check if group has more than 6 people
            if len(groups[group_num]) == 6:
                await ctx.send('A group cannot have more than 6 people!')
                return

            # check if member is already in another group
            for key in groups.keys():
                if member_name in groups[key]:
                    await ctx.send('You are already in ' + key.title())
                    return

            # add the member to the group and send confirmation
            groups[group_num].append(member_name)
            db.query(
                'INSERT INTO groups (guild_id, group_num, member_name) VALUES (%s, %s, %s)',
                (ctx.guild.id, group_num, member_name)
            )
            await ctx.send('You are now in ' + group_num.title() + '!')

        # error handling
        else:
            await ctx.send('Not a valid group')
            await ctx.send('To use the join command, do: $join \'Group\' <Num> \n ( For example: $join Group 0 )')

    # this handles errors related to the join command
    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('To use the join command, do: $join \'Group\' <Num> \n ( For example: $join Group 0 )')

    # -------------------------------------------------------------------------------------------------------
    #    Function: remove(self, ctx, arg='group', arg2='-1')
    #    Description: removes the user from the given group
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - arg: the name of the group
    #    - arg2: the number of the group
    #    Outputs: removes the user from the given group or returns an error if the group is invalid or in
    #             case of syntax errors
    # -------------------------------------------------------------------------------------------------------
    @commands.command(name='remove', help='To use the remove command, do: $remove \'Group\' <Num> \n \
    ( For example: $remove Group 0 )', pass_context=True)
    async def remove(self, ctx, arg='group', arg2='-1'):

        # load groups csv
        groups = load_groups(ctx.guild.id)

        # get the name of the caller
        member_name = ctx.message.author.display_name.upper()

        # get the arguments for the group to join
        group_num = arg.upper() + ' ' + arg2

        # if the the group is a valid option
        if group_num in groups:

            # if member in is the group, then remove them from it
            if member_name in groups[group_num]:
                db.query(
                    'DELETE FROM groups WHERE guild_id = %s AND group_num = %s AND member_name = %s',
                    (ctx.guild.id, group_num, member_name)
                )
                await ctx.send('You have been removed from ' + group_num.title() + '!')
            # else error message
            else:
                await ctx.send('You are not in ' + group_num.title())

        # if the arguments are not listed, then try to find out what group the member is in and remove them
        elif arg2 == '-1':
            rows_deleted = db.query(
                'DELETE FROM groups WHERE guild_id = %s AND group_num = %s AND member_name = %s',
                (ctx.guild.id, group_num, member_name)
            )
            for row in rows_deleted:
                _, group_num, *_ = row
                await ctx.send('You have been removed from ' + group_num + '!')

        # error handling
        else:
            await ctx.send(group_num.title() + ' is not a valid group')
            await ctx.send('To use the remove command, do: $remove \'Group\' <Num> \n \
            ( For example: $remove Group 0 )')

    # this handles errors related to the remove command
    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('To use the remove command, do: $remove \'Group\' <Num> \n \
            ( For example: $remove Group 0 )')

    # -------------------------------------------------------------------------------------------------------
    #    Function: group(self, ctx)
    #    Description: prints the list of groups
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    Outputs: prints the list of groups
    # -------------------------------------------------------------------------------------------------------
    @commands.command(name='group', help='print amount of groups that are full', pass_context=True)
    @commands.dm_only()
    async def group(self, ctx):

        # load groups csv
        groups = load_groups(ctx.guild.id)

        # create embedded objects
        embed = discord.Embed(title='Group List', color=discord.Color.teal())
        embed.set_thumbnail(url="https://i.pinimg.com/474x/e7/e3/bd/e7e3bd1b5628510a4e9d7a9a098b7be8.jpg")

        embed2 = discord.Embed(title='Group List', color=discord.Color.teal())
        embed2.set_thumbnail(url="https://i.pinimg.com/474x/e7/e3/bd/e7e3bd1b5628510a4e9d7a9a098b7be8.jpg")

        # ignoring the first line, add all group member counts to the embedded objects
        count = 0
        for key in groups.keys():
            if key != 'GROUP_NUM':
                if count < 20:
                    embed.add_field(name=key, value=str(len(groups[key])), inline=True)
                else:
                    embed2.add_field(name=key, value=str(len(groups[key])), inline=True)
                count += 1

        # print the embedded objects
        embed.set_footer(text="Number Represents the Group Size")
        embed2.set_footer(text="Number Represents the Group Size")
        await ctx.send(embed=embed)

        if count >= 20:
            await ctx.send(embed=embed2)

    # -----------------------------------------------------------
    # This is a testing arg, not really used for anything else but adding to the csv file
    # -----------------------------------------------------------
    # @commands.command(name='test_name', help='add a name to the name_mapping.csv', pass_context=True)
    # async def test_name(self, ctx, arg, arg2):
    #     student_pool = load_pool()
    #     display_name = ctx.message.author.display_name
    #     display_name_upper = display_name.upper()
    #
    #     if student_pool.get(display_name_upper) is None:
    #         student_pool[display_name_upper] = arg.upper() + ' ' + arg2.upper()
    #     else:
    #         member_name = student_pool[display_name_upper]
    #         await ctx.send('You have already registered with the name: ' + member_name.title())
    #
    #     print_pool(student_pool)


# -----------------------------------------------------------
# Used to load the groups from the csv file into a dictionary
# -----------------------------------------------------------
def load_groups(guild_id) -> dict:
    groups = db.query('SELECT array_agg(name) FROM groups WHERE guild_id = %s GROUP BY group_num', (guild_id,))
    # dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # os.chdir(dir)
    # os.chdir('data')
    # os.chdir('server_data')
    # with open('groups.csv', mode='r') as infile:
    #     reader = csv.reader(infile)
    #     group = {rows[0].upper(): [rows[1].upper(), rows[2].upper(), rows[3].upper(), rows[4].upper(),
    #                                rows[5].upper(), rows[6].upper()] for rows in reader}

    # for key in group.keys():
    #     group[key] = list(filter(None, group[key])
    # )

    # TODO CHECK

    return groups


# # ------------------------------------------------------------
# # Used to load the members from the csv file into a dictionary
# # ------------------------------------------------------------
# def load_pool() -> dict:
#     dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.chdir(dir)
#     os.chdir('data')
#     os.chdir('server_data')
#     with open('name_mapping.csv', mode='r') as infile:
#         reader = csv.reader(infile)
#         student_pools = {rows[0].upper(): rows[1].upper() for rows in reader}
#     return student_pools


# # -----------------------------------------------------------
# # Used to print the members to the csv file
# # -----------------------------------------------------------
# def print_pool(pools):
#     dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.chdir(dir)
#     os.chdir('data')
#     os.chdir('server_data')
#     with open('name_mapping.csv', mode='w', newline="") as outfile:
#         writer = csv.writer(outfile)
#         for key, value in pools.items():
#             writer.writerow([key, value])


# -----------------------------------------------------------
# add the file to the bot's cog system
# -----------------------------------------------------------
def setup(bot):
    bot.add_cog(Groups(bot))
