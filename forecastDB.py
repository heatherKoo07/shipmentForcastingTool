"""
Author: Heather Koo

Mia Skinner
Heather Koo
CIS41B Final project
forecastDB.py:
- creates new database called "Forecast.db" to store predicted data.
"""

import sqlite3

class forecastDB(object):
    """ creates new database called "Forecast.db" to store predicted data.
    """
    def __init__(self):
        """ creates new database called "Forecast.db" to store predicted data.
        """
        try:
            self.conn = sqlite3.connect('Forecast.db')
            self.cur = self.conn.cursor()
            self._createTable()

            self.conn.commit()
            self.conn.close()
        except sqlite3.DatabaseError as e:
            print("Database Error: ", e)

    def _createTable(self):
        """ creates a new table called Forecast that contains predicted data information.
        """
        self.cur.execute("DROP TABLE IF EXISTS Forecast")
        self.cur.execute('''CREATE TABLE Forecast (
                                id INTEGER NOT NULL PRIMARY KEY,
                                productID INTEGER,
                                forecastRun DATE,
                                period TEXT,
                                expirationDate DATE,
                                quantity REAL,
                                accuracy REAL)''')

forecastDB()