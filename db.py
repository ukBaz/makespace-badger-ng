#!/usr/bin/env python3

import sqlite3 as sqlite

class Database():
    def __init__(self, dbfile):
        self.conn = sqlite.connect(dbfile)

    def close(self):
        self.conn.close()
        self.conn = None

    def initialise(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE Tags(Tag INT, Name TEXT, Comment TEXT)")
        self.conn.commit()

    def lookup(self, tag):
        cur = self.conn.cursor()
        cur.execute("SELECT Name, Comment FROM Tags WHERE Tag = x'"+tag.encode('hex')+"'")
        return cur.fetchone()

    def update(self, tag, name, comment):
        t = (name, comment)
        cur = self.conn.cursor()
        # seems you can't use variables in a where clause...
        cur.execute("UPDATE Tags SET Name=?, Comment=? WHERE Tag=x'"+tag.encode('hex')+"'", t)
        self.conn.commit()

    def insert(self, tag, name, comment):
        t = (name, comment)
        cur = self.conn.cursor()
        cur.execute("INSERT INTO Tags VALUES(x'"+tag.encode('hex')+"', ?, ?)", t)
        self.conn.commit()
