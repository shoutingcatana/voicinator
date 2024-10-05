import sqlite3


def create_table():
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()

    # Tabelle erstellen, wenn sie nicht existiert
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS btc_addresses( 
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        btc_address TEXT NOT NULL,
        count_image_requests INTEGER DEFAULT 0,
        count_audio_requests INTEGER DEFAULT 0,
        UNIQUE(user_id, btc_address))
    """)
    conn.commit()
    return conn, cursor

def count_users_requests(user_id):
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT count_image_requests, count_audio_requests FROM btc_addresses
        WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()  # Ein Ergebnis abrufen
    conn.close()

    if result:  # Prüfen, ob ein Ergebnis gefunden wurde
        count_image_requests, count_audio_requests = result
        return count_image_requests, count_audio_requests
    else:
        return 0, 0  # Rückgabe von 0, falls der Benutzer nicht gefunden wurde


def add_columns():
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()

    # Neue Spalte für count_image_requests hinzufügen, falls sie nicht existiert
    try:
        cursor.execute("ALTER TABLE btc_addresses ADD COLUMN count_image_requests INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        print("Spalte count_image_requests existiert bereits.")

    # Neue Spalte für count_audio_requests hinzufügen, falls sie nicht existiert
    try:
        cursor.execute("ALTER TABLE btc_addresses ADD COLUMN count_audio_requests INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        print("Spalte count_audio_requests existiert bereits.")

    conn.commit()
    conn.close()





def add_or_update_user(user_id, btc_address):
    conn, cursor = create_table()  # Sicherstellen, dass die Tabelle existiert
    cursor.execute("""
    INSERT INTO btc_addresses (user_id, btc_address)
    VALUES(?, ?)
    ON CONFLICT(user_id, btc_address) DO UPDATE SET btc_address = excluded.btc_address
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


def increment_request_count(user_id, image=False, voice=False):
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()

    if image:
        cursor.execute("""
            UPDATE btc_addresses
            SET count_image_requests = count_image_requests + 1
            WHERE user_id = ?
        """, (user_id,))

    if voice:
        cursor.execute("""
            UPDATE btc_addresses
            SET count_audio_requests = count_audio_requests + 1
            WHERE user_id = ?
        """, (user_id,))

    # Änderungen speichern und Verbindung schließen
    conn.commit()
    conn.close()

    print(f"Der user: {user_id} hat eine Anfrage an {'image extractor' if image else 'voice extractor'} gesendet")

add_columns()


