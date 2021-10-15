import os 
import re
import sqlite3
import requests
import urllib.parse
import json
import time
import dateutil.parser as dateParser
from datetime import datetime
from lxml import etree
from sqlite3.dbapi2 import Connection, Cursor

con: Connection
cur: Cursor
session = requests.session()
DOMAIN = os.getenv("w2wDomain")
USERNAME = os.getenv("w2wUsername")
PASSWORD = os.getenv("w2wPassword")
Overwrite_blacklist = [686024997, 697980471]

class shift:
    def __init__(self, EID: str, EName: str, Description: str, Start: int, End: int, SkillID: str, ShiftID: str):
        self.EID: str = EID
        self.EName: str = EName.replace(" (deleted)", "")
        self.Deleted: str = str(EName.find("(deleted)") != -1)
        self.Description: str = Description
        self.Date: str = datetime.fromtimestamp(Start).date()
        self.Start: int = Start
        self.End: int = End
        self.ShiftID: str = ShiftID
        self.SkillID: str = SkillID

class employee:
    def __init__(self, EID, EName):
        self.EID = EID
        self.EName = EName.replace(" (deleted)", "")
        self.Deleted = str(EName.find("(deleted)") != -1)
        
        self.Skills = ""
        self.Rank = "Employee"
    
    def setRank(self, Current):
        if self.Skills == "": return
        if (self.Skills.find("426599712") != -1) or Current == "Team Lead": self.Rank = "Team Lead"
        if (self.Skills.find("312463108") != -1) or Current == "Maintenance": self.Rank = "Maintenance"
        if (self.Skills.find("322487716") != -1) or Current == "Manager": self.Rank = "Manager"

def login(): # SID, W2W
    global session, DOMAIN, USERNAME, PASSWORD, con, cur
    con = sqlite3.connect(os.getenv("w2wDatabase"))
    cur = con.cursor()

    data = {
        'name': 'signin',
        'Launch': '',
        'LaunchParams': '',
        'UserId1': USERNAME,
        'Password1': PASSWORD,
        'captcha_required': 'false',
        'Submit1': 'Please Wait...'
        }

    page = session.get(f'https://{DOMAIN}/cgi-bin/w2w.dll/login', data=data)
    tree = etree.HTML(page.content)
    SID = tree.xpath("head/script[1]")[0].attrib["data-sid"]
    W2W = tree.xpath("head/script[1]")[0].attrib["data-w2w"]
    return SID, W2W

def scrapeShifts(SID: str, W2W: str, start: int = int(time.time()), end: int = 1259388000):
    global session, DOMAIN, con, cur
    assert end < start
    currentTime = start
    while currentTime > end:
        Date = datetime.fromtimestamp(currentTime).strftime("%m/%d/%Y"); print(Date)
        page = session.get(f'https://www3.{DOMAIN}{W2W}empfullschedule?SID={SID}&View=Day&Date={Date}')
        tree = etree.HTML(page.content)

        SkillID = ""
        for item in tree.xpath('//*[@class="bd"]/script'):
            if item.text == None: continue
            if item.text.find("hdc(") != -1: continue
            if item.text.find("php(") != -1: SkillID = re.search('"[0123456789]*?"', item.text)[0][1:-1]; continue

            text = urllib.parse.unquote(item.text)
            hdr = re.search('hdr\(.*?,[0123456789]*,(?P<EID>.*?),"(?P<EName>.*?)"\);', text)
            cl = re.search('cl\(.*?"(?P<ShiftID>[!$#*~123456789].*?)",".*?(?P<JSON>{.*?})', text)
            shiftJSON = json.loads(cl.group("JSON"))
            Start = int(dateParser.parse(Date + " " + shiftJSON["start"]).timestamp())
            End = int(dateParser.parse(Date + " " + shiftJSON["end"]).timestamp())

            if SkillID != shiftJSON["skillid"]: exit("Non-Matching SkillIDs") 
            shiftObj = shift(hdr.group("EID"), hdr.group("EName"), shiftJSON["description"], Start, End, SkillID, cl.group("ShiftID"))
            empObj = employee(hdr.group("EID"), hdr.group("EName"))

            cur.execute('SELECT COUNT(ShiftID) FROM `Shifts` WHERE ShiftID is ?;', (shiftObj.ShiftID,))
            if cur.fetchone()[0] > 0: cur.execute(
                'UPDATE `Shifts` SET EID=?,EName=?,Deleted=?,Description=?,Date=?,Start=?,End=?,SkillID=? WHERE ShiftID is ?;', 
                (shiftObj.EID, shiftObj.EName, shiftObj.Deleted, shiftObj.Description, shiftObj.Date, shiftObj.Start, shiftObj.End, shiftObj.SkillID, shiftObj.ShiftID,)
            )
            else: cur.execute(
                'INSERT INTO `Shifts` (EID, EName, Deleted, Description, Date, Start, End, ShiftID, SkillID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);',
                (shiftObj.EID, shiftObj.EName, shiftObj.Deleted, shiftObj.Description, shiftObj.Date, shiftObj.Start, shiftObj.End, shiftObj.ShiftID, shiftObj.SkillID,)
            )

            cur.execute('SELECT COUNT(EID) FROM `Employees` WHERE EID IS ?', (empObj.EID,))
            if cur.fetchone()[0] == 0: cur.execute(
                'INSERT INTO `Employees` (EID, EName, Deleted, Rank) VALUES (?, ?, ?, ?);',
                (empObj.EID, empObj.EName, empObj.Deleted, empObj.Rank)
            )

        con.commit()
        currentTime -= 86400

def scrapeEmployees(SID: str, W2W: str):
    global session, DOMAIN, con, cur
    eids = dict() # {EID: {SkillID, SkillID}}
    enames = dict() # {EID: EName}
    page = session.get(f'https://www3.{DOMAIN}{W2W}empemplist.htm?SID={SID}&SkillFilter=-1')
    tree = etree.HTML(page.content)

    SkillIDs = []
    for option in tree.xpath('//*[@class="modwideclear"]/tr/td[2]/select/option'):
        SkillID = option.attrib["value"]
        print(SkillID, option.text)
        if SkillID == "" or int(SkillID) < 0: continue
        SkillIDs.append(SkillID)

    for SkillID in SkillIDs:
        empPage = session.get(f'https://www3.{DOMAIN}{W2W}empemplist.htm?SID={SID}&SkillFilter={SkillID}')
        empTree = etree.HTML(empPage.content)
        print(SkillID)
        for empRow in empTree.xpath('//*[@aria-label="employee name"]/a'):
            EID = re.search("'(?P<EID>.*?)'", empRow.attrib["onclick"]).group("EID")
            enames[EID] = empRow.text
            if EID not in eids: eids[EID] = set()
            eids[EID].add(SkillID)
            print("    ", EID)

    for EID, Skills in eids.items():
        if int(EID) in Overwrite_blacklist: continue
        empObj = employee(EID, enames[EID])
        empObj.Skills = ",".join(Skills)
        cur.execute('SELECT "Rank" FROM `Employees` WHERE EID IS ?;', (empObj.EID,))
        try: empObj.setRank(cur.fetchone()[0])
        except: continue
        cur.execute('UPDATE `Employees` SET EName=?,Deleted=?,Rank=?,Skills=? WHERE EID IS ?;', (empObj.EName, empObj.Deleted, empObj.Rank, empObj.Skills, empObj.EID,))
    con.commit()

#Cleanup:
#con.close()
#session.close()
