import sqlite3
from datetime import datetime

def setup_amenities():
    # Connessione al database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Data corrente per i campi created_at e updated_at
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # 1. Creazione categoria icone se non esiste già
    icon_categories = [
        ('Amenities', 'amenities', 1)
    ]
    
    for cat in icon_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO icons_iconcategory (name, slug, "order")
            VALUES (?, ?, ?)
        ''', cat)
        
    # Ottieni l'ID della categoria icone
    cursor.execute('SELECT id FROM icons_iconcategory WHERE slug = ?', ('amenities',))
    icon_category_id = cursor.fetchone()[0]

    # 2. Creazione delle icone di default per ogni categoria
    icons = [
        ('EssenzialiIcon', 'fa', 'fa-home', '', True, current_time, current_time, icon_category_id),
        ('CucinaIcon', 'fa', 'fa-utensils', '', True, current_time, current_time, icon_category_id),
        ('BagnoIcon', 'fa', 'fa-bath', '', True, current_time, current_time, icon_category_id),
        ('CameraIcon', 'fa', 'fa-bed', '', True, current_time, current_time, icon_category_id),
        ('LavanderiaIcon', 'fa', 'fa-washing-machine', '', True, current_time, current_time, icon_category_id),
        ('ComfortIcon', 'fa', 'fa-tv', '', True, current_time, current_time, icon_category_id),
        ('EsterniIcon', 'fa', 'fa-tree', '', True, current_time, current_time, icon_category_id),
        ('SicurezzaIcon', 'fa', 'fa-shield', '', True, current_time, current_time, icon_category_id),
        ('PremiumIcon', 'fa', 'fa-star', '', True, current_time, current_time, icon_category_id),
        ('AccessibilitaIcon', 'fa', 'fa-wheelchair', '', True, current_time, current_time, icon_category_id),
        ('BambiniIcon', 'fa', 'fa-baby', '', True, current_time, current_time, icon_category_id),
        ('PetIcon', 'fa', 'fa-paw', '', True, current_time, current_time, icon_category_id)
    ]
    
    for icon in icons:
        cursor.execute('''
            INSERT OR IGNORE INTO icons_icon 
            (name, icon_type, fa_class, custom_icon, is_active, created_at, updated_at, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', icon)

    # 3. Creazione delle categorie di amenities
    amenity_categories = [
        ('Essenziali', 1),
        ('Cucina e Zona Pranzo', 2),
        ('Bagno', 3),
        ('Camera da letto', 4),
        ('Lavanderia e Pulizia', 5),
        ('Comfort e Intrattenimento', 6),
        ('Esterni e Parcheggio', 7),
        ('Sicurezza', 8),
        ('Servizi Premium', 9),
        ('Accessibilità', 10),
        ('Servizi per Bambini', 11),
        ('Pet-Friendly', 12)
    ]
    
    for cat in amenity_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO amenities_amenitycategory (name, "order")
            VALUES (?, ?)
        ''', cat)

    # 4. Associazione delle icone alle categorie
    icon_mapping = {}
    for icon in icons:
        cursor.execute('SELECT id FROM icons_icon WHERE name = ?', (icon[0],))
        icon_id = cursor.fetchone()[0]
        icon_mapping[icon[0]] = icon_id

    # 5. Creazione delle amenities con riferimenti alle icone
    amenities = [
        # Essenziali
        ('Wi-Fi ad alta velocità', 'Internet veloce e affidabile', True, 1, 1, icon_mapping['EssenzialiIcon']),
        ('Aria condizionata', 'Sistema di climatizzazione', True, 2, 1, icon_mapping['EssenzialiIcon']),
        ('Riscaldamento', 'Sistema di riscaldamento autonomo', True, 3, 1, icon_mapping['EssenzialiIcon']),
        ('TV', 'Televisore Smart', True, 4, 1, icon_mapping['EssenzialiIcon']),
        ('Biancheria da letto', 'Lenzuola, coperte e cuscini puliti', True, 5, 1, icon_mapping['EssenzialiIcon']),
        
        # Cucina e Zona Pranzo
        ('Cucina completa', 'Cucina completamente attrezzata', True, 1, 2, icon_mapping['CucinaIcon']),
        ('Piano cottura', 'Piano cottura a induzione/gas', True, 2, 2, icon_mapping['CucinaIcon']),
        ('Forno', 'Forno elettrico', True, 3, 2, icon_mapping['CucinaIcon']),
        ('Microonde', 'Forno a microonde', False, 4, 2, icon_mapping['CucinaIcon']),
        ('Frigorifero', 'Frigorifero con freezer', True, 5, 2, icon_mapping['CucinaIcon']),
        ('Set pentole e padelle', 'Set completo per cucinare', True, 6, 2, icon_mapping['CucinaIcon']),
        ('Stoviglie complete', 'Piatti, bicchieri e posate', True, 7, 2, icon_mapping['CucinaIcon']),
        ('Set coltelli', 'Set di coltelli da cucina', False, 8, 2, icon_mapping['CucinaIcon']),
        ('Taglieri', 'Taglieri in legno/plastica', False, 9, 2, icon_mapping['CucinaIcon']),
        ('Bollitore elettrico', 'Per tè e bevande calde', False, 10, 2, icon_mapping['CucinaIcon']),
        ('Macchina caffè', 'Macchina per il caffè', False, 11, 2, icon_mapping['CucinaIcon']),
        ('Lavastoviglie', 'Lavastoviglie', False, 12, 2, icon_mapping['CucinaIcon']),
        
        # Bagno
        ('Set asciugamani', 'Set completo di asciugamani', True, 1, 3, icon_mapping['BagnoIcon']),
        ('Doccia', 'Doccia con acqua calda', True, 2, 3, icon_mapping['BagnoIcon']),
        ('Set cortesia', 'Sapone, shampoo, carta igienica', True, 3, 3, icon_mapping['BagnoIcon']),
        ('Asciugacapelli', 'Asciugacapelli professionale', False, 4, 3, icon_mapping['BagnoIcon']),
        ('Bidet', 'Bidet in bagno', False, 5, 3, icon_mapping['BagnoIcon']),
        ('Specchio ingranditore', 'Specchio con ingranditore', False, 6, 3, icon_mapping['BagnoIcon']),
        
        # Camera da letto
        ('Armadio', 'Armadio spazioso', True, 1, 4, icon_mapping['CameraIcon']),
        ('Appendiabiti', 'Set di appendiabiti', True, 2, 4, icon_mapping['CameraIcon']),
        ('Cuscini extra', 'Cuscini aggiuntivi', False, 3, 4, icon_mapping['CameraIcon']),
        ('Coperte extra', 'Coperte aggiuntive', False, 4, 4, icon_mapping['CameraIcon']),
        ('Tende oscuranti', 'Tende per oscurare la stanza', False, 5, 4, icon_mapping['CameraIcon']),
        ('Ventilatore', 'Ventilatore a soffitto/piantana', False, 6, 4, icon_mapping['CameraIcon']),
        
        # Lavanderia e Pulizia
        ('Lavatrice', 'Lavatrice automatica', True, 1, 5, icon_mapping['LavanderiaIcon']),
        ('Asciugatrice', 'Asciugatrice elettrica', False, 2, 5, icon_mapping['LavanderiaIcon']),
        ('Stendino', 'Stendino pieghevole', True, 3, 5, icon_mapping['LavanderiaIcon']),
        ('Ferro da stiro', 'Ferro e asse da stiro', False, 4, 5, icon_mapping['LavanderiaIcon']),
        ('Kit pulizia', 'Scopa, paletta e spugne', True, 5, 5, icon_mapping['LavanderiaIcon']),
        ('Aspirapolvere', 'Aspirapolvere', False, 6, 5, icon_mapping['LavanderiaIcon']),
        
        # Comfort e Intrattenimento
        ('Smart TV', 'TV con servizi streaming', True, 1, 6, icon_mapping['ComfortIcon']),
        ('Netflix', 'Accesso a Netflix', False, 2, 6, icon_mapping['ComfortIcon']),
        ('Amazon Prime', 'Accesso a Prime Video', False, 3, 6, icon_mapping['ComfortIcon']),
        ('Disney+', 'Accesso a Disney+', False, 4, 6, icon_mapping['ComfortIcon']),
        ('Console giochi', 'PlayStation/Xbox', False, 5, 6, icon_mapping['ComfortIcon']),
        ('Giochi da tavolo', 'Set di giochi da tavolo', False, 6, 6, icon_mapping['ComfortIcon']),
        
        # Esterni e Parcheggio
        ('Parcheggio privato', 'Posto auto riservato', True, 1, 7, icon_mapping['EsterniIcon']),
        ('Balcone arredato', 'Balcone con mobili', False, 2, 7, icon_mapping['EsterniIcon']),
        ('Giardino', 'Giardino privato', False, 3, 7, icon_mapping['EsterniIcon']),
        ('BBQ', 'Barbecue per grigliate', False, 4, 7, icon_mapping['EsterniIcon']),
        ('Piscina', 'Piscina privata', False, 5, 7, icon_mapping['EsterniIcon']),
        ('Area relax', 'Area relax esterna', False, 6, 7, icon_mapping['EsterniIcon']),
        
        # Sicurezza
        ('Cassaforte', 'Cassaforte per oggetti di valore', True, 1, 8, icon_mapping['SicurezzaIcon']),
        ('Allarme', 'Sistema di allarme', True, 2, 8, icon_mapping['SicurezzaIcon']),
        ('Telecamere', 'Telecamere di sicurezza esterne', False, 3, 8, icon_mapping['SicurezzaIcon']),
        ('Estintore', 'Estintore di sicurezza', True, 4, 8, icon_mapping['SicurezzaIcon']),
        ('Kit pronto soccorso', 'Kit di primo soccorso', True, 5, 8, icon_mapping['SicurezzaIcon']),
        
        # Servizi Premium
        ('Colazione', 'Colazione inclusa', False, 1, 9, icon_mapping['PremiumIcon']),
        ('Pulizie giornaliere', 'Servizio di pulizia quotidiano', False, 2, 9, icon_mapping['PremiumIcon']),
        ('Concierge', 'Servizio concierge', False, 3, 9, icon_mapping['PremiumIcon']),
        ('Transfer', 'Servizio transfer', False, 4, 9, icon_mapping['PremiumIcon']),
        
        # Servizi per Bambini
        ('Lettino neonato', 'Lettino per neonati', False, 1, 11, icon_mapping['BambiniIcon']),
        ('Seggiolone', 'Seggiolone per bambini', False, 2, 11, icon_mapping['BambiniIcon']),
        ('Fasciatoio', 'Fasciatoio per neonati', False, 3, 11, icon_mapping['BambiniIcon']),
        ('Kit sicurezza bimbi', 'Protezioni per prese e spigoli', False, 4, 11, icon_mapping['BambiniIcon']),
        
        # Pet-Friendly
        ('Ammessi animali', 'Struttura pet-friendly', False, 1, 12, icon_mapping['PetIcon']),
        ('Cuccia', 'Cuccia per animali', False, 2, 12, icon_mapping['PetIcon']),
        ('Ciotole', 'Ciotole per cibo e acqua', False, 3, 12, icon_mapping['PetIcon']),
        ('Area animali', 'Area dedicata agli animali', False, 4, 12, icon_mapping['PetIcon'])
    ]
    
    for amenity in amenities:
        cursor.execute('''
            INSERT OR IGNORE INTO amenities_amenity 
            (name, description, is_popular, "order", category_id, icon_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', amenity)
    
    # Commit delle modifiche e chiusura della connessione
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_amenities()
    print("Setup completato con successo!")