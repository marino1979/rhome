import React from 'react';
import { createRoot } from 'react-dom/client';
import ListingWizard from './ListingWizard';

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('listing-wizard-root');
    if (container) {
        const root = createRoot(container);
        root.render(<ListingWizard />);
    }
});