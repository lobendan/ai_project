import sys
import os
import time
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the database folder to sys.path
sys.path.append(project_root)
from plate_bot.src.database.sqliteDB import SQLiteDB

class PlateGetter:
    def __init__(self, state, max_age_minutes = 60, min_len=1, max_len=7):
        self.db = SQLiteDB("plate_bot/src/database/plates.db")
        self.state = state
        self.max_age = max_age_minutes
        self.min_len = min_len
        self.max_len = max_len

    def check_plate_availability(self, plates):
        available = []
        not_available = []

        for plate in plates:

            if self.db.was_recently_updated(plate, self.state, self.max_age):
                if self.db.get_word_availability(plate, self.state) == "available":
                    available.append(plate)

                else:
                    not_available.append(plate)

            else:
                self.db.set_last_checked_old(plate, self.state)
                ticker = 0
                #waits a max of 20 seconds until word is checked again and still available, if it changes to unavailable it  
                while(ticker<40):
                    if self.db.was_recently_updated(plate, self.state):
                        if self.db.was_recently_updated(plate, self.state, self.max_age):
                            if self.db.get_word_availability(plate, self.state) == "available":
                                available.append(plate)
                                break

                            else:
                                not_available.append(plate)
                                break
                    else: 
                        time.sleep(1)
                        ticker+=1

                if ticker>=40:
                    print("Warning: Plate availability check timed out for plate:", plate)
                    not_available.append(plate)    

        return available, not_available
            

