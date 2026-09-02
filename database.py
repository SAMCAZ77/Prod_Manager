"""
database.py
Handles all data persistence for Prod Manager using a local SQLite file.
The database file (prod_manager.db) is created next to the executable /
script on first run, so the app is fully self-contained (no server needed).
"""

import os
import sqlite3
import sys
from datetime import datetime


def get_app_dir():
    """Return the folder the app is running from (works both as a normal
    script and when frozen into a PyInstaller .exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(get_app_dir(), "prod_manager.db")


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT,
                unit TEXT DEFAULT 'pcs',
                unit_price REAL DEFAULT 0,
                stock REAL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mtype TEXT NOT NULL CHECK (mtype IN ('IN','OUT')),
                date TEXT NOT NULL,
                model TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                operator TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Products
    # ------------------------------------------------------------------ #
    def add_product(self, model, name, category, unit, unit_price, stock):
        self.conn.execute(
            """INSERT INTO products (model, name, category, unit, unit_price, stock)
               VALUES (?,?,?,?,?,?)""",
            (model.strip(), name.strip(), category.strip(), unit.strip(),
             float(unit_price or 0), float(stock or 0)),
        )
        self.conn.commit()

    def update_product(self, product_id, model, name, category, unit, unit_price, stock):
        self.conn.execute(
            """UPDATE products SET model=?, name=?, category=?, unit=?,
               unit_price=?, stock=? WHERE id=?""",
            (model.strip(), name.strip(), category.strip(), unit.strip(),
             float(unit_price or 0), float(stock or 0), product_id),
        )
        self.conn.commit()

    def delete_product(self, product_id):
        self.conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.conn.commit()

    def get_products(self, search=""):
        cur = self.conn.cursor()
        if search:
            like = f"%{search.strip()}%"
            cur.execute(
                """SELECT id, model, name, category, unit, unit_price, stock
                   FROM products WHERE model LIKE ? OR name LIKE ?
                   ORDER BY model COLLATE NOCASE""",
                (like, like),
            )
        else:
            cur.execute(
                """SELECT id, model, name, category, unit, unit_price, stock
                   FROM products ORDER BY model COLLATE NOCASE"""
            )
        return cur.fetchall()

    def get_product_by_model(self, model):
        cur = self.conn.cursor()
        cur.execute("SELECT id, model, name, category, unit, unit_price, stock "
                     "FROM products WHERE model=?", (model,))
        return cur.fetchone()

    def model_exists_for_other(self, model, product_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM products WHERE model=? AND id<>?",
                     (model, product_id))
        return cur.fetchone() is not None

    def adjust_stock(self, model, delta):
        self.conn.execute(
            "UPDATE products SET stock = stock + ? WHERE model = ?",
            (delta, model),
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Production In / Out (movements)
    # ------------------------------------------------------------------ #
    def add_movement(self, mtype, date, model, product_name, quantity,
                      operator="", notes=""):
        self.conn.execute(
            """INSERT INTO movements (mtype, date, model, product_name,
               quantity, operator, notes) VALUES (?,?,?,?,?,?,?)""",
            (mtype, date, model.strip(), product_name.strip(),
             float(quantity), operator.strip(), notes.strip()),
        )
        self.conn.commit()
        # Keep product stock in sync: IN adds to stock, OUT removes from it
        delta = float(quantity) if mtype == "IN" else -float(quantity)
        self.adjust_stock(model.strip(), delta)

    def delete_movement(self, movement_id):
        cur = self.conn.cursor()
        cur.execute("SELECT mtype, model, quantity FROM movements WHERE id=?",
                     (movement_id,))
        row = cur.fetchone()
        if row:
            mtype, model, qty = row
            delta = -qty if mtype == "IN" else qty
            self.adjust_stock(model, delta)
        self.conn.execute("DELETE FROM movements WHERE id=?", (movement_id,))
        self.conn.commit()

    def get_movements(self, mtype=None, search="", date_from=None, date_to=None):
        query = ("SELECT id, mtype, date, model, product_name, quantity, "
                  "operator, notes FROM movements WHERE 1=1")
        params = []
        if mtype:
            query += " AND mtype=?"
            params.append(mtype)
        if search:
            query += " AND (model LIKE ? OR product_name LIKE ?)"
            like = f"%{search.strip()}%"
            params.extend([like, like])
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        query += " ORDER BY date DESC, id DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def close(self):
        self.conn.close()


def today_str():
    return datetime.now().strftime("%Y-%m-%d")
