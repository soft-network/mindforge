/* config.example.js
 * Kopiere diese Datei nach `config.js` (lokal, nicht in Git) und passe
 * die Werte an. Wird vor allen anderen Scripts geladen.
 *
 *   cp config.example.js config.js   (Linux/Mac)
 *   copy config.example.js config.js (Windows PowerShell/CMD)
 */

// GTM-Container-ID — aus Google Tag Manager > Admin > Container Settings
window.MF_GTM_ID = "GTM-XXXXXX";

// Make-Webhook-URL — aus Make Scenario, Webhook-Modul
window.MF_CONFIG = {
  webhookUrl: "https://hook.eu2.make.com/REPLACE_ME",
  testMode: true, // bei true: Submit fließt, Make markiert den Payload als Test
};
