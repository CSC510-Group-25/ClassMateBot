import discord
from discord.ext import commands
import os
import csv
import random


# ---------------------------------------------------------------------------------------
# Contains commands for member verification, which is handled with direct DMs to the bot
# ---------------------------------------------------------------------------------------
class Helper(commands.Cog):
    GUILD = os.getenv("GUILD")
    UNVERIFIED_ROLE_NAME = os.getenv("UNVERIFIED_ROLE_NAME")
    VERIFIED_MEMBER_ROLE = os.getenv("VERIFIED_MEMBER_ROLE")
    path = os.path.join("data", "welcome")

    def __init__(self, bot):
        self.bot = bot

    # -------------------------------------------------------------------------------------------------------------
    #    Function: verify(self, ctx, *, name: str = None)
    #    Description: Ask the bot to give the user the verified role in the server
    #    Inputs:
    #    - self: used to access parameters passed to the class through the constructor
    #    - ctx: used to access the values passed through the current context
    #    - *:
    #    - name: name of the user to verify
    #    Outputs: returns a success message if the user is sucessfully verified or error in case of syntax problems
    # --------------------------------------------------------------------------------------------------------------
    @commands.dm_only()
    @commands.command(
        name="verify",
        pass_context=True,
        help="Request the bot to verify the user to get access to channels",
    )
    async def verify(self, ctx, *, name: str = None):
        guild = None
        for g in self.bot.guilds:  # finding guild using guild name
            if g.name == self.GUILD:
                guild = g
        member = guild.get_member(
            ctx.message.author.id
        )  # finding member using member id
        unverified = discord.utils.get(
            guild.roles, name=self.UNVERIFIED_ROLE_NAME
        )  # finds the unverified role in the guild
        if (
            unverified in member.roles
        ):  # checks if the user running the command has the unveirifed role
            if name == None:
                await ctx.send(
                    "To use the verify command, do: $verify <your_full_name> \n ( For example: $verify Jane Doe )"
                )
            else:
                verified = discord.utils.get(
                    guild.roles, name=self.VERIFIED_MEMBER_ROLE
                )  # finds the verified role in the guild
                db.query('INSERT INTO name_mappings (username, real_name) VALUES (%s, %s)', (member.name, name))

                await member.add_roles(verified)  # adding verfied role
                await member.remove_roles(unverified)  # removed verfied role
                await ctx.send(
                    "Thank you for verifying! You can start using " + self.GUILD + "!"
                )
                embed = discord.Embed(
                    description="Click [Here](https://github.com/txt/se21) for the home page of the class Github page"
                )
                welcome_images = os.listdir(self.path)
                selected_image = random.choice(welcome_images)
                file = discord.File(os.path.join(self.path, selected_image))
                embed.set_image(
                    url="attachment://" + selected_image
                )  # Embedding the image
                await member.send(file=file, embed=embed)
        else:  # user has verified role
            await ctx.send("You are already verified!")
            embed = discord.Embed(
                description="Click [Here](https://github.com/txt/se21) for the home page of the class Github page"
            )
            await member.send(embed=embed)


# --------------------------------------
# add the file to the bot's cog system
# --------------------------------------
def setup(bot):
    bot.add_cog(Helper(bot))


# Copyright (c) 2021 War-Keeper
