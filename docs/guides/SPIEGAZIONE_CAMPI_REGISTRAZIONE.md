# 📋 Spiegazione Campi Form di Registrazione

## Campi del Form di Registrazione

### 1. **Username** (Nome utente)
- **Tipo**: Testo
- **Obbligatorio**: ✅ Sì
- **Lunghezza massima**: 150 caratteri
- **Caratteri permessi**: Lettere, numeri e @/./+/-/_
- **Scopo**: Nome univoco che userai per fare login
- **Esempio**: `mario_rossi`, `mariorossi2024`
- **Validazione**: 
  - Deve essere unico (non può essere già in uso)
  - Controllo case-insensitive (mario_rossi = Mario_Rossi)

### 2. **Nome** (First Name)
- **Tipo**: Testo
- **Obbligatorio**: ✅ Sì
- **Lunghezza massima**: 30 caratteri
- **Scopo**: Il tuo nome di battesimo
- **Esempio**: `Mario`
- **Dove viene usato**: 
  - Nelle email di benvenuto
  - Nel profilo utente
  - Nelle comunicazioni personalizzate

### 3. **Cognome** (Last Name)
- **Tipo**: Testo
- **Obbligatorio**: ✅ Sì
- **Lunghezza massima**: 30 caratteri
- **Scopo**: Il tuo cognome
- **Esempio**: `Rossi`
- **Dove viene usato**: 
  - Insieme al nome per identificarti
  - Nelle comunicazioni formali

### 4. **Email**
- **Tipo**: Email
- **Obbligatorio**: ✅ Sì
- **Lunghezza massima**: 254 caratteri
- **Scopo**: Indirizzo email per comunicazioni e recupero password
- **Esempio**: `mario.rossi@example.com`
- **Validazione**: 
  - Formato email valido (nome@dominio.estensione)
  - Deve essere unico (non può essere già in uso)
  - Case-insensitive (mario@example.com = Mario@Example.com)
  - Viene normalizzato in minuscolo
- **Dove viene usato**: 
  - Per le comunicazioni relative alle prenotazioni
  - Per il recupero password
  - Per le notifiche

### 5. **Numero di telefono** (Phone)
- **Tipo**: Testo
- **Obbligatorio**: ✅ Sì
- **Lunghezza massima**: 20 caratteri
- **Scopo**: Numero di telefono per contatti urgenti
- **Formato consigliato**: `+39 123 456 7890` o `+39-123-456-7890`
- **Validazione**: 
  - Deve contenere almeno 10 cifre
  - Accetta spazi, trattini, parentesi per formattazione
  - Viene salvato così come inserito (non normalizzato)
- **Esempi validi**: 
  - `+39 123 456 7890`
  - `+39-123-456-7890`
  - `0039 123 456 7890`
  - `1234567890`
- **Dove viene usato**: 
  - Per contatti urgenti relativi alle prenotazioni
  - Per comunicazioni importanti
  - Può essere modificato nel profilo dopo la registrazione

### 6. **Password** (Password1)
- **Tipo**: Password (nascosto)
- **Obbligatorio**: ✅ Sì
- **Scopo**: Password per accedere al tuo account
- **Requisiti minimi**:
  - ✅ Almeno 8 caratteri
  - ✅ Non può essere completamente numerica
  - ✅ Non può essere troppo simile allo username
  - ✅ Non può essere una password comune
- **Validazione in tempo reale**: 
  - Il form mostra le regole mentre digiti
  - Le regole diventano verdi quando vengono soddisfatte
- **Sicurezza**: 
  - Viene salvata in forma hash (non in chiaro)
  - Non può essere recuperata, solo resettata

### 7. **Conferma Password** (Password2)
- **Tipo**: Password (nascosto)
- **Obbligatorio**: ✅ Sì
- **Scopo**: Conferma che hai digitato correttamente la password
- **Validazione**: 
  - Deve corrispondere esattamente alla password
  - Validazione in tempo reale: mostra se corrisponde o meno
- **Perché serve**: 
  - Evita errori di digitazione
  - Assicura che la password sia quella desiderata

---

## 🔒 Sicurezza e Privacy

### Come vengono salvati i dati:
- **Password**: Hash (non in chiaro)
- **Email**: In chiaro (necessario per invio email)
- **Telefono**: In chiaro (necessario per chiamate)
- **Username**: In chiaro (necessario per login)

### Validazioni applicate:
1. **Username**: Unicità (non può essere duplicato)
2. **Email**: 
   - Formato valido
   - Unicità (non può essere duplicata)
   - Normalizzazione in minuscolo
3. **Telefono**: 
   - Almeno 10 cifre
   - Formato flessibile
4. **Password**: 
   - Regole di sicurezza Django
   - Validazione in tempo reale nel browser

---

## 📝 Dopo la Registrazione

Dopo aver compilato il form:
1. ✅ L'account viene creato immediatamente
2. ✅ Vieni automaticamente loggato
3. ✅ Vieni reindirizzato alla dashboard
4. ✅ Puoi modificare il profilo (incluso il telefono) in qualsiasi momento

---

## 🔄 Modifica Dati

Puoi modificare questi dati dopo la registrazione:
- ✅ Nome
- ✅ Cognome  
- ✅ Email
- ✅ Numero di telefono
- ❌ Username (non modificabile per sicurezza)
- ❌ Password (deve essere resettata, non modificata)

---

## ❓ Domande Frequenti

**Q: Posso usare lo stesso username di qualcun altro?**
A: No, ogni username deve essere unico.

**Q: Posso usare la stessa email di qualcun altro?**
A: No, ogni email deve essere unica.

**Q: Il numero di telefono è obbligatorio?**
A: Sì, è obbligatorio per contatti urgenti.

**Q: Posso modificare il telefono dopo?**
A: Sì, puoi modificarlo nella pagina del profilo.

**Q: La password è sicura?**
A: Sì, viene salvata in forma hash e non può essere recuperata.

