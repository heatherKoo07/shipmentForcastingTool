"""
Author: Mia Skinner

Mia Skinner
Heather Koo
CIS41B Final project
shipmentsDB.py:
- creates new database called "Shipments.db" to store historical, shipment data.
- Only run once if Shipments.db is missing, or to re-generate with a new JSON data file.
"""

import json
import sqlite3

DATA_FILE = 'data_201811191543.json'

class BuildShipmentDB(object):
    """ Uses the JSON file as input to build the database into a SQLite file.
    """

    def __init__(self, data):
        """
        Uses the JSON file as input to build the database into a SQLite file.
        :param data - a JSON file name
        """
        self._readJSON(data)
        try:
            self.conn = sqlite3.connect('Shipments.db')
            self.cur = self.conn.cursor()
            self._createTable()
            self._insertData()

            self.conn.commit()
            self.conn.close()

        except sqlite3.DatabaseError as e:
            print("Database Error: ", e)

    def _readJSON(self, data):
        """
        Creates a Python list of dictionary objects from a JSON file.
        :param data - a JSON file name
        :return: None
        """
        try:
            with open(data, 'r') as fh:
                self.dataDict = json.load(fh)

        except FileNotFoundError as e:
            print("Unable to open file ", data, ", exiting program. ", e)
            raise SystemExit()


    def _createTable(self):
        """
        Creates a main shipment table using SQL commands.
        Example entry:
            "csd_date_wid" : 16649,
            "date_wid" : 16649,
            "cbd_date_wid" : 16679,
            "customer_wid" : 1773,
            "mkt_item_wid" : 13744,
            "cust_book_date" : "2015-08-31T07:00:00Z",
            "cust_ship_date" : "2015-08-01T07:00:00Z",
            "order_number" : "SO4660",
            "quantity" : 1.00
        """
        self.cur.execute("DROP TABLE IF EXISTS Shipments")
        self.cur.execute('''CREATE TABLE Shipments (
                                id INTEGER NOT NULL PRIMARY KEY,
                                csd_date_wid INTEGER,
                                date_wid INTEGER,
                                customer_wid INTEGER,
                                mkt_item_wid INTEGER,
                                cust_ship_date DATE,
                                order_number TEXT,
                                quantity INTEGER)''')


    def _insertData(self):
        """
        Inserts data into Shipments table from the dictionary.
        :return: None
        """
        for d in self.dataDict:
            self.cur.execute('''INSERT INTO Shipments
                   (csd_date_wid, date_wid, customer_wid, mkt_item_wid, cust_ship_date, order_number, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''', (d['csd_date_wid'],
                                             d['date_wid'],
                                             d['customer_wid'],
                                             d['mkt_item_wid'],
                                             d['cust_ship_date'],
                                             d['order_number'],
                                             d['quantity']))

def main():
    """
    Store JSON file in SQLite DB
    """
    print("Building database...")
    BuildShipmentDB(DATA_FILE)
    print("******** Completed building Shipment.db database ********")


def test():
    conn = sqlite3.connect('Shipments.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM Shipments")
    print(cur.fetchall())
    conn.close()

main()
#test()