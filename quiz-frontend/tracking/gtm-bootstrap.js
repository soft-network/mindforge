/* gtm-bootstrap.js
 * Lädt den Google Tag Manager Container. Vor dem Laden wird auf Einwilligung
 * gewartet (siehe consent.js). Container-ID per Window-Config überschreibbar:
 *
 *   <script>window.MF_GTM_ID = "GTM-ABCDEFG";</script>
 *   <script src="tracking/gtm-bootstrap.js"></script>
 *
 * Default: GTM-XXXXXX (Platzhalter — kein echter Container).
 */
(function () {
  "use strict";

  const ID = window.MF_GTM_ID || "GTM-XXXXXX";

  // DataLayer initialisieren (auch wenn GTM noch nicht geladen ist)
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({
    "gtm.start": Date.now(),
    event: "gtm.js",
    app: "mindforge-quiz",
    version: "1.0.0",
  });

  // Globale Einwilligung-API: setzt Default DENY für alle Marketing-Cookies
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag("consent", "default", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "granted",
    security_storage: "granted",
    wait_for_update: 1500,
  });

  // Container nachladen — wird aber nur dann auch tatsächlich Tags feuern,
  // wenn Einwilligung-Update auf "granted" gesetzt wird (siehe consent.js)
  function loadGTM() {
    if (ID === "GTM-XXXXXX") {
      console.info("[MindForge] GTM-Container-ID nicht gesetzt — Skript-Loader übersprungen.");
      return;
    }
    const s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(ID);
    const first = document.getElementsByTagName("script")[0];
    first.parentNode.insertBefore(s, first);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadGTM);
  } else {
    loadGTM();
  }
})();
