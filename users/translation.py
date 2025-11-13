"""
Configurazione modeltranslation per escludere i modelli di allauth
Questo evita conflitti quando modeltranslation cerca di modificare i modelli socialaccount
"""
# Non registriamo nessun modello di allauth per la traduzione
# Questo previene l'errore 'super' object has no attribute 'dicts'

# I modelli di allauth sono esclusi dalla traduzione per evitare conflitti

