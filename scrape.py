import os
import time
import json
import atexit
import sqlite3
import urllib.parse
from typing import List
from dateutil import parser
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class shift:
    def __init__(self, EID, EName, Position, Description, Start, End, SkillID, ShiftID):
        self.EID = EID
        self.EName = EName if EName.find("(deleted)") == -1 else EName.replace(" (deleted)", "")
        self.Position = Position
        self.Description = Description
        self.Date = datetime.fromtimestamp(Start).date()
        self.Start = Start
        self.End = End
        self.Duration = (End - Start) if End > Start else ((End + 86400) - Start) # Correct for midnight and later shifts
        self.Deleted = str(EName.find("(deleted)") != -1)
        self.SkillID = SkillID
        self.ShiftID = ShiftID

class employee:
    def __init__(self, EID, EName, Deleted):
        self.EID = EID
        self.EName = EName
        self.Deleted = Deleted
        self.Skills = str()

    def setRank(self):
        if self.Skills is None: return
        if (self.Skills.find("322487716") != -1):
            self.Rank = "Manager"
        elif (self.Skills.find("426599712") != -1):
            self.Rank = "Team Lead"
        elif (self.Skills.find("312463108") != -1):
            self.Rank = "Maintenance"
        else:
            self.Rank = "Employee"

def setup() -> webdriver:
    driver: webdriver = webdriver.Safari()
    atexit.register(driver.close)

    driver.get("https://whentowork.com/login.htm")
    WebDriverWait(driver, 10).until(EC.title_contains("W2W Sign In"))
    time.sleep(1) # Load JS
    username, password = str(os.getenv("w2wU")), str(os.getenv("w2wP"))
    driver.find_element_by_id("username").send_keys(username)
    driver.find_element_by_id("password").send_keys(password)
    while True: 
        if driver.find_element_by_id("password").get_attribute("value") == password: break
    driver.find_element_by_id("password").send_keys(Keys.ENTER)
    WebDriverWait(driver, 10).until(EC.title_contains("Home"))

    return driver

def scrapeShifts(driver: webdriver, start: int = int(time.time()), end: int = 1259388000):
    con = sqlite3.connect("w2w.db")
    cur = con.cursor()

    currentTime = start
    while currentTime > end:
        Date = datetime.fromtimestamp(currentTime).strftime("%m/%d/%Y")
        print(Date) # to show progress

        driver.execute_script(f"ReplWin('empfullschedule','&View=Day&Date='+'{Date}');")
        WebDriverWait(driver, 10).until(EC.title_contains("Schedule"), EC.url_contains("empfullschedule"))
        time.sleep(1.5) # Load Elements
        assert Date in driver.current_url

        POS, SID = "", ""
        for item in driver.find_elements_by_xpath('//*[@id="maincontent"]/table[1]/tbody/tr[2]/td/table/tbody/script'):
            func = urllib.parse.unquote(item.text)
            if func[0:3] == "php":
                func = func.split('"')
                POS, SID = func[5], func[1]
                continue
            func = func.split(";")
            hdr = func[0].split("\"")
            cl = func[[idx for idx, element in enumerate(func) if element.__contains__("cl(")][0]].split(",")
            clidx = [idx for idx, s in enumerate(cl) if '{' in s][0]
            ShiftJson = json.loads(", ".join(cl[clidx:])[1:-2])
            assert SID == ShiftJson["skillid"]

            EID, EName = hdr[2].split(",")[2], hdr[3]
            ShiftID = cl[3][1:-1]
            startTime = int(parser.parse(f"{Date} {ShiftJson['start']}").timestamp())
            endTime = int(parser.parse(f"{Date} {ShiftJson['end']}").timestamp())

            Shift = shift(EID, EName, POS, ShiftJson["description"], startTime, endTime, SID, ShiftID)
            
            cur.execute('SELECT * FROM `Shifts` WHERE "ShiftID" IS ?;', (Shift.ShiftID,))
            if len(cur.fetchall()) == 0:
                cur.execute('INSERT INTO `Shifts` ("EID", "EName", "Position", "Description", "Date", "Start", "End", "Duration", "Deleted", "SkillID", "ShiftID") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', (Shift.EID, Shift.EName, Shift.Position, Shift.Description, Shift.Date, Shift.Start, Shift.End, Shift.Duration, Shift.Deleted, Shift.SkillID, Shift.ShiftID,))
            else:
                cur.execute('UPDATE `Shifts` SET "EID" = ?, "EName" = ?, "Deleted" = ? WHERE "ShiftID" IS ?', (Shift.EID, Shift.EName, Shift.Deleted, Shift.ShiftID,))

            cur.execute('SELECT * FROM `Employees` WHERE "EID" IS ?;', (Shift.EID,))
            if len(cur.fetchall()) == 0:
                cur.execute('INSERT INTO `Employees` ("EID", "EName", "Deleted") VALUES (?, ?, ?);', (Shift.EID, Shift.EName, Shift.Deleted,))
            else:
                cur.execute('UPDATE `Employees` SET "Deleted" = ? WHERE EID IS ?;', (Shift.Deleted, Shift.EID,))

        con.commit()
        currentTime -= 86400
    con.commit()
    con.close()

def scrapeEmployees(driver: webdriver):
    eids = dict() # {EID: {POSID, POSID}}
    enames = dict() # {EID: EName}
    con = sqlite3.connect("w2w.db")
    cur = con.cursor()

    driver.execute_script(f"ReplWin('empemplist.htm','')")
    WebDriverWait(driver, 10).until (EC.title_contains("Staff List"))
    assert "empemplist" in driver.current_url
    time.sleep(1)
        
    for SkillID in [idx.get_attribute("value") for idx in driver.find_elements_by_xpath("/html/body/div[2]/table/tbody/tr/td[2]/select/option")]:
        if SkillID == '' or int(SkillID) < 0: continue
        print(SkillID)
        Select(driver.find_element_by_xpath("/html/body/div[2]/table/tbody/tr/td[2]/select")).select_by_value(SkillID)
        time.sleep(1) # implicit wait to change the value (change to dynamic later)
        for item in [idx for idx in driver.find_elements_by_xpath('//*[@id="maincontent"]/table[1]/tbody/tr[2]/td/table/tbody/tr')]:
            try:
                EID = item.find_elements_by_xpath('./td[1]/*')[0].get_attribute("onclick").split("'")[1]
                print(EID)
                if EID not in eids: eids[EID] = set()
                eids[EID].add(SkillID)
                if EID not in enames: enames[EID] = item.find_elements_by_xpath('./td[1]/*')[0].text
            except:
                pass

    for EID, Skills in eids.items():
        cur.execute('SELECT * FROM `Employees` WHERE "EID" IS ?;', (EID,))
        emp = cur.fetchone()
        try:
            empobj = employee(emp[0], emp[1], emp[2])
            for SkillID in Skills:
                empobj.Skills = empobj.Skills + SkillID + ","
            empobj.setRank()
        except:
            cur.execute('INSERT INTO `Employees` ("EID", "EName", "Deleted", "Rank") VALUES (?, ?, ?, ?);', (EID, enames[EID], "False", "Employee"))
            continue # temp fix for random EIDS
        cur.execute('UPDATE `Employees` SET "Skills" = ?, "Rank" = ? WHERE EID IS ?;', (empobj.Skills, empobj.Rank, EID,))
    con.commit()
    con.close()
