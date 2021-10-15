import discord
import sqlite3
import os

Skills = { # str(SkillID) to str(Name)
    "310853183": "Arcade",
    "656121611": "Axe Throwing",
    "415327590": "Banquet",
    "310853184": "Control Counter",
    "677654691": "Control Counter",
    "538416832": "Escape Room",
    "310853506": "Float",
    "415325361": "Go-Carts",
    "415325359": "Gounds Team",
    "400090436": "Janitorial",
    "324621987": "Kitchen Team",
    "486535897": "Bowling League Attendant",
    "312463108": "Maintenance",
    "322487716": "Manager",
    "489143721": "Manager Meeting",
    "315805767": "Office",
    "483317720": "P.T. Sports",
    "486535895": "P.T. Island",
    "656121608": "PT Social",
    "310853186": "Party Host/Hostess",
    "310853187": "Snack Bar",
    "604175097": "Supervised Play",
    "426599712": "Team Lead",
    "538411160": "The Lab",
    "316580542": "Training",
    }

Roles = {
    "310853183": 883930042802008155,# Arcade
    "656121611": 883930271227994114,# Axe Throwing
    "415327590": 883930320787869717,# Banquet
    "310853184": 883930352928837642,# Control Counter
    "538416832": 883930427046391828,# Escape Room
    "310853506": 883930496764108890,# Float
    "415325361": 883930531853647893,# Go-Carts
    "415325359": 883930596928274452,# Gounds Team
    "400090436": 883930629878726726,# Janitorial
    "324621987": 883930673134600202,# Kitchen Team
    "486535897": 883930709486604288,# Bowling League Attendant 
    "312463108": 883930757804990494,##Maintenance
    "322487716": 883924977869553734,##Manager##########
    "489143721": 883924977869553734,##Manager Meeting##
    "315805767": 883930798309376001,# Office
    "677654691": 883930352928837642,# Control Counter
    "483317720": 883930840306954290,# P.T. Sports
    "486535895": 883930891611697192,# PT Island
    "656121608": 883930923173806093,# PT Social
    "310853186": 883930951258898502,# Party Host/Hostess
    "310853187": 883930998088290354,# Snack Bar
    "604175097": 883931066694524939,# Supervised Play
    "426599712": 883925170220310608,##Team Lead
    "538411160": 883930840306954290,# The Lab
    "316580542": 898620300743307314,# Training

    "0": 883925471899820073,
    "1": 883925170220310608,
    "2": 883924977869553734
    }

con = sqlite3.connect(os.getenv("w2wDatabase"))
cur = con.cursor()
TOKEN, GUILD = os.getenv("botToken"), int(os.getenv("botGuild"))
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"{client.user} ready")

    guild: discord.guild.Guild = client.get_guild(GUILD)
    for member in guild.members:
        cur.execute("SELECT Skills FROM `Employees` WHERE DiscordID IS ?;", (member.id,))
        try:
            empSkills = cur.fetchone()[0]
            empSkills = empSkills.replace(",322487716", ""); empSkills = empSkills.replace(",489143721", "") # Prevent assigning over current rank
            
            await member.add_roles(*[guild.get_role(Roles[idx]) for idx in empSkills.split(',')])

            print(member.name)
            for String in ["   "+str(idx.name) for idx in member.roles]:
                print(String)
        except TypeError:
            print(member.name, "not in database!")

    await client.close()
client.run(TOKEN)


# Has no way of taking away roles, so that wont be a problem
# Only issue is might add random team leads
