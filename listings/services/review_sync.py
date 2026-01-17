"""
Servizio per sincronizzare le recensioni da Airbnb usando pyairbnb.
"""
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import pyairbnb

logger = logging.getLogger(__name__)


class AirbnbReviewSyncError(Exception):
    """Eccezione personalizzata per errori di sincronizzazione"""
    pass


class AirbnbReviewSync:
    """
    Classe per gestire la sincronizzazione delle recensioni da Airbnb.
    """
    
    def __init__(self, listing, airbnb_url=None, language='it', proxy_url=''):
        """
        Inizializza il servizio di sincronizzazione.
        
        Args:
            listing: Oggetto Listing Django
            airbnb_url: URL dell'annuncio Airbnb (opzionale, può essere preso da listing.airbnb_listing_url)
            language: Lingua per le recensioni (default: 'it')
            proxy_url: URL proxy opzionale
        """
        self.listing = listing
        self.airbnb_url = airbnb_url or listing.airbnb_listing_url
        self.language = language
        self.proxy_url = proxy_url
        
        if not self.airbnb_url:
            raise AirbnbReviewSyncError("URL Airbnb non specificato. Inserisci l'URL nell'annuncio o passalo come parametro.")
    
    def sync_reviews(self, min_rating=None, date_from=None, max_reviews=None):
        """
        Sincronizza le recensioni da Airbnb.
        
        Args:
            min_rating: Rating minimo (es. 4.0 per solo 4+ stelle, None per tutte)
            date_from: Data minima per le recensioni (default: ultimo anno)
            max_reviews: Numero massimo di recensioni da sincronizzare (None = tutte)
        
        Returns:
            dict con statistiche della sincronizzazione:
            {
                'synced': numero recensioni sincronizzate,
                'skipped': numero recensioni saltate (duplicati),
                'errors': numero errori,
                'total_found': numero totale recensioni trovate
            }
        """
        if not self.airbnb_url:
            raise AirbnbReviewSyncError("URL Airbnb non specificato")
        
        # Imposta date_from di default (ultimo anno) solo se non specificato
        # NOTA: Se date_from è None, significa che l'utente vuole TUTTE le recensioni
        # Non impostiamo un default qui, lasciamo che sia None se non specificato
        # Il default viene gestito nell'admin view
        
        stats = {
            'synced': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'total_found': 0
        }
        
        try:
            logger.info(f"Inizio sincronizzazione recensioni per listing {self.listing.id} da {self.airbnb_url}")
            
            # Chiama pyairbnb per ottenere le recensioni
            reviews_data = pyairbnb.get_reviews(
                self.airbnb_url,
                self.language,
                self.proxy_url
            )
            
            if not reviews_data:
                logger.warning(f"Nessuna recensione trovata per {self.airbnb_url}")
                return stats
            
            # Parsing dei dati (la struttura può variare, adattare in base alla risposta reale)
            reviews_list = self._parse_reviews_data(reviews_data)
            stats['total_found'] = len(reviews_list)
            
            logger.info(f"Trovate {len(reviews_list)} recensioni da processare")
            
            # Analizza le date delle recensioni per capire il range
            if reviews_list and len(reviews_list) > 0:
                dates_found = []
                for review in reviews_list[:10]:  # Controlla le prime 10
                    review_date = self._extract_review_date(review)
                    if review_date:
                        dates_found.append(review_date)
                
                if dates_found:
                    dates_found.sort()
                    logger.info(f"Range date recensioni trovate: da {dates_found[0]} a {dates_found[-1]}")
                    logger.info(f"NOTA: pyairbnb potrebbe restituire solo le recensioni più recenti (~50-60).")
                    logger.info(f"      Se hai più recensioni su Airbnb, potrebbero non essere tutte disponibili tramite API.")
                
                # Log della prima recensione per debug - VISIBILE
                print(f"\n[ANALISI] Analisi struttura prima recensione:")
                logger.info(f"Esempio prima recensione (tipo): {type(reviews_list[0])}")
                if isinstance(reviews_list[0], dict):
                    first_review = reviews_list[0]
                    all_keys = list(first_review.keys())
                    logger.info(f"Chiavi prima recensione: {all_keys}")
                    print(f"  [CHIAVI] Chiavi disponibili ({len(all_keys)}): {', '.join(all_keys[:20])}")
                    
                    # Cerca specificamente strutture che potrebbero contenere categorie
                    found_rating_structure = False
                    for key in ['ratings', 'category_ratings', 'subratings', 'subtitleItems', 'localizedReview', 'subRatings', 'categoryRatings']:
                        if key in first_review:
                            value = first_review[key]
                            logger.info(f"  {key}: {value}")
                            print(f"  [DATA] {key}: {str(value)[:300]}")
                            found_rating_structure = True
                    
                    if not found_rating_structure:
                        print(f"  [WARN] Nessuna struttura di rating trovata nelle chiavi principali")
                        # Stampa tutte le chiavi per vedere cosa c'è
                        print(f"  [TUTTE] Tutte le chiavi: {', '.join(all_keys)}")
                    
                    # Log alcuni campi chiave
                    print(f"\n  [CAMPI] Campi principali:")
                    for key in ['id', 'createdAt', 'reviewer', 'comments', 'rating']:
                        if key in first_review:
                            value = first_review[key]
                            if isinstance(value, dict):
                                print(f"    {key}: {dict(list(value.items())[:3])}")
                            else:
                                print(f"    {key}: {str(value)[:100]}")
                    
                    # Cerca rating per categoria in tutte le chiavi
                    print(f"\n  [CERCA] Cerca rating per categoria:")
                    category_keywords = ['clean', 'accuracy', 'checkin', 'communication', 'location', 'value']
                    found_category_keys = []
                    for key in all_keys:
                        key_lower = key.lower()
                        for keyword in category_keywords:
                            if keyword in key_lower:
                                value = first_review[key]
                                print(f"    [OK] Trovato '{key}': {value}")
                                found_category_keys.append(key)
                                break
                    
                    # Esplora strutture complesse che potrebbero contenere rating
                    print(f"\n  [ESP] Esplora strutture complesse:")
                    for key in ['reviewee', 'reviewHighlight', 'response', 'reviewMediaItems']:
                        if key in first_review:
                            value = first_review[key]
                            if isinstance(value, dict):
                                print(f"    [DICT] {key} (dict): {list(value.keys())}")
                                # Cerca rating in questa struttura
                                for sub_key in value.keys():
                                    sub_key_lower = sub_key.lower()
                                    if any(kw in sub_key_lower for kw in category_keywords + ['rating', 'score']):
                                        print(f"      [OK] Trovato '{sub_key}' in {key}: {value.get(sub_key)}")
                            elif isinstance(value, list) and len(value) > 0:
                                print(f"    [LIST] {key} (list con {len(value)} elementi)")
                                if isinstance(value[0], dict):
                                    print(f"      Chiavi primo elemento: {list(value[0].keys())}")
                    
                    if not found_category_keys:
                        print(f"    [WARN] Nessuna chiave con rating per categoria trovata nella struttura principale")
                        print(f"    [INFO] pyairbnb potrebbe non fornire i rating per categoria tramite questa API")
                else:
                    logger.info(f"Prima recensione: {str(reviews_list[0])[:500]}")
            
            # Filtra per data e rating
            filtered_reviews = self._filter_reviews(reviews_list, min_rating, date_from)
            
            if max_reviews:
                filtered_reviews = filtered_reviews[:max_reviews]
            
            logger.info(f"Recensioni da sincronizzare dopo filtri: {len(filtered_reviews)}")
            print(f"\n[SYNC] Recensioni da sincronizzare: {len(filtered_reviews)}")
            
            # Analizza se ci sono categorie nelle prime recensioni
            categories_sample = []
            for i, review in enumerate(filtered_reviews[:5]):  # Controlla le prime 5
                if isinstance(review, dict):
                    has_categories = any([
                        self._extract_category_rating(review, 'cleanliness', 'clean'),
                        self._extract_category_rating(review, 'accuracy', 'accurate'),
                        self._extract_category_rating(review, 'checkin', 'check_in'),
                    ])
                    categories_sample.append(has_categories)
            
            if categories_sample:
                categories_found_count = sum(categories_sample)
                logger.info(f"Analisi campione: {categories_found_count}/{len(categories_sample)} recensioni hanno categorie")
                print(f"[STATS] Analisi campione: {categories_found_count}/{len(categories_sample)} recensioni hanno categorie")
            
            # Sincronizza ogni recensione
            categories_saved_count = 0
            with transaction.atomic():
                for idx, review_data in enumerate(filtered_reviews, 1):
                    try:
                        logger.debug(f"Processando recensione {idx+1}/{len(filtered_reviews)}")
                        result = self._sync_single_review(review_data)
                        if result:
                            stats['synced'] += 1
                            # result può essere 'created' o 'updated'
                            if result == 'created':
                                stats['created'] += 1
                                logger.info(f"Recensione {idx+1} creata")
                                # Controlla se ha categorie salvate
                                if isinstance(review_data, dict):
                                    if any([
                                        self._extract_category_rating(review_data, 'cleanliness', 'clean'),
                                        self._extract_category_rating(review_data, 'accuracy', 'accurate'),
                                        self._extract_category_rating(review_data, 'checkin', 'check_in'),
                                        self._extract_category_rating(review_data, 'communication', 'communicate'),
                                        self._extract_category_rating(review_data, 'location', 'loc'),
                                        self._extract_category_rating(review_data, 'value', 'price'),
                                    ]):
                                        categories_saved_count += 1
                            elif result == 'updated':
                                stats['updated'] += 1
                                logger.info(f"Recensione {idx+1} aggiornata")
                        else:
                            stats['skipped'] += 1
                            logger.warning(f"Recensione {idx+1} saltata (dati incompleti o errore)")
                    except Exception as e:
                        logger.error(f"Errore sincronizzazione recensione {idx+1}: {e}", exc_info=True)
                        stats['errors'] += 1
                    
                    # Progress ogni 20 recensioni
                    if idx % 20 == 0:
                        print(f"  [PROGRESS] Processate {idx}/{len(filtered_reviews)} recensioni...")
                
                if categories_saved_count > 0:
                    logger.info(f"Recensioni con categorie salvate: {categories_saved_count}/{stats['synced']}")
                    print(f"[OK] Recensioni con categorie salvate: {categories_saved_count}/{stats['synced']}")
                else:
                    logger.warning(f"WARN: Nessuna recensione con categorie salvata! Potrebbe essere un problema di estrazione dati.")
                    print(f"[WARN] ATTENZIONE: Nessuna recensione con categorie salvata!")
                
                # Sincronizza anche le medie aggregate per categoria
                self.sync_category_averages()
                
                # Aggiorna last_synced sul listing
                self.listing.airbnb_listing_url = self.airbnb_url
                self.listing.airbnb_reviews_last_synced = timezone.now()
                self.listing.save(update_fields=['airbnb_listing_url', 'airbnb_reviews_last_synced'])
            
            logger.info(f"Sincronizzazione completata: {stats['synced']} recensioni sincronizzate, {stats['skipped']} saltate, {stats['errors']} errori")
            # Stampa anche nella console per visibilità
            print(f"\n{'='*60}")
            print(f"SINCRONIZZAZIONE RECENSIONI - LISTING {self.listing.id}")
            print(f"{'='*60}")
            print(f"Totale trovate da pyairbnb: {stats['total_found']}")
            print(f"  NOTA: pyairbnb potrebbe restituire solo le recensioni più recenti (~50-60)")
            print(f"        Se hai più recensioni su Airbnb, potrebbero non essere tutte disponibili")
            print(f"Sincronizzate: {stats['synced']} ({stats.get('created', 0)} create, {stats.get('updated', 0)} aggiornate)")
            print(f"Saltate: {stats['skipped']}")
            print(f"Errori: {stats['errors']}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Errore durante sincronizzazione recensioni: {e}", exc_info=True)
            raise AirbnbReviewSyncError(f"Errore durante sincronizzazione: {str(e)}")
        
        return stats
    
    def _parse_reviews_data(self, reviews_data):
        """
        Parsing dei dati delle recensioni da pyairbnb.
        pyairbnb.get_reviews() restituisce direttamente una lista di recensioni.
        """
        reviews_list = []
        
        # Debug: log della struttura dei dati
        logger.info(f"Tipo dati ricevuti da pyairbnb: {type(reviews_data)}")
        
        if isinstance(reviews_data, list):
            # pyairbnb restituisce direttamente una lista
            reviews_list = reviews_data
            logger.info(f"Ricevuta lista diretta con {len(reviews_list)} elementi")
        elif isinstance(reviews_data, dict):
            logger.info(f"Ricevuto dict con chiavi: {list(reviews_data.keys())}")
            # Se è un dict, cerca liste di recensioni
            reviews_list = reviews_data.get('reviews', []) or reviews_data.get('data', []) or reviews_data.get('reviews_list', [])
            # Se non trova nulla, cerca qualsiasi lista che sembri recensioni
            if not reviews_list:
                for key, value in reviews_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict) and any(k in value[0] for k in ['reviewer', 'author', 'review_text', 'text', 'rating', 'overall_rating', 'comments', 'comment']):
                            reviews_list = value
                            logger.info(f"Trovata lista recensioni in chiave '{key}'")
                            break
        else:
            logger.warning(f"Tipo dati inaspettato: {type(reviews_data)}")
        
        logger.info(f"Parsing completato: {len(reviews_list)} recensioni trovate")
        if reviews_list and len(reviews_list) > 0 and isinstance(reviews_list[0], dict):
            logger.info(f"Esempio struttura recensione (chiavi): {list(reviews_list[0].keys())}")
        
        return reviews_list
    
    def _filter_reviews(self, reviews_list, min_rating=None, date_from=None):
        """
        Filtra le recensioni in base a rating minimo e data.
        """
        filtered = []
        skipped_rating = 0
        skipped_date = 0
        
        for review in reviews_list:
            # Filtra per rating
            if min_rating is not None:
                rating = self._extract_rating(review)
                if rating is None or float(rating) < float(min_rating):
                    skipped_rating += 1
                    continue
            
            # Filtra per data
            if date_from:
                review_date = self._extract_review_date(review)
                if review_date:
                    if review_date < date_from:
                        skipped_date += 1
                        continue
                else:
                    # Se non riesce a estrarre la data, logga per debug
                    logger.debug(f"Impossibile estrarre data da recensione, inclusa comunque")
            
            filtered.append(review)
        
        if skipped_rating > 0:
            logger.info(f"Filtro rating: {skipped_rating} recensioni saltate (rating < {min_rating})")
        if skipped_date > 0:
            logger.info(f"Filtro data: {skipped_date} recensioni saltate (data < {date_from})")
        logger.info(f"Dopo filtri: {len(filtered)} recensioni da sincronizzare (su {len(reviews_list)} totali)")
        
        return filtered
    
    def _extract_rating(self, review_data):
        """Estrae il rating da una recensione"""
        if isinstance(review_data, dict):
            # pyairbnb restituisce 'rating' come numero (es. 5)
            rating = review_data.get('rating') or review_data.get('overall_rating') or review_data.get('stars')
            if rating is not None:
                try:
                    return float(rating)
                except (ValueError, TypeError):
                    pass
        return None
    
    def _extract_review_date(self, review_data):
        """Estrae la data della recensione"""
        if isinstance(review_data, dict):
            # pyairbnb: createdAt in formato ISO (es. "2025-10-31T15:14:41Z")
            date_str = review_data.get('createdAt') or review_data.get('review_date') or review_data.get('created_at') or review_data.get('date')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        # Prova formato ISO prima
                        if 'T' in date_str:
                            try:
                                # Rimuovi 'Z' finale e microsecondi se presenti
                                date_str_clean = date_str.split('.')[0].replace('Z', '')
                                return datetime.strptime(date_str_clean, '%Y-%m-%dT%H:%M:%S').date()
                            except ValueError:
                                pass
                        # Prova altri formati
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y']:
                            try:
                                return datetime.strptime(date_str, fmt).date()
                            except ValueError:
                                continue
                    elif isinstance(date_str, (datetime, date)):
                        return date_str if isinstance(date_str, date) else date_str.date()
                except Exception:
                    pass
        return None
    
    def _sync_single_review(self, review_data):
        """
        Sincronizza una singola recensione nel database.
        Se la recensione esiste già, viene aggiornata invece di essere saltata.
        
        Returns:
            True se la recensione è stata creata o aggiornata, False se non è stato possibile
        """
        from listings.models import Review
        
        # Estrai l'ID univoco della recensione Airbnb
        airbnb_review_id = self._extract_review_id(review_data)
        logger.debug(f"ID estratto da pyairbnb: {airbnb_review_id}")
        
        if not airbnb_review_id:
            # Se non c'è un ID, prova a creare uno basato su altri campi
            # Questo è meno ideale ma può funzionare
            reviewer_name = self._extract_field(review_data, 'reviewer_name', 'author', 'name')
            review_date = self._extract_review_date(review_data)
            review_text = self._extract_field(review_data, 'review_text', 'text', 'comment', 'review')
            
            # Crea un ID più robusto usando nome, data e hash del testo
            if reviewer_name and review_date:
                import hashlib
                text_hash = hashlib.md5((review_text or '').encode('utf-8')).hexdigest()[:8]
                airbnb_review_id = f"{reviewer_name}_{review_date.isoformat()}_{text_hash}"
            else:
                logger.warning("Impossibile creare ID univoco per recensione, saltata")
                return False
        
        # Controlla se la recensione esiste già per questo listing
        existing_review = Review.objects.filter(
            listing=self.listing,
            airbnb_review_id=airbnb_review_id
        ).first()
        
        if existing_review:
            # Aggiorna la recensione esistente invece di saltarla
            logger.debug(f"Recensione {airbnb_review_id} già presente per listing {self.listing.id}, aggiornamento...")
            if self._update_existing_review(existing_review, review_data):
                return 'updated'
            return False
        
        # Estrai tutti i dati necessari
        # pyairbnb struttura: reviewer.firstName, reviewer.pictureUrl, localizedReviewerLocation
        reviewer_obj = review_data.get('reviewer', {}) if isinstance(review_data, dict) else {}
        reviewer_name = reviewer_obj.get('firstName') or reviewer_obj.get('hostName') or reviewer_obj.get('name') or self._extract_field(review_data, 'reviewer_name', 'author', 'name')
        reviewer_location = review_data.get('localizedReviewerLocation') or self._extract_field(review_data, 'reviewer_location', 'location', 'author_location')
        reviewer_avatar_url = reviewer_obj.get('pictureUrl') or reviewer_obj.get('userProfilePicture', {}).get('baseUrl') or self._extract_field(review_data, 'reviewer_avatar_url', 'avatar', 'avatar_url', 'profile_picture')
        
        review_date = self._extract_review_date(review_data)
        stay_date = self._extract_stay_date(review_data)
        
        # pyairbnb: comments o localizedReview.comments
        localized_review = review_data.get('localizedReview') if isinstance(review_data, dict) else None
        if localized_review is None or not isinstance(localized_review, dict):
            localized_review = {}
        review_text = localized_review.get('comments') or review_data.get('comments') or self._extract_field(review_data, 'review_text', 'text', 'comment', 'review')
        
        # Risposta host
        response_obj = review_data.get('response', {}) if isinstance(review_data, dict) else {}
        host_response = response_obj.get('comments') if isinstance(response_obj, dict) else (response_obj if isinstance(response_obj, str) else None) or self._extract_field(review_data, 'host_response', 'response', 'host_comment')
        host_response_date = self._extract_host_response_date(review_data)
        
        # Rating: pyairbnb restituisce 'rating' come numero
        overall_rating = review_data.get('rating') or self._extract_rating(review_data)
        
        # Estrai rating per categoria
        cleanliness_rating = self._extract_category_rating(review_data, 'cleanliness', 'clean')
        accuracy_rating = self._extract_category_rating(review_data, 'accuracy', 'accurate')
        checkin_rating = self._extract_category_rating(review_data, 'checkin', 'check_in')
        communication_rating = self._extract_category_rating(review_data, 'communication', 'communicate')
        location_rating = self._extract_category_rating(review_data, 'location', 'loc')
        value_rating = self._extract_category_rating(review_data, 'value', 'price')
        
        # Log per debug delle categorie - VISIBILE
        if isinstance(review_data, dict):
            categories_found = []
            if cleanliness_rating: categories_found.append(f"cleanliness={cleanliness_rating}")
            if accuracy_rating: categories_found.append(f"accuracy={accuracy_rating}")
            if checkin_rating: categories_found.append(f"checkin={checkin_rating}")
            if communication_rating: categories_found.append(f"communication={communication_rating}")
            if location_rating: categories_found.append(f"location={location_rating}")
            if value_rating: categories_found.append(f"value={value_rating}")
            
            if categories_found:
                logger.info(f"[OK] Rating categorie trovate: {', '.join(categories_found)}")
                print(f"  [OK] Categorie trovate: {', '.join(categories_found)}")
            else:
                logger.warning(f"[WARN] Nessun rating per categoria trovato per questa recensione")
                print(f"  [WARN] Nessun rating per categoria trovato")
                # Log struttura per capire dove sono i rating
                if 'ratings' in review_data or 'category_ratings' in review_data or 'subratings' in review_data:
                    ratings_data = review_data.get('ratings') or review_data.get('category_ratings') or review_data.get('subratings')
                    logger.info(f"Struttura 'ratings' trovata: {ratings_data}")
                    print(f"  [DATA] Struttura 'ratings': {ratings_data}")
                if 'subtitleItems' in review_data:
                    subtitle_items = review_data.get('subtitleItems')
                    logger.info(f"subtitleItems trovati: {subtitle_items}")
                    print(f"  [DATA] subtitleItems: {subtitle_items}")
                if 'localizedReview' in review_data:
                    localized = review_data.get('localizedReview')
                    if localized:
                        logger.info(f"localizedReview trovato: {type(localized)}")
                        print(f"  [DATA] localizedReview (tipo: {type(localized).__name__}): {str(localized)[:500]}")
                        if isinstance(localized, dict):
                            localized_keys = list(localized.keys())
                            logger.info(f"Chiavi in localizedReview: {localized_keys}")
                            print(f"  [CHIAVI] Chiavi in localizedReview: {', '.join(localized_keys)}")
                            if 'subtitleItems' in localized:
                                logger.info(f"localizedReview.subtitleItems: {localized.get('subtitleItems')}")
                                print(f"  [DATA] localizedReview.subtitleItems: {localized.get('subtitleItems')}")
                            # Cerca rating per categoria in localizedReview
                            for key in localized_keys:
                                key_lower = key.lower()
                                if any(kw in key_lower for kw in ['clean', 'accuracy', 'checkin', 'communication', 'location', 'value', 'rating']):
                                    value = localized.get(key)
                                    print(f"  [TROVATO] Trovato '{key}' in localizedReview: {value}")
                # Log tutte le chiavi disponibili per debug
                logger.info(f"Chiavi disponibili in review_data: {list(review_data.keys())}")
                print(f"  [CHIAVI] Chiavi disponibili: {', '.join(list(review_data.keys())[:20])}...")
        
        # Valida i dati obbligatori
        if not reviewer_name or not review_text or not review_date or overall_rating is None:
            # Log dettagliato anche a livello INFO per visibilità
            missing_fields = []
            if not reviewer_name:
                missing_fields.append("reviewer_name")
            if not review_text:
                missing_fields.append("review_text")
            if not review_date:
                missing_fields.append("review_date")
            if overall_rating is None:
                missing_fields.append("overall_rating")
            
            logger.warning(
                f"Recensione {airbnb_review_id} saltata - campi mancanti: {', '.join(missing_fields)}"
            )
            logger.info(
                f"Dettagli recensione saltata - "
                f"reviewer_name={reviewer_name}, review_text={bool(review_text)}, "
                f"review_date={review_date}, overall_rating={overall_rating}"
            )
            # Log della struttura per debug
            if isinstance(review_data, dict):
                logger.info(f"Chiavi disponibili in review_data: {list(review_data.keys())}")
                # Log alcuni valori per capire la struttura
                for key in ['id', 'review_id', 'author', 'reviewer', 'name', 'text', 'review_text', 'comment', 'rating', 'overall_rating', 'stars']:
                    if key in review_data:
                        logger.info(f"  {key} = {str(review_data[key])[:100]}")
            return False
        
        # Crea la recensione
        review = Review.objects.create(
            listing=self.listing,
            reviewer_name=reviewer_name,
            reviewer_location=reviewer_location or '',
            reviewer_avatar_url=reviewer_avatar_url or '',
            review_date=review_date,
            stay_date=stay_date,
            review_text=review_text,
            host_response=host_response or '',
            host_response_date=host_response_date,
            overall_rating=Decimal(str(overall_rating)),
            cleanliness_rating=Decimal(str(cleanliness_rating)) if cleanliness_rating else None,
            accuracy_rating=Decimal(str(accuracy_rating)) if accuracy_rating else None,
            checkin_rating=Decimal(str(checkin_rating)) if checkin_rating else None,
            communication_rating=Decimal(str(communication_rating)) if communication_rating else None,
            location_rating=Decimal(str(location_rating)) if location_rating else None,
            value_rating=Decimal(str(value_rating)) if value_rating else None,
            airbnb_review_id=airbnb_review_id,
            airbnb_listing_url=self.airbnb_url,
            is_verified=True,  # Le recensioni da Airbnb sono verificate
            last_synced=timezone.now()
        )
        
        logger.debug(f"Recensione {airbnb_review_id} creata con successo")
        return 'created'
    
    def _update_existing_review(self, review, review_data):
        """
        Aggiorna una recensione esistente con i nuovi dati.
        
        Args:
            review: Oggetto Review esistente
            review_data: Dati della recensione da pyairbnb
        
        Returns:
            True se aggiornata con successo, False altrimenti
        """
        try:
            # Estrai i dati usando la stessa logica di _sync_single_review
            reviewer_obj = review_data.get('reviewer', {}) if isinstance(review_data, dict) else {}
            reviewer_name = reviewer_obj.get('firstName') or reviewer_obj.get('hostName') or reviewer_obj.get('name') or self._extract_field(review_data, 'reviewer_name', 'author', 'name')
            reviewer_location = review_data.get('localizedReviewerLocation') or self._extract_field(review_data, 'reviewer_location', 'location', 'author_location')
            reviewer_avatar_url = reviewer_obj.get('pictureUrl') or reviewer_obj.get('userProfilePicture', {}).get('baseUrl') or self._extract_field(review_data, 'reviewer_avatar_url', 'avatar', 'avatar_url', 'profile_picture')
            
            review_date = self._extract_review_date(review_data)
            stay_date = self._extract_stay_date(review_data)
            
            localized_review = review_data.get('localizedReview', {}) if isinstance(review_data, dict) else {}
            review_text = localized_review.get('comments') or review_data.get('comments') or self._extract_field(review_data, 'review_text', 'text', 'comment', 'review')
            
            response_obj = review_data.get('response', {}) if isinstance(review_data, dict) else {}
            host_response = response_obj.get('comments') if isinstance(response_obj, dict) else (response_obj if isinstance(response_obj, str) else None) or self._extract_field(review_data, 'host_response', 'response', 'host_comment')
            host_response_date = self._extract_host_response_date(review_data)
            
            overall_rating = review_data.get('rating') or self._extract_rating(review_data)
            
            # Estrai rating per categoria
            cleanliness_rating = self._extract_category_rating(review_data, 'cleanliness', 'clean')
            accuracy_rating = self._extract_category_rating(review_data, 'accuracy', 'accurate')
            checkin_rating = self._extract_category_rating(review_data, 'checkin', 'check_in')
            communication_rating = self._extract_category_rating(review_data, 'communication', 'communicate')
            location_rating = self._extract_category_rating(review_data, 'location', 'loc')
            value_rating = self._extract_category_rating(review_data, 'value', 'price')
            
            # Aggiorna solo se ci sono dati validi
            if reviewer_name:
                review.reviewer_name = reviewer_name
            if reviewer_location:
                review.reviewer_location = reviewer_location
            if reviewer_avatar_url:
                review.reviewer_avatar_url = reviewer_avatar_url
            if review_date:
                review.review_date = review_date
            if stay_date:
                review.stay_date = stay_date
            if review_text:
                review.review_text = review_text
            if host_response:
                review.host_response = host_response
            if host_response_date:
                review.host_response_date = host_response_date
            if overall_rating is not None:
                review.overall_rating = Decimal(str(overall_rating))
            if cleanliness_rating:
                review.cleanliness_rating = Decimal(str(cleanliness_rating))
            if accuracy_rating:
                review.accuracy_rating = Decimal(str(accuracy_rating))
            if checkin_rating:
                review.checkin_rating = Decimal(str(checkin_rating))
            if communication_rating:
                review.communication_rating = Decimal(str(communication_rating))
            if location_rating:
                review.location_rating = Decimal(str(location_rating))
            if value_rating:
                review.value_rating = Decimal(str(value_rating))
            
            # Aggiorna timestamp di sincronizzazione
            review.last_synced = timezone.now()
            review.save()
            
            logger.debug(f"Recensione {review.airbnb_review_id} aggiornata con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante aggiornamento recensione: {e}")
            return False
    
    def _extract_review_id(self, review_data):
        """Estrae l'ID univoco della recensione"""
        if isinstance(review_data, dict):
            # pyairbnb restituisce 'id' direttamente
            return review_data.get('id') or review_data.get('review_id') or review_data.get('airbnb_review_id')
        return None
    
    def _extract_field(self, review_data, *possible_keys):
        """Estrae un campo da review_data provando diverse chiavi possibili"""
        if isinstance(review_data, dict):
            for key in possible_keys:
                value = review_data.get(key)
                if value:
                    # Se è un dict annidato (es. reviewer.firstName), estrai il valore
                    if isinstance(value, dict):
                        # Prova chiavi comuni per oggetti annidati
                        for nested_key in ['firstName', 'name', 'hostName', 'value', 'text']:
                            if nested_key in value:
                                return str(value[nested_key])
                    return str(value)
        return None
    
    def _extract_stay_date(self, review_data):
        """Estrae la data del soggiorno"""
        if isinstance(review_data, dict):
            date_str = review_data.get('stay_date') or review_data.get('checkin_date') or review_data.get('check_in')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y']:
                            try:
                                return datetime.strptime(date_str, fmt).date()
                            except ValueError:
                                continue
                    elif isinstance(date_str, (datetime, date)):
                        return date_str if isinstance(date_str, date) else date_str.date()
                except Exception:
                    pass
        return None
    
    def _extract_host_response_date(self, review_data):
        """Estrae la data della risposta host"""
        if isinstance(review_data, dict):
            # pyairbnb: localizedRespondedDate o response.createdAt
            response_obj = review_data.get('response', {})
            if isinstance(response_obj, dict):
                date_str = response_obj.get('createdAt') or response_obj.get('date')
            else:
                date_str = review_data.get('localizedRespondedDate') or review_data.get('host_response_date') or review_data.get('response_date')
            
            if date_str:
                try:
                    if isinstance(date_str, str):
                        # Prova formato ISO
                        if 'T' in date_str:
                            try:
                                date_str_clean = date_str.split('.')[0].replace('Z', '')
                                return datetime.strptime(date_str_clean, '%Y-%m-%dT%H:%M:%S').date()
                            except ValueError:
                                pass
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y']:
                            try:
                                return datetime.strptime(date_str, fmt).date()
                            except ValueError:
                                continue
                    elif isinstance(date_str, (datetime, date)):
                        return date_str if isinstance(date_str, date) else date_str.date()
                except Exception:
                    pass
        return None
    
    def _extract_category_rating(self, review_data, *possible_keys):
        """Estrae il rating di una categoria specifica"""
        if isinstance(review_data, dict):
            # pyairbnb potrebbe avere i rating in una struttura diversa
            # Prova chiavi dirette prima
            for key in possible_keys:
                value = review_data.get(key)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        continue
            
            # Prova in sottostrutture
            ratings = review_data.get('ratings') or review_data.get('category_ratings') or review_data.get('subratings') or {}
            if isinstance(ratings, dict):
                for key in possible_keys:
                    value = ratings.get(key)
                    if value is not None:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            continue
            
            # Prova in localizedReview (potrebbe contenere i rating per categoria)
            localized_review = review_data.get('localizedReview')
            if localized_review is not None and isinstance(localized_review, dict):
                # Cerca direttamente nelle chiavi di localizedReview
                for key in possible_keys:
                    value = localized_review.get(key)
                    if value is not None:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            continue
                
                # Cerca in sottostrutture di localizedReview
                localized_ratings = localized_review.get('ratings') or localized_review.get('category_ratings') or localized_review.get('subratings') or {}
                if isinstance(localized_ratings, dict):
                    for key in possible_keys:
                        value = localized_ratings.get(key)
                        if value is not None:
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                continue
            
            # Prova anche in subtitleItems (pyairbnb potrebbe usare questo)
            subtitle_items = review_data.get('subtitleItems', [])
            if isinstance(subtitle_items, list):
                for item in subtitle_items:
                    if isinstance(item, dict):
                        item_text = item.get('text', '').lower()
                        item_value = item.get('value')
                        for key in possible_keys:
                            if key.lower() in item_text and item_value:
                                try:
                                    return float(item_value)
                                except (ValueError, TypeError):
                                    continue
            
            # Prova anche in localizedReview.subtitleItems
            localized_review = review_data.get('localizedReview')
            if localized_review is not None and isinstance(localized_review, dict):
                subtitle_items = localized_review.get('subtitleItems', [])
                if isinstance(subtitle_items, list):
                    for item in subtitle_items:
                        if isinstance(item, dict):
                            item_text = item.get('text', '').lower()
                            item_value = item.get('value')
                            for key in possible_keys:
                                if key.lower() in item_text and item_value:
                                    try:
                                        return float(item_value)
                                    except (ValueError, TypeError):
                                        continue
            
            # Prova anche in una struttura con chiavi come 'cleanlinessRating', 'accuracyRating', etc.
            for key in possible_keys:
                # Prova camelCase
                camel_key = key + 'Rating'
                value = review_data.get(camel_key)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
                
                # Prova con underscore
                underscore_key = key + '_rating'
                value = review_data.get(underscore_key)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
            
            # Ricerca più aggressiva: cerca in tutte le chiavi che contengono le parole chiave
            for review_key in review_data.keys():
                review_key_lower = review_key.lower()
                for possible_key in possible_keys:
                    possible_key_lower = possible_key.lower()
                    # Cerca se la chiave contiene la parola chiave e rating/score/star
                    if (possible_key_lower in review_key_lower and 
                        ('rating' in review_key_lower or 'score' in review_key_lower or 'star' in review_key_lower)):
                        value = review_data.get(review_key)
                        if value is not None:
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                continue
        return None
    
    def sync_category_averages(self):
        """
        Sincronizza le medie aggregate per categoria da Airbnb usando get_details().
        Queste medie sono disponibili pubblicamente nell'annuncio, non nelle singole recensioni.
        """
        try:
            logger.info(f"Sincronizzazione medie aggregate per listing {self.listing.id}")
            
            # Ottieni i dettagli dell'annuncio
            details = pyairbnb.get_details(
                self.airbnb_url,
                self.language,
                self.proxy_url
            )
            
            if not details or not isinstance(details, dict):
                logger.warning(f"Nessun dettaglio trovato per {self.airbnb_url}")
                return False
            
            # Estrai i rating per categoria
            ratings = details.get('rating', {})
            if not isinstance(ratings, dict):
                logger.warning(f"Struttura rating non valida: {type(ratings)}")
                return False
            
            # Mappa i campi da pyairbnb al modello Django
            # Nota: pyairbnb usa 'checking' invece di 'checkin'
            category_mapping = {
                'cleanliness': 'cleanliness',
                'accuracy': 'accuracy',
                'checking': 'checkin',  # pyairbnb usa 'checking'
                'communication': 'communication',
                'location': 'location',
                'value': 'value',
            }
            
            updated_fields = []
            for pyairbnb_key, django_field in category_mapping.items():
                value = ratings.get(pyairbnb_key)
                if value is not None:
                    try:
                        # Converti a Decimal e arrotonda a 2 decimali
                        decimal_value = Decimal(str(round(float(value), 2)))
                        
                        # Aggiorna il campo corrispondente
                        field_name = f'airbnb_{django_field}_avg'
                        setattr(self.listing, field_name, decimal_value)
                        updated_fields.append(field_name)
                        
                        logger.info(f"Media {django_field} aggiornata: {decimal_value}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Errore conversione valore {pyairbnb_key}={value}: {e}")
            
            if updated_fields:
                # Salva solo i campi aggiornati
                self.listing.save(update_fields=updated_fields)
                logger.info(f"Medie aggregate sincronizzate: {len(updated_fields)} campi aggiornati")
                print(f"  [OK] Medie aggregate sincronizzate: {len(updated_fields)} categorie")
                return True
            else:
                logger.warning("Nessuna media aggregata trovata nei dettagli")
                return False
                
        except Exception as e:
            logger.error(f"Errore durante sincronizzazione medie aggregate: {e}", exc_info=True)
            print(f"  [ERRORE] Errore sincronizzazione medie aggregate: {e}")
            return False

