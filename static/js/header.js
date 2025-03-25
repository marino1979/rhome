// Funzioni per gestire l'header interattivo
document.addEventListener('DOMContentLoaded', function() {
    // Riferimenti agli elementi DOM
    const mainHeader = document.getElementById('mainHeader');
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const mobileMenu = document.getElementById('mobileMenu');
    const languageToggle = document.getElementById('languageToggle');
    const languageDropdown = document.getElementById('languageDropdown');
    
    // Gestione apertura/chiusura del menu mobile
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('show');
        });
        
        // Chiudi il menu mobile quando si clicca fuori
        document.addEventListener('click', function(event) {
            if (!mobileMenuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.remove('show');
            }
        });
    }
    
    // Gestione dropdown lingua
    if (languageToggle && languageDropdown) {
        languageToggle.addEventListener('click', function(event) {
            event.stopPropagation();
            languageDropdown.classList.toggle('show');
        });
        
        // Chiudi il dropdown delle lingue quando si clicca fuori
        document.addEventListener('click', function(event) {
            if (!languageToggle.contains(event.target)) {
                languageDropdown.classList.remove('show');
            }
        });
    }
    
    // Funzione per cambiare lingua
    window.changeLanguage = function(langCode) {
        const select = document.getElementById('languageSelect');
        if (select) {
            select.value = langCode;
            document.getElementById('languageForm').submit();
        }
    };
    
    // Effetto shadow durante lo scroll
    if (mainHeader) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                mainHeader.classList.add('scrolled');
            } else {
                mainHeader.classList.remove('scrolled');
            }
        });
        
        // Verifica lo stato dello scroll all'inizio
        if (window.scrollY > 10) {
            mainHeader.classList.add('scrolled');
        }
    }
});
