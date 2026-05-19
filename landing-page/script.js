// =============================================================
// MindForge Landing Page — Form Handler
// - Captures UTM parameters
// - Validates client-side
// - Generates event_id for Meta Pixel/CAPI deduplication
// - Submits to Make webhook
// - Fires Meta Pixel "Lead" event on success
// =============================================================

(function () {
    'use strict';

    // CONFIG — loaded from config.js (created from config.example.js)
    const CONFIG = window.MINDFORGE_CONFIG || {};
    const WEBHOOK_URL = CONFIG.WEBHOOK_URL;

    if (!WEBHOOK_URL || WEBHOOK_URL.includes('YOUR_WEBHOOK_TOKEN')) {
        console.error('[MindForge] WEBHOOK_URL not configured — copy config.example.js to config.js');
    }

    const form = document.getElementById('leadForm');
    const submitBtn = document.getElementById('submitBtn');
    const formStatus = document.getElementById('formStatus');
    const sourceInput = document.getElementById('source');

    // -------------------------------------------------------------
    // UTM Capture — read on page load, set hidden source field
    // -------------------------------------------------------------
    function captureSource() {
        const params = new URLSearchParams(window.location.search);
        const utmSource = params.get('utm_source');
        const utmMedium = params.get('utm_medium');
        const referrer = document.referrer;

        let source = 'Organic';

        if (utmSource) {
            const sourceMap = {
                'google': 'Google Ads',
                'facebook': 'Facebook',
                'fb': 'Facebook',
                'instagram': 'Instagram',
                'ig': 'Instagram',
                'tiktok': 'TikTok',
                'linkedin': 'LinkedIn',
                'newsletter': 'Newsletter',
                'referral': 'Referral'
            };
            source = sourceMap[utmSource.toLowerCase()] || utmSource;
        } else if (referrer) {
            if (referrer.includes('google.')) source = 'Organic';
            else if (referrer.includes('facebook.')) source = 'Facebook';
            else if (referrer.includes('instagram.')) source = 'Instagram';
            else source = 'Referral';
        }

        sourceInput.value = source;
        return source;
    }

    captureSource();

    // -------------------------------------------------------------
    // Validation
    // -------------------------------------------------------------
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function validateForm(data) {
        const errors = [];
        if (!data.name || data.name.trim().length < 2) errors.push('name');
        if (!data.email || !validateEmail(data.email)) errors.push('email');
        if (!data.interest_program) errors.push('interest_program');
        return errors;
    }

    function clearErrors() {
        form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    }

    function markErrors(fields) {
        fields.forEach(field => {
            const el = form.elements[field];
            if (el) el.classList.add('error');
        });
    }

    // -------------------------------------------------------------
    // Event ID (for Meta Pixel ↔ CAPI deduplication)
    // -------------------------------------------------------------
    function generateEventId() {
        return 'lead_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
    }

    // -------------------------------------------------------------
    // Status display
    // -------------------------------------------------------------
    function showStatus(message, type) {
        formStatus.textContent = message;
        formStatus.className = 'form-status ' + type;
    }

    // -------------------------------------------------------------
    // Submit handler
    // -------------------------------------------------------------
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        clearErrors();

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const errors = validateForm(data);
        if (errors.length) {
            markErrors(errors);
            showStatus('Bitte fülle die markierten Felder korrekt aus.', 'error');
            return;
        }

        const eventId = generateEventId();
        data.event_id = eventId;
        data.timestamp = new Date().toISOString();
        data.user_agent = navigator.userAgent;
        data.page_url = window.location.href;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Wird gesendet...';
        showStatus('', '');

        try {
            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Webhook returned ' + response.status);

            // Fire Meta Pixel Lead event (deduped server-side via event_id)
            if (typeof fbq !== 'undefined') {
                fbq('track', 'Lead', {
                    content_name: data.interest_program,
                    content_category: 'coaching_lead'
                }, { eventID: eventId });
            }

            // Fire dataLayer event for GTM
            if (typeof window.dataLayer !== 'undefined') {
                window.dataLayer.push({
                    event: 'lead_submitted',
                    lead_program: data.interest_program,
                    lead_source: data.source,
                    event_id: eventId
                });
            }

            showStatus('Danke! Wir melden uns innerhalb von 24h.', 'success');
            form.reset();
            sourceInput.value = data.source;
            submitBtn.textContent = 'Gesendet ✓';

        } catch (err) {
            console.error('Submit error:', err);
            showStatus('Etwas ist schiefgelaufen. Bitte versuche es nochmal oder schreib uns direkt.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Gespräch jetzt anfragen';
        }
    });
})();
