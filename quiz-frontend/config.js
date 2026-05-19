/* config.js — public runtime config (committed to git)
 *
 * Enthält nur PUBLIC IDs — keine Secrets:
 *  - Make-Webhook-URL → öffentlich erreichbar, durch Rate-Limits geschützt
 *  - GTM-Container-ID → ist auf jeder Site mit GTM einsehbar
 *
 * Echte Secrets (HubSpot Token, Airtable PAT, API-Keys) liegen ausschließlich
 * im Make-Backend bzw. in .env (lokal, in .gitignore).
 *
 * Für lokale Überschreibungen: kopiere config.local.js.example zu
 * config.local.js (in .gitignore) — wird nicht committed.
 */

// GTM-Container — wird gesetzt sobald Container in GTM angelegt ist
window.MF_GTM_ID = "GTM-XXXXXX";

// Make-Webhook für Quiz-Submit
window.MF_CONFIG = {
  webhookUrl: "https://hook.eu1.make.com/eikeiljl9fbwaoagpn013mjy30vel5wb",
  testMode: false,
};
