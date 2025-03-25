/**
 * Rhome Gallery - JS per la gestione avanzata della galleria immagini
 */

class RhomeGallery {
    constructor(options = {}) {
        this.mainSelector = options.mainSelector || '#main-gallery';
        this.thumbsSelector = options.thumbsSelector || '#thumbnail-gallery';
        this.roomGallerySelector = options.roomGallerySelector || '.room-gallery';
        this.lightboxEnabled = options.lightboxEnabled !== false;
        this.autoHeight = options.autoHeight || false;
        this.transitionEffect = options.transitionEffect || 'slide';
        this.lazyLoad = options.lazyLoad !== false;
        
        this.mainGallery = null;
        this.thumbnailGallery = null;
        this.roomGalleries = [];
        this.lightbox = null;
        
        this.init();
    }
    
    init() {
        this.initMainGallery();
        this.initRoomGalleries();
        if (this.lightboxEnabled) {
            this.initLightbox();
        }
    }
    
    initMainGallery() {
        const mainEl = document.querySelector(this.mainSelector);
        const thumbsEl = document.querySelector(this.thumbsSelector);
        
        if (!mainEl) return;
        
        // Configurazione galleria principale
        this.mainGallery = new Splide(mainEl, {
            type: this.transitionEffect,
            perPage: 1,
            perMove: 1,
            gap: '1rem',
            pagination: false,
            arrows: true,
            lazyLoad: this.lazyLoad ? 'nearby' : false,
            height: this.autoHeight ? 'auto' : undefined,
            classes: {
                arrow: 'splide__arrow bg-white shadow-md text-gray-800',
                prev: 'splide__arrow--prev',
                next: 'splide__arrow--next',
            }
        });
        
        // Configurazione thumbnails
        if (thumbsEl) {
            this.thumbnailGallery = new Splide(thumbsEl, {
                perPage: 15,
                gap: '0.5rem',
                rewind: true,
                pagination: false,
                isNavigation: true,
                arrows: true,
                classes: {
                    arrow: 'splide__arrow bg-white shadow-sm text-gray-800',
                },
                breakpoints: {
                    1024: {
                        perPage: 4,
                    },
                    768: {
                        perPage: 3,
                    },
                    640: {
                        perPage: 3,
                    },
                },
            });
            
            // Sincronizzazione delle gallerie
            this.mainGallery.sync(this.thumbnailGallery);
            this.thumbnailGallery.mount();
        }
        
        // Mount la galleria principale
        this.mainGallery.mount();
        
        // Aggiunge classe active alla thumbnail attiva
        if (this.thumbnailGallery) {
            this.mainGallery.on('moved', (newIndex) => {
                const thumbnails = document.querySelectorAll(`${this.thumbsSelector} .gallery-thumb`);
                thumbnails.forEach((thumb, i) => {
                    if (i === newIndex) {
                        thumb.classList.add('is-active');
                    } else {
                        thumb.classList.remove('is-active');
                    }
                });
            });
        }
        
        // Trigger per il primo slide
        setTimeout(() => {
            this.mainGallery.go(0);
        }, 100);
    }
    
    initRoomGalleries() {
        // Inizializza le gallerie per ogni stanza
        document.querySelectorAll(this.roomGallerySelector).forEach(gallery => {
            const hasMultipleSlides = gallery.querySelectorAll('.splide__slide').length > 1;
            
            const roomGallery = new Splide(gallery, {
                type: this.transitionEffect,
                perPage: 1,
                perMove: 1,
                gap: '0.5rem',
                pagination: true,
                arrows: hasMultipleSlides,
                lazyLoad: this.lazyLoad ? 'nearby' : false,
                height: this.autoHeight ? 'auto' : undefined,
                classes: {
                    arrow: 'splide__arrow bg-white shadow-sm text-gray-800 scale-75',
                    pagination: 'splide__pagination bottom-2',
                }
            });
            
            roomGallery.mount();
            this.roomGalleries.push(roomGallery);
        });
    }
    
    initLightbox() {
        // Inizializza il lightbox
        this.lightbox = GLightbox({
            touchNavigation: true,
            loop: true,
            autoplayVideos: true,
            preload: false,
            openEffect: 'zoom',
            closeEffect: 'fade',
            cssEffects: {
                fade: { in: 'fadeIn', out: 'fadeOut' },
                zoom: { in: 'zoomIn', out: 'zoomOut' }
            }
        });
        
        // Aggiungi classe attiva quando si apre il lightbox
        this.lightbox.on('open', () => {
            document.body.classList.add('lightbox-open');
        });
        
        // Rimuovi classe attiva quando si chiude il lightbox
        this.lightbox.on('close', () => {
            document.body.classList.remove('lightbox-open');
        });
    }
    
    // Metodi pubblici per controllare la galleria esternamente
    goToSlide(index) {
        if (this.mainGallery) {
            this.mainGallery.go(index);
        }
    }
    
    next() {
        if (this.mainGallery) {
            this.mainGallery.go('+1');
        }
    }
    
    prev() {
        if (this.mainGallery) {
            this.mainGallery.go('-1');
        }
    }
    
    openLightbox(index = 0) {
        if (this.lightbox) {
            this.lightbox.openAt(index);
        }
    }
    
    destroy() {
        if (this.mainGallery) {
            this.mainGallery.destroy();
        }
        if (this.thumbnailGallery) {
            this.thumbnailGallery.destroy();
        }
        this.roomGalleries.forEach(gallery => {
            gallery.destroy();
        });
    }
}

// Inizializzazione al caricamento della pagina
document.addEventListener('DOMContentLoaded', function() {
    // Crea l'istanza della galleria
    window.rhomeGallery = new RhomeGallery({
        // Opzioni personalizzate
        mainSelector: '#main-gallery',
        thumbsSelector: '#thumbnail-gallery',
        roomGallerySelector: '.room-gallery',
        lightboxEnabled: true,
        autoHeight: false,
        transitionEffect: 'fade',
        lazyLoad: true
    });
    
    // Gestione del preloader se necessario
    const preloader = document.getElementById('gallery-preloader');
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add('opacity-0');
            setTimeout(() => {
                preloader.style.display = 'none';
            }, 300);
        }, 800);
    }
    
    // Aggiunge funzionalità di swipe su mobile
    if ('ontouchstart' in window) {
        const gallerySections = document.querySelectorAll('.splide__track');
        gallerySections.forEach(section => {
            let startX;
            let endX;
            
            section.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
            });
            
            section.addEventListener('touchend', (e) => {
                endX = e.changedTouches[0].clientX;
                const diff = startX - endX;
                
                // Rileva la direzione dello swipe
                if (Math.abs(diff) > 50) { // Minima distanza per considerarlo uno swipe
                    if (diff > 0) {
                        // Swipe verso sinistra -> avanti
                        window.rhomeGallery.next();
                    } else {
                        // Swipe verso destra -> indietro
                        window.rhomeGallery.prev();
                    }
                }
            });
        });
    }
});
