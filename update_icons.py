import sqlite3
import os
from datetime import datetime

def insert_and_update_icons(db_path):
    conn = None
    try:
        # Ensure the database file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the current timestamp
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert new icons into icons_icon
        insert_icons_query = f"""
        INSERT INTO icons_icon (name, fa_class, icon_type, custom_icon, is_active, category_id, created_at, updated_at)
        VALUES
            ('Wi-Fi', 'fa-wifi', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Riscaldamento', 'fa-fire', 'fontawesome', '', 1, 3, '{current_timestamp}', '{current_timestamp}'),
            ('Lavatrice', 'fa-water', 'fontawesome', '', 1, 3, '{current_timestamp}', '{current_timestamp}'),
            ('Ferro da stiro', 'fa-tshirt', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('TV', 'fa-tv', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Frigo', 'fa-snowflake', 'fontawesome', '', 1, 3, '{current_timestamp}', '{current_timestamp}'),
            ('Microonde', 'fa-microwave', 'fontawesome', '', 1, 3, '{current_timestamp}', '{current_timestamp}'),
            ('Balcone', 'fa-umbrella-beach', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Terrazza', 'fa-house', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Vista città', 'fa-city', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Ascensore', 'fa-arrow-up-down', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Parcheggio', 'fa-parking', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Piscina', 'fa-swimming-pool', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Palestra', 'fa-dumbbell', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Giardino', 'fa-leaf', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Centro storico', 'fa-landmark', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Vicino metro', 'fa-subway', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Vicino bus', 'fa-bus', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Zona tranquilla', 'fa-bed', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Vicino ristoranti', 'fa-utensils', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Cassaforte', 'fa-lock', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Rilevatore fumo', 'fa-bell', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Estintore', 'fa-fire-extinguisher', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Kit pronto soccorso', 'fa-first-aid', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Serratura smart', 'fa-key', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Netflix', 'fa-film', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Prime Video', 'fa-video', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Disney+', 'fa-magic', 'fontawesome', '', 1, 2, '{current_timestamp}', '{current_timestamp}'),
            ('Xbox', 'fa-gamepad', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}'),
            ('Biliardo', 'fa-circle', 'fontawesome', '', 1, 5, '{current_timestamp}', '{current_timestamp}');
        """
        cursor.execute(insert_icons_query)

        # Update amenities_amenity to associate icon_id
        amenities_updates = [
            ('Wi-Fi', 'fa-wifi'),
            ('Riscaldamento', 'fa-fire'),
            ('Lavatrice', 'fa-water'),
            ('Ferro da stiro', 'fa-tshirt'),
            ('TV', 'fa-tv'),
            ('Frigo', 'fa-snowflake'),
            ('Microonde', 'fa-microwave'),
            ('Balcone', 'fa-umbrella-beach'),
            ('Terrazza', 'fa-house'),
            ('Vista città', 'fa-city'),
            ('Ascensore', 'fa-arrow-up-down'),
            ('Parcheggio', 'fa-parking'),
            ('Piscina', 'fa-swimming-pool'),
            ('Palestra', 'fa-dumbbell'),
            ('Giardino', 'fa-leaf'),
            ('Centro storico', 'fa-landmark'),
            ('Vicino metro', 'fa-subway'),
            ('Vicino bus', 'fa-bus'),
            ('Zona tranquilla', 'fa-bed'),
            ('Vicino ristoranti', 'fa-utensils'),
            ('Cassaforte', 'fa-lock'),
            ('Rilevatore fumo', 'fa-bell'),
            ('Estintore', 'fa-fire-extinguisher'),
            ('Kit pronto soccorso', 'fa-first-aid'),
            ('Serratura smart', 'fa-key'),
            ('Netflix', 'fa-film'),
            ('Prime Video', 'fa-video'),
            ('Disney+', 'fa-magic'),
            ('Xbox', 'fa-gamepad'),
            ('Biliardo', 'fa-circle'),
        ]

        for amenity_name, fa_class in amenities_updates:
            update_query = f"""
            UPDATE amenities_amenity
            SET icon_id = (SELECT id FROM icons_icon WHERE fa_class = '{fa_class}')
            WHERE name = '{amenity_name}';
            """
            cursor.execute(update_query)

        # Commit the changes and close the connection
        conn.commit()
        print("Icons and amenities updated successfully.")

    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

# Path to the database file
db_path = "C:/Users/info/prove_python/booking_env/Rhome_book/db.sqlite3"
insert_and_update_icons(db_path)
