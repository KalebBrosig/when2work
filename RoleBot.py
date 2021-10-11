import discord
import os
from w2w import *

# To switch to pt discord, change RoleIDs and Env vars (specifically w2wG)

RoleIDs = { # {SkillID: RoleID,}
    322487716: 892074964096811009, ##Manager
    489143721: 892074964096811009, ##Manager Meeting
    # Bot rank here
    312463108: 892074840608100373, ##Maintenance
    426599712: 892075427303137291, ##Team Lead
    315805767: 892075133244694569, # Office
    310853184: 892074545379409930, # Control Counter
    677654691: 892074545379409930, # Control Counter
    324621987: 892074694386266172, # Kitchen Team
    310853187: 892075334051172362, # Snack Bar
    310853183: 891922814423142480, # Arcade
    415325361: 891922939614756925, # Go-Carts
    # Niche below
    310853506: 892076050174066718, # Float
    415327590: 892077387905380392, # Banquet
    310853186: 892075758116302849, # Party Host/Hostess
    483317720: 892075228736413736, # P.T. Sports
    486535897: 892075550011719710, # Bowling League Attendant
    538416832: 892075958268481626, # Escape Room
    656121611: 892076183636807740, # Axe Throwing
    486535895: 892077178508967936, # PT Island
    656121608: 892077227590701127, # PT Social
    415325359: 892077274491420713, # Grounds Team
    604175097: 892077319563382784, # Supervised Play
    400090436: 892077425045930054, # Janitorial
    538411160: 892077465990725662, # The Lab
    316580542: 891922967162929162, # Training
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

        if isDeleted(eid): 
            await member.kick() # when testing do not include this line!!!!!!!
            print(f"Kicked {member.name}")
            continue
        
        print(member.name, "(", getEName(getEIDByDiscordID(str(member.id))), ")")
        for SkillID in getPositionsByEID(eid):
            RoleID = int(RoleIDs[int(SkillID)])
            print("    ", SkillID, RoleID, getPositionFromID(SkillID))
            try:
                await member.add_roles(guild.get_role(RoleID)) # when testing do not include this line!!!!!!!!!!!
            except discord.errors.Forbidden:
                print("Tried to assign higher than current rank!")
                pass

    await client.close()

client.run(TOKEN)
