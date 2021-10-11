import sqlite3
import discord
import os
from w2w import *

TOKEN, GUILD = os.getenv("w2wD"), int(os.getenv("w2wG"))
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"{client.user} Ready")

    guild: discord.guild.Guild = client.get_guild(GUILD)
    MODS = getMODS(int(time.time()), int(time.time())+3600)
    for mod in MODS:
        DiscordID = getDiscordIDByEID(mod)
        member = guild.get_member(int(DiscordID))
        try:
            await member.add_roles(guild.get_role(895780333469962310))
        except discord.errors.Forbidden:
            print("Tried to assign higher than current rank!")
            pass

    for member in guild.members:
        eid = getEIDByDiscordID(str(member.id))
        guildMember = guild.get_member(int(member.id))
        if str(eid) in MODS: continue
        try:
            await guildMember.remove_roles(guild.get_role(895780333469962310))
        except discord.errors.Forbidden:
            print("Tried to assign higher than current rank!")
            pass

    await client.close()

client.run(TOKEN)
