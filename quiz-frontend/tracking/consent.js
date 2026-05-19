/* consent.js
 * Minimaler DSGVO-tauglicher Cookie-Consent. Setzt Cookies + sendet
 * gtag('consent', 'update', ...) sobald Nutzer entscheidet.
 *
 * Bewusst minimal — kein Drittanbieter (Usercentrics/Cookiebot/etc),
 * damit das Demo portabel bleibt. In Produktion durch CMP ersetzen.
 *
 * Cookie: mf_consent={granted|denied}; Path=/; Max-Age=180 Tage; SameSite=Lax
 */
(function () {
  "use strict";

  const COOKIE = "mf_consent";
  const MAX_AGE = 60 * 60 * 24 * 180; // 180 Tage

  function readCookie(name) {
    return document.cookie.split(";").map((c) => c.trim()).reduce((acc, c) => {
      const i = c.indexOf("=");
      if (i === -1) return acc;
      if (c.slice(0, i) === name) acc = decodeURIComponent(c.slice(i + 1));
      return acc;
    }, null);
  }
  function writeCookie(name, value) {
    document.cookie = name + "=" + encodeURIComponent(value) +
      "; Path=/; Max-Age=" + MAX_AGE + "; SameSite=Lax";
  }

  function updateConsent(granted) {
    if (typeof window.gtag !== "function") return;
    const v = granted ? "granted" : "denied";
    window.gtag("consent", "update", {
      ad_storage: v,
      ad_user_data: v,
      ad_personalization: v,
      analytics_storage: v,
    });
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: "consent_" + v });
  }

  function applyStoredConsent() {
    const stored = readCookie(COOKIE);
    if (stored === "granted") { updateConsent(true);  return true; }
    if (stored === "denied")  { updateConsent(false); return true; }
    return false;
  }

  function renderBanner() {
    const el = document.createElement("div");
    el.className = "mf-consent";
    el.innerHTML = ''
      + '<div class="mf-consent__inner">'
      + '  <p>Wir nutzen Cookies, um die Nutzung dieser Seite zu analysieren und unsere Inhalte zu verbessern. Du kannst jederzeit widerrufen.</p>'
      + '  <div class="mf-consent__actions">'
      + '    <button class="mf-consent__btn mf-consent__btn--ghost" data-consent="denied">Nur notwendige</button>'
      + '    <button class="mf-consent__btn mf-consent__btn--primary" data-consent="granted">Alle akzeptieren</button>'
      + '  </div>'
      + '</div>';

    const style = document.createElement("style");
    style.textContent = ''
      + '.mf-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;'
      + ' background:#142033;border:1px solid #25334e;border-radius:12px;color:#e8edf5;'
      + ' box-shadow:0 12px 32px rgba(0,0,0,.35);max-width:760px;margin:0 auto;}'
      + '.mf-consent__inner{display:flex;flex-direction:column;gap:12px;padding:16px 18px;}'
      + '@media(min-width:720px){.mf-consent__inner{flex-direction:row;align-items:center;}'
      + ' .mf-consent__inner p{flex:1;margin:0;}}'
      + '.mf-consent p{margin:0;font-size:14px;line-height:1.45;color:#cbd6ea;}'
      + '.mf-consent__actions{display:flex;gap:8px;justify-content:flex-end;}'
      + '.mf-consent__btn{cursor:pointer;border-radius:8px;padding:10px 14px;font:600 14px Inter,system-ui,sans-serif;border:1px solid transparent;}'
      + '.mf-consent__btn--primary{background:#b6d3ff;color:#0d1623;}'
      + '.mf-consent__btn--ghost{background:transparent;color:#e8edf5;border-color:#25334e;}';

    document.head.appendChild(style);
    document.body.appendChild(el);

    el.addEventListener("click", (e) => {
      const t = e.target.closest("[data-consent]");
      if (!t) return;
      const v = t.dataset.consent;
      writeCookie(COOKIE, v);
      updateConsent(v === "granted");
      el.remove();
    });
  }

  function init() {
    if (applyStoredConsent()) return;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", renderBanner);
    } else {
      renderBanner();
    }
  }

  init();
})();
