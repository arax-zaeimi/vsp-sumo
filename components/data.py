#!/usr/bin/python
import sqlite3
import os

DB_NAME = 'simulation_db.db'
NEW_VEHICLE = 'add_one'
NEW_DESTINATION = 'update_destination'


class change_request:
    def __init__(self, action, vehicle_id, departure, destination):
        self.action = action
        self. vehicle_id = vehicle_id
        self.departure = departure
        self.destination = destination


def create_table():
    conn = sqlite3.connect(DB_NAME)

    conn.execute('''CREATE TABLE UPDATES
         (ID INTEGER PRIMARY KEY AUTOINCREMENT,
         CHANGE_TYPE         CHAR(50)     NOT NULL,
         VEHICLE_ID          CHAR(50)     NOT NULL,
         NEW_DEPARTURE       CHAR(50),
         NEW_DESTINATION     CHAR(50),
         STATUS              INT);''')

    conn.close()


def connect(database_name) -> sqlite3.Connection:
    # new_db = False
    # if not os.path.isfile(DB_NAME):
    #     new_db = True
    connection = sqlite3.connect(database_name)

    # if new_db:
    #     create_table()

    return connection


def insert_new_destination(vehicle_id, address):
    conn = connect(DB_NAME)

    conn.execute(f"INSERT INTO UPDATES (CHANGE_TYPE,VEHICLE_ID,NEW_DESTINATION,STATUS) \
      VALUES ('{NEW_DESTINATION}', '{vehicle_id}', '{address}', 0 )")

    conn.commit()
    conn.close()
    print('New destination registered.')


def insert_new_vehicle(vehicle_id, departure, destination):
    conn = connect(DB_NAME)

    conn.execute(f"INSERT INTO UPDATES (CHANGE_TYPE,VEHICLE_ID,NEW_DEPARTURE, NEW_DESTINATION,STATUS) \
      VALUES ('{NEW_VEHICLE}', '{vehicle_id}', '{departure}', '{destination}', 0 )")

    conn.commit()
    conn.close()
    print('New vehicle registered.')


def get_changes():
    changes = []

    try:
        conn = connect(DB_NAME)

        cursor = conn.execute(
            "SELECT CHANGE_TYPE, VEHICLE_ID, NEW_DEPARTURE, NEW_DESTINATION from UPDATES where STATUS = 0")

        for row in cursor:
            changes.append(change_request(
                action=row[0],
                vehicle_id=row[1],
                departure=row[2],
                destination=row[3]))

        conn.close()
    except:
        print('Error while reading the database file.')

    return changes


def clear_changes():
    conn = connect(DB_NAME)

    conn.execute(f"DELETE FROM UPDATES")
    conn.commit()
    conn.close()


def mark_change_done(change_id):
    conn = connect(DB_NAME)

    conn.execute(f"UPDATE UPDATES set STATUS = 1 where ID = {change_id}")
    conn.commit()
    conn.close()
