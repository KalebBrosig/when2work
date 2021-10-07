import time
import sqlite3
import scrape as s
from typing import List
from dateutil import parser

# Employee funcs:

def getEName(EID: str) -> str: # str(EName)
    # Get EName of an employee from their EID
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "EName" FROM `Employees` WHERE "EID" IS ?;', (EID,))

        return str(cur.fetchone()[0])
    except:
        return None
    finally:
        con.close()

def getEID(EName: str) -> str: # str(EID)
    # Get EID of an employee from their EName
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "EID" FROM `Employees` WHERE "EName" IS ?;', (EName,))

        return str(cur.fetchone()[0])
    except:
        return None
    finally:
        con.close()

def getAmtStones(EID: str) -> int: # int(num)
    # Get the amount of positions an employee is able to work from their EID
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "Positions" FROM `Employees` WHERE "EID" IS ?;', (EID,))

        return int(len(cur.fetchone()[0])/10)
    except:
        return None
    finally:
        con.close()

def getRank(Rank: str) -> List[str]: # [EID,]
    # Gets all employees with the given Rank
    # return value is [EID,]
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "EID" FROM `Employees` WHERE "Rank" IS ?;', (Rank,))

        return [str(idx[0]) for idx in cur.fetchall()]
    except:
        return None
    finally:
        con.close()

def setAllStarts():
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT DISTINCT "EID" FROM `Shifts`;')
        for EID in [str(idx[0]) for idx in cur.fetchall()]:
            try:
                cur.execute('SELECT "Start" FROM `Shifts` WHERE "EID" IS ? ORDER BY "Start" ASC;', (EID,))
                first = cur.fetchone()[0]
                cur.execute('UPDATE "Employees" SET "Start" = ? WHERE EID IS ?;', (first, EID,))
            except:
                pass
    except:
        return None
    finally:
        con.commit()
        con.close()

def isDeleted(EID: str) -> bool: # Deleted
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "Deleted" FROM `Employees` WHERE "EID" IS ?;', (EID,))
        return cur.fetchone()[0] == "True"
    except:
        return None
    finally:
        con.close()

# Shift funcs:

def getTotal(EID: str) -> int: # int(seconds)
    # Get the total amount of seconds an employee has worked
    # Should be converted into mins, hours, and days after return.
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()
        cur.execute('SELECT SUM("Duration") FROM `Shifts` WHERE "EID" IS ?;', (EID,))
        return int(cur.fetchone()[0])
    except:
        return None
    finally:
        con.close()

def getMODS(Start: int, End: int) -> List[str]: # [str(EID),]
    # Get the MODS in a time range
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        SkillID = "322487716"
        cur.execute('SELECT "EID" FROM `Shifts` WHERE "SkillID" IS ? AND "Start" < ? AND "End" > ?;', (SkillID, End, Start,))

        return [str(idx[0]) for idx in cur.fetchall()]
    except:
        return None
    finally:
        con.close()

def getShifts(Time: int) -> List[str]: # [str(ShiftID)]
    # Get all the shifts that intersect a timestamp
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "ShiftID" FROM `Shifts` WHERE "Start" < ? AND "End" > ?;', (Time, Time,))

        return [str(idx[0]) for idx in cur.fetchall()]
    except:
        return None
    finally:
        con.close()

def getWeek(Starting: str, EID: str = None) -> List[str]: # [str(ShiftID)]
    # Get all shifts in a given week starting at Starting with an optional employee filter
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        Start = parser.parse(Starting).timestamp()
        End = Start + (86400*7)
        if EID is None:
            cur.execute('SELECT "ShiftID" FROM `Shifts` WHERE "Start" > ? AND "End" < ?;', (Start, End,))
        else:
            cur.execute('SELECT "ShiftID" FROM `Shifts` WHERE "Start" > ? AND "End" < ? AND "EID" IS ?;', (Start, End, EID,))

        return [str(idx[0]) for idx in cur.fetchall()]
    except:
        return None
    finally:
        con.close()

# Database funcs:

def redoDB():
    # Delete and repopulate the w2w.db file
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('DELETE FROM `Shifts`;')
        cur.execute('DELETE FROM `Employees`;')

        driver = s.setup()
        time.sleep(2)
        s.scrapeShifts(driver, (time.time() + (86400 * 14)))
        time.sleep(2)
        s.scrapeEmployees(driver)
        time.sleep(2)
        driver.close()
    finally:
        con.commit()
        con.close()

def updateDB():
    # Update the database to have the most recent data
    driver = s.setup()
    time.sleep(4)
    s.scrapeShifts(driver, (time.time() + (86400 * 24)), (time.time() - (86400 * 44))) # give the scraper a large range to get things like employees leaving and such
    time.sleep(4)
    s.scrapeEmployees(driver)
    time.sleep(4)
    driver.close()

# Misc funcs:

def getPositionFromID(SkillID: str) -> str: # str(Pos)
    # Get the name of a position from it's SkillID
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT "Position" FROM `Shifts` WHERE "SkillID" IS ?;', (SkillID,))

        return str(cur.fetchone()[0])
    except:
        return None
    finally:
        con.close()

def getSkillIDS() -> List[str]: # [str(SkillID),]
    try:
        con = sqlite3.connect("w2w.db")
        cur = con.cursor()

        cur.execute('SELECT DISTINCT "SkillID" FROM `Shifts`;')

        return [idx[0] for idx in cur.fetchall()]
    except:
        return None
    finally:
        con.close()
