import sqlite3
import discord
import os
import w2w

# To switch to pt discord, change RoleIDs and Env vars (specifically w2wG)

def getEIDByDiscordID(DiscordID: str) -> str: # EID
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "EID" FROM `Employees` WHERE "DiscordID" IS ?;', (DiscordID,))
        return str(cur.fetchone()[0])
    except:
        return None
    finally:
        con.close()

def getPositionsByEID(EID: str) -> list[str]: # [SkillID]
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "Skills" FROM `Employees` WHERE "EID" IS ?;', (EID,))
        return [str(idx) for idx in cur.fetchone()[0].split(",")[0:-1]]
    except:
        return None
    finally:
        con.close()

RoleIDs = { # {SkillID: RoleID,}
    310853183: 891922814423142480, # Arcade
    310853184: 892074545379409930, # Control Counter
    415325361: 891922939614756925, # Go-Carts
    324621987: 892074694386266172, # Kitchen Team
    312463108: 892074840608100373, ##Maintenance
    322487716: 892074964096811009, ##Manager
    315805767: 892075133244694569, # Office
    483317720: 892075228736413736, # P.T. Sports
    310853187: 892075334051172362, # Snack Bar
    426599712: 892075427303137291, ##Team Lead
    316580542: 891922967162929162, # Training
    486535897: 892075550011719710, # Bowling League Attendant
    310853186: 892075758116302849, # Party Host/Hostess
    538416832: 892075958268481626, # Escape Room
    310853506: 892076050174066718, # Float
    656121611: 892076183636807740, # Axe Throwing
    677654691: 892074545379409930, # Control Counter
    486535895: 892077178508967936, # PT Island
    656121608: 892077227590701127, # PT Social
    415325359: 892077274491420713, # Grounds Team
    604175097: 892077319563382784, # Supervised Play
    415327590: 892077387905380392, # Banquet
    400090436: 892077425045930054, # Janitorial
    538411160: 892077465990725662, # The Lab
    489143721: 892078326770991124, # Manager Meeting
}

# Discord

TOKEN, GUILD = os.getenv("w2wD"), int(os.getenv("w2wG"))
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"{client.user} Ready")

    guild: discord.guild.Guild = client.get_guild(GUILD)
    for member in guild.members:
        eid = getEIDByDiscordID(str(member.id))
        if eid == None:
            print(member.name, "Not found in database!")
            continue
        if w2w.isDeleted(eid): 
            await member.kick() # when testing do not include this line!!!!!!!
            print(f"Kicked {member.name}")
            continue
        
        print(member.name)
        for SkillID in getPositionsByEID(eid):
            RoleID = int(RoleIDs[int(SkillID)])
            print("    ", SkillID, RoleID)
            try:
                await member.add_roles(guild.get_role(RoleID)) # when testing do not include this line!!!!!!!!!!!
            except discord.errors.Forbidden:
                print("Tried to assign higher than current rank!")
                pass

    await client.close()

client.run(TOKEN)
