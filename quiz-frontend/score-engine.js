/* score-engine.js
 * Score-Berechnung für das MindForge Quiz.
 *
 * Single-Choice: nimmt den data-score-Wert der gewählten Option.
 * Multi-Choice:  summiert alle ausgewählten Optionen.
 *
 * Max-Score ist auf 100 normalisiert. Reihenfolge der Fragen entspricht
 * data-step im DOM. Skip-Logic: übersprungene Fragen tragen 0 bei.
 */
(function (global) {
  "use strict";

  // Gewichtung pro Frage (Summe = 100)
  // Step-Index → Gewicht in Prozentpunkten
  const WEIGHTS = {
    1:  5,   // business_status (Ja/Nein-Gate)
    2:  10,  // years_self_employed
    3:  10,  // business_field
    4:  10,  // visibility
    5:  10,  // team_setup
    6:  20,  // monthly_revenue  ← stärkster Qualifier
    7:  10,  // main_wish
    8:  10,  // gap (multi)
    9:  15,  // time_budget      ← Commit-Indikator
  };

  // Max-Rohpunkte pro Frage (für Normalisierung)
  const RAW_MAX = {
    1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10,
  };

  function scoreForStep(step, rawValue) {
    const weight = WEIGHTS[step] || 0;
    const max = RAW_MAX[step] || 1;
    return Math.round((rawValue / max) * weight * 100) / 100;
  }

  function totalScore(answers) {
    let sum = 0;
    Object.entries(answers).forEach(([step, a]) => {
      const stepNum = Number(step);
      if (!(stepNum in WEIGHTS)) return;
      sum += scoreForStep(stepNum, a.rawScore || 0);
    });
    return Math.min(100, Math.round(sum));
  }

  function classify(score) {
    if (score >= 70) return { tier: "hot",   label: "Hot Lead — sofort durch Setter anrufen" };
    if (score >= 50) return { tier: "warm",  label: "Warm Lead — innerhalb 24h kontaktieren" };
    if (score >= 30) return { tier: "cold",  label: "Cold Lead — Nurture-Sequenz" };
    return                  { tier: "unqualified", label: "Nicht qualifiziert — Drip-E-Mail" };
  }

  global.MindForgeScore = { scoreForStep, totalScore, classify, WEIGHTS, RAW_MAX };
})(window);
