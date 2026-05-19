/* submit-engine.js
 * Sendet den Quiz-Submit an den Make-Webhook und feuert die Conversion-
 * DataLayer-Events. Server-Side-Pixel (Meta CAPI, GA4 MP, TikTok Events
 * API) werden NICHT hier gefeuert, sondern im Make-Szenario — sonst
 * würden Access-Tokens im Frontend liegen.
 *
 * Konfiguration:
 *   window.MF_CONFIG = {
 *     webhookUrl: "https://hook.eu2.make.com/<your-hook-id>",
 *     testMode: false
 *   };
 *
 * Wenn keine webhookUrl gesetzt ist, läuft der Submit im Dry-Run und
 * loggt nur in die Console — nützlich für lokale Entwicklung ohne Make.
 */
(function (global) {
  "use strict";

  const DEFAULT_TIMEOUT_MS = 10000;

  function buildPayload(state) {
    const answers = state.answers || {};
    const contact = (answers[10] && answers[10].value) || {};
    const score = (global.MindForgeScore && global.MindForgeScore.totalScore(answers)) || 0;
    const tier = (global.MindForgeScore && global.MindForgeScore.classify(score)) || { tier: "unknown" };

    return {
      meta: {
        event_id: state.event_id,
        started_at: state.started_at,
        submitted_at: new Date().toISOString(),
        source_url: location.href,
        referrer: document.referrer || null,
        user_agent: navigator.userAgent,
      },
      utm: state.utm || {},
      contact: {
        first_name: contact.first_name,
        last_name: contact.last_name,
        email: contact.email,
        phone: contact.phone,
        country: contact.country,
        consent: contact.consent === true,
      },
      quiz: {
        score,
        tier: tier.tier,
        tier_label: tier.label,
        business_status:      answerOf(answers, 1),
        years_self_employed:  answerOf(answers, 2),
        business_field:       answerOf(answers, 3),
        visibility:           answerOf(answers, 4),
        team_setup:           answerOf(answers, 5),
        monthly_revenue:      answerOf(answers, 6),
        main_wish:            answerOf(answers, 7),
        gap:                  answerOf(answers, 8),
        time_budget:          answerOf(answers, 9),
      },
    };
  }

  function answerOf(answers, step) {
    const a = answers[step];
    if (!a) return null;
    return Array.isArray(a.value) ? a.value.join(",") : a.value;
  }

  function timeoutFetch(url, opts, ms) {
    return new Promise((resolve, reject) => {
      const ctrl = new AbortController();
      const t = setTimeout(() => { ctrl.abort(); reject(new Error("Timeout")); }, ms);
      fetch(url, Object.assign({}, opts, { signal: ctrl.signal }))
        .then((r) => { clearTimeout(t); resolve(r); })
        .catch((e) => { clearTimeout(t); reject(e); });
    });
  }

  async function fire(state) {
    const cfg = global.MF_CONFIG || {};
    const payload = buildPayload(state);

    // DataLayer: Lead-Event vor Submit (für client-side Pixel via GTM)
    global.dataLayer = global.dataLayer || [];
    global.dataLayer.push({
      event: "quiz_submit",
      event_id: state.event_id,
      score: payload.quiz.score,
      tier: payload.quiz.tier,
      email_hash: null, // GTM-Variable hashed clientseitig vor Pixel-Tag
      email_plain: payload.contact.email, // ← wird von GTM-Variable gehashed
      value: 0, currency: "EUR",
    });

    if (!cfg.webhookUrl) {
      console.warn("[MindForge] Kein webhookUrl konfiguriert — Dry-Run.", payload);
      return { ok: true, dryRun: true, payload };
    }

    const r = await timeoutFetch(cfg.webhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
      mode: "cors",
      credentials: "omit",
    }, DEFAULT_TIMEOUT_MS);

    if (!r.ok) throw new Error("Webhook " + r.status);
    const data = await r.json().catch(() => ({}));
    return Object.assign({ ok: true, payload }, data);
  }

  global.MindForgeSubmit = { fire, buildPayload };
})(window);
