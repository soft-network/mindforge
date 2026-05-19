/* quiz-engine.js
 * State, Navigation und Skip-Logic für das MindForge Quiz.
 *
 * State liegt in sessionStorage unter "mf_quiz_state". Format:
 *   {
 *     step: <int>,
 *     answers: {
 *       "<step>": { value: "<key>"|["k1","k2"], rawScore: <num>, key: "<data-key>" }
 *     },
 *     started_at: <iso>,
 *     utm: { source, medium, campaign, term, content },
 *     event_id: <uuid>
 *   }
 *
 * Tracking-DataLayer-Events:
 *   - quiz_start
 *   - quiz_step_answered (step, key, value)
 *   - quiz_submit_ready (score)
 */
(function () {
  "use strict";

  const STORAGE_KEY = "mf_quiz_state";
  const LAST_STEP_BEFORE_CONTACT = 9;
  const CONTACT_STEP = 10;
  const THANKYOU_STEP = 11;

  /* ---------- DataLayer Helpers ---------- */
  window.dataLayer = window.dataLayer || [];
  function dl(event, payload) {
    window.dataLayer.push(Object.assign({ event }, payload || {}));
  }

  /* ---------- UTM + Event-ID ---------- */
  function uuid() {
    return (crypto.randomUUID && crypto.randomUUID()) ||
      "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
      });
  }
  function captureUtm() {
    const p = new URLSearchParams(location.search);
    const keys = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"];
    const u = {};
    keys.forEach((k) => { const v = p.get(k); if (v) u[k] = v; });
    return u;
  }

  /* ---------- State ---------- */
  function loadState() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* noop */ }
    return null;
  }
  function saveState(s) { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
  function freshState() {
    return {
      step: 0,
      answers: {},
      started_at: new Date().toISOString(),
      utm: captureUtm(),
      event_id: uuid(),
    };
  }
  let state = loadState() || freshState();

  /* ---------- DOM ---------- */
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const $ = (sel, root) => (root || document).querySelector(sel);

  const sections = $$(".step");
  const progressBar = $("#progress-bar");
  const stepLabel = $("#step-label");

  function showStep(n) {
    state.step = n;
    saveState(state);
    sections.forEach((s) => s.classList.toggle("is-active", Number(s.dataset.step) === n));

    const totalContent = LAST_STEP_BEFORE_CONTACT; // 9 inhaltliche Fragen
    if (n === 0) {
      progressBar.style.width = "0%";
      stepLabel.textContent = "Step 0 of " + totalContent;
    } else if (n <= totalContent) {
      progressBar.style.width = ((n / totalContent) * 90) + "%";
      stepLabel.textContent = "Step " + n + " of " + totalContent;
    } else if (n === CONTACT_STEP) {
      progressBar.style.width = "95%";
      stepLabel.textContent = "Kontakt";
    } else {
      progressBar.style.width = "100%";
      stepLabel.textContent = "Fertig";
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---------- Skip-Logic ---------- */
  function nextStep(currentStep, skipTo) {
    // Explizites skip-to vom data-Attribut (z.B. Step 1 "Nein" → Step 3)
    if (typeof skipTo === "number") return skipTo;
    // Sonst linear
    return currentStep + 1;
  }

  /* ---------- Antwort verarbeiten ---------- */
  function answerSingle(section, optBtn) {
    const step = Number(section.dataset.step);
    const key = section.dataset.key;
    const value = optBtn.dataset.value;
    const rawScore = Number(optBtn.dataset.score) || 0;
    const skipTo = optBtn.dataset.skipTo ? Number(optBtn.dataset.skipTo) : undefined;

    state.answers[step] = { value, rawScore, key };
    saveState(state);

    // visuelles Feedback (kurz, dann weiter)
    $$(".opt", section).forEach((o) => o.removeAttribute("aria-pressed"));
    optBtn.setAttribute("aria-pressed", "true");

    dl("quiz_step_answered", { step, key, value, score: rawScore });

    setTimeout(() => showStep(nextStep(step, skipTo)), 220);
  }

  function toggleMulti(section, optBtn) {
    const pressed = optBtn.getAttribute("aria-pressed") === "true";
    optBtn.setAttribute("aria-pressed", pressed ? "false" : "true");
  }

  function commitMulti(section) {
    const step = Number(section.dataset.step);
    const key = section.dataset.key;
    const chosen = $$(".opt[aria-pressed='true']", section);
    if (chosen.length === 0) {
      flashError(section, "Bitte wähle mindestens eine Option.");
      return;
    }
    const values = chosen.map((o) => o.dataset.value);
    const rawScore = chosen.reduce((sum, o) => sum + (Number(o.dataset.score) || 0), 0);
    // Multi-Score auf RAW_MAX=10 deckeln, damit Gewichtung konsistent ist
    const cappedRaw = Math.min(10, rawScore);

    state.answers[step] = { value: values, rawScore: cappedRaw, key };
    saveState(state);

    dl("quiz_step_answered", { step, key, value: values.join(","), score: cappedRaw });
    showStep(nextStep(step));
  }

  function flashError(section, msg) {
    let el = $(".flash", section);
    if (!el) {
      el = document.createElement("p");
      el.className = "flash hint";
      el.style.color = "var(--danger)";
      section.appendChild(el);
    }
    el.textContent = msg;
    setTimeout(() => el && el.remove(), 2500);
  }

  /* ---------- Event-Wiring ---------- */
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-action], .opt");
    if (!t) return;

    if (t.dataset.action === "start") {
      dl("quiz_start", { event_id: state.event_id });
      showStep(1);
      return;
    }

    if (t.classList.contains("opt")) {
      const section = t.closest(".step");
      const type = section.dataset.type;
      if (type === "single") answerSingle(section, t);
      else if (type === "multi") toggleMulti(section, t);
      return;
    }

    if (t.dataset.action === "next-multi") {
      const section = t.closest(".step");
      commitMulti(section);
      return;
    }
  });

  /* ---------- Form Submit ---------- */
  const form = $("#contact-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const contact = {
        first_name: (fd.get("first_name") || "").trim(),
        last_name:  (fd.get("last_name")  || "").trim(),
        email:      (fd.get("email")      || "").trim().toLowerCase(),
        phone:      (fd.get("phone")      || "").trim(),
        country:    (fd.get("country")    || "").trim(),
        consent:    !!fd.get("consent"),
      };
      const err = validateContact(contact);
      if (err) {
        const e1 = $("#form-error");
        e1.textContent = err;
        e1.hidden = false;
        return;
      }
      state.answers[CONTACT_STEP] = { value: contact, rawScore: 0, key: "contact" };
      saveState(state);

      // Submit über submit-engine.js → window.MindForgeSubmit.fire(state)
      if (window.MindForgeSubmit && typeof window.MindForgeSubmit.fire === "function") {
        window.MindForgeSubmit.fire(state)
          .then((res) => {
            const score = (window.MindForgeScore && window.MindForgeScore.totalScore(state.answers)) || 0;
            const finalEl = $("#final-score");
            if (finalEl) finalEl.textContent = String(score);
            dl("quiz_submit_ready", { event_id: state.event_id, score });
            showStep(THANKYOU_STEP);
          })
          .catch((err) => {
            const e2 = $("#form-error");
            e2.textContent = "Übermittlung fehlgeschlagen: " + (err && err.message ? err.message : "unbekannter Fehler") + ". Bitte erneut versuchen.";
            e2.hidden = false;
          });
      } else {
        // Fallback (Engine nicht geladen)
        showStep(THANKYOU_STEP);
      }
    });
  }

  function validateContact(c) {
    if (!c.first_name || c.first_name.length < 2) return "Bitte Vornamen eingeben.";
    if (!c.last_name  || c.last_name.length  < 2) return "Bitte Nachnamen eingeben.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(c.email)) return "Bitte gültige E-Mail-Adresse eingeben.";
    if (!/^[\+0-9\s\-()]{6,}$/.test(c.phone)) return "Bitte gültige Telefonnummer eingeben.";
    if (!c.country) return "Bitte Land auswählen.";
    if (!c.consent) return "Bitte der Datenverarbeitung zustimmen.";
    return null;
  }

  /* ---------- Restart ---------- */
  const restart = $("#restart");
  if (restart) {
    restart.addEventListener("click", (e) => {
      e.preventDefault();
      sessionStorage.removeItem(STORAGE_KEY);
      state = freshState();
      saveState(state);
      showStep(0);
    });
  }

  /* ---------- Init ---------- */
  showStep(state.step || 0);
})();
