import sqlite3

def create_table():
    conn = sqlite3.connect("btc_addresses.db")

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS btc_addresses( 
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        btc_address TEXT NOT NULL,
        UNIQUE(user_id, btc_address))
        """)
    conn.commit()
    return conn, cursor

def add_or_update_user(user_id, btc_address):
    conn, cursor = create_table()
    cursor.execute("""
    INSERT INTO btc_addresses (user_id, btc_address)
    VALUES(?, ?)
    ON CONFLICT(user_id, btc_address) DO NOTHING
    """, (user_id, btc_address))
    conn.commit()
    conn.close()

def get_btc_address(user_id):
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT btc_address FROM btc_addresses
        WHERE user_id = ?
    """, (user_id,))
    addresses = cursor.fetchall()
    conn.close()
    return [address[0] for address in addresses]

