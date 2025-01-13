import sqlite3


def create_table():
    """Erstellt die Tabelle, falls sie noch nicht existiert."""
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
            UNIQUE(user_id, btc_address)
        )
    """)
    conn.commit()
    return conn, cursor


def clear_table():
    """Leert die Tabelle, um sicherzustellen, dass keine alten Daten vorhanden sind."""
    conn, cursor = create_table()
    cursor.execute("DELETE FROM btc_addresses")
    conn.commit()
    conn.close()
    print("Tabelle geleert.")


def add_or_update_user(user_id, btc_address):
    """Fügt einen neuen Benutzer und dessen Adresse hinzu oder aktualisiert diese."""
    conn, cursor = create_table()
    cursor.execute("""
        INSERT INTO btc_addresses (user_id, btc_address)
        VALUES(?, ?)
        ON CONFLICT(user_id, btc_address) DO NOTHING
    """, (user_id, btc_address))
    conn.commit()
    conn.close()


def increment_request_count(user_id, image=False, voice=False):
    """Erhöht den Zähler für Bild- oder Audioanforderungen."""
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

    conn.commit()
    conn.close()


def return_all_data():
    """Gibt alle Daten der Tabelle zurück und druckt sie."""
    conn = sqlite3.connect("btc_addresses.db")
    rows = conn.execute("SELECT * FROM btc_addresses").fetchall()
    conn.close()
    print(rows)
    return rows


def get_btc_address(user_id):
    """Gibt alle BTC-Adressen eines Benutzers zurück."""
    conn = sqlite3.connect("btc_addresses.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT btc_address FROM btc_addresses
        WHERE user_id = ?
    """, (user_id,))
    addresses = cursor.fetchall()
    conn.close()
    return [address[0] for address in addresses]

