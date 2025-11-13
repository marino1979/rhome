#!/usr/bin/env python
"""
Handler personalizzato per il debug del calendario.
Questo script mostra solo i messaggi di debug del calendario in tempo reale.
"""

import time
import re
import os
from datetime import datetime

def follow_calendar_debug():
    """Segue il file di log del calendario e mostra solo i messaggi di debug."""
    
    log_file = 'calendar_debug.log'
    
    if not os.path.exists(log_file):
        print("File calendar_debug.log non trovato. Avvia prima il server Django.")
        return
    
    print("=" * 80)
    print("🔍 CALENDAR DEBUG MONITOR - Seguendo calendar_debug.log")
    print("=" * 80)
    print("Premi Ctrl+C per uscire")
    print("=" * 80)
    
    # Leggi le ultime righe del file
    with open(log_file, 'r', encoding='utf-8') as f:
        # Vai alla fine del file
        f.seek(0, 2)
        
        try:
            while True:
                line = f.readline()
                if line:
                    # Filtra solo i messaggi di debug del calendario
                    if '[CALENDAR DEBUG]' in line:
                        # Estrai il timestamp
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            timestamp = timestamp_match.group(1)
                        else:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                        
                        # Estrai il messaggio di debug
                        debug_match = re.search(r'\[CALENDAR DEBUG\](.*)', line)
                        if debug_match:
                            message = debug_match.group(1).strip()
                            
                            # Aggiungi colori per diversi tipi di messaggi
                            if '=== ' in message:
                                print(f"\033[1;36m[{timestamp}]\033[0m \033[1;33m{message}\033[0m")
                            elif '[BLOCKED]' in message:
                                print(f"\033[1;36m[{timestamp}]\033[0m \033[1;31m{message}\033[0m")
                            elif '[GAP]' in message:
                                print(f"\033[1;36m[{timestamp}]\033[0m \033[1;35m{message}\033[0m")
                            elif '[RULES]' in message:
                                print(f"\033[1;36m[{timestamp}]\033[0m \033[1;34m{message}\033[0m")
                            elif '[RESULT]' in message:
                                print(f"\033[1;36m[{timestamp}]\033[0m \033[1;32m{message}\033[0m")
                            else:
                                print(f"\033[1;36m[{timestamp}]\033[0m {message}")
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\n🔍 Monitor debug terminato.")

if __name__ == "__main__":
    follow_calendar_debug()
