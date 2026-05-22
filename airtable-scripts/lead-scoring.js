// =============================================================
// MindForge — Lead Scoring Script (LEGACY / MANUAL)
// =============================================================
// Die Produktiv-Scoring-Logik läuft jetzt in der Python Cloud Function
//   gcp/cloud-function-score/main.py
// und wird von Make nach jedem Lead-Create automatisch aufgerufen.
//
// Dieses Script bleibt als manuelles Re-Scoring-Tool in Airtable
// nutzbar — z.B. wenn ein Lead-Status manuell geändert wurde oder
// die Scoring-Formel neu kalibriert werden soll. Die Score-Logik
// ist identisch zur Cloud Function.
// =============================================================
//
// Score 0-100, basierend auf:
//   - Source-Qualität       (max 30)
//   - Programm-Preis        (max 30, linear 0-5000 EUR)
//   - Telefon vorhanden       (15)
//   - Notizen >20 Zeichen     (5)
//   - Recency               (max 20)
// =============================================================

const LEADS_TABLE = 'Leads';
const PROGRAMS_TABLE = 'Programme';

// Gewichtung pro Source — basiert auf typischen Conversion-Rates
const SOURCE_WEIGHTS = {
    'Referral':   30,
    'Organic':    25,
    'Google Ads': 20,
    'Facebook':   15,
    'Instagram':  12,
    'Other':       5,
};

// Bonus für vollständige Kontaktdaten
const PHONE_BONUS = 15;
const NOTES_BONUS = 5;

// =============================================================

const leadsTable = base.getTable(LEADS_TABLE);
const programsTable = base.getTable(PROGRAMS_TABLE);

output.markdown('# Lead Scoring');
output.text('Wähle einen Lead aus, dessen Score berechnet werden soll:');

const lead = await input.recordAsync('Lead auswählen', leadsTable);

if (!lead) {
    output.text('Kein Lead ausgewählt — Abbruch.');
} else {
    const score = await calculateScore(lead);

    output.markdown(`## Ergebnis für: **${lead.getCellValueAsString('Name')}**`);
    output.table([
        { Kriterium: 'Source',     Punkte: score.breakdown.source },
        { Kriterium: 'Programm',   Punkte: score.breakdown.program },
        { Kriterium: 'Telefon',      Punkte: score.breakdown.phone },
        { Kriterium: 'Notizen',      Punkte: score.breakdown.notes },
        { Kriterium: 'Recency',    Punkte: score.breakdown.recency },
        { Kriterium: 'GESAMT',     Punkte: score.total },
    ]);

    const shouldUpdate = await input.buttonsAsync(
        `Score ${score.total} in Airtable speichern?`,
        [
            { label: 'Ja, speichern', value: 'yes', variant: 'primary' },
            { label: 'Nein', value: 'no' },
        ]
    );

    if (shouldUpdate === 'yes') {
        const newStatus = score.total >= 70 ? 'Qualified' : lead.getCellValueAsString('Status') || 'New';

        await leadsTable.updateRecordAsync(lead.id, {
            'Lead Score': score.total,
            'Status':     { name: newStatus },
        });

        output.markdown(`Lead-Score gespeichert. Status: **${newStatus}**`);

        if (score.total >= 70) {
            output.markdown('Hot Lead — Vertrieb sollte kontaktieren.');
        }
    } else {
        output.text('Nicht gespeichert.');
    }
}

// =============================================================
// Score-Berechnung
// =============================================================
async function calculateScore(lead) {
    const breakdown = {
        source:  0,
        program: 0,
        phone:   0,
        notes:   0,
        recency: 0,
    };

    // 1. Source-Gewichtung
    const source = lead.getCellValueAsString('Source');
    breakdown.source = SOURCE_WEIGHTS[source] ?? 0;

    // 2. Programm-Preis (Premium-Programme zeigen höheren Intent)
    const interestLinks = lead.getCellValue('Interesse');
    if (interestLinks && interestLinks.length > 0) {
        const programRecord = await programsTable.selectRecordAsync(interestLinks[0].id);
        if (programRecord) {
            const price = programRecord.getCellValue('Price (EUR)') ?? 0;
            // Lineare Skala: 0 EUR → 0 Punkte, 5000 EUR → 30 Punkte
            breakdown.program = Math.min(30, Math.round(price / 5000 * 30));
        }
    }

    // 3. Telefon vorhanden
    const phone = lead.getCellValueAsString('Telefon');
    if (phone && phone.trim().length > 0) {
        breakdown.phone = PHONE_BONUS;
    }

    // 4. Notizen vorhanden (zeigt Engagement)
    const notes = lead.getCellValueAsString('Notizen');
    if (notes && notes.trim().length > 20) {
        breakdown.notes = NOTES_BONUS;
    }

    // 5. Recency — neuer Lead = mehr Punkte
    const createdValue = lead.getCellValue('Erstellt am');
    if (createdValue) {
        const created = new Date(createdValue);
        const hoursOld = (Date.now() - created.getTime()) / (1000 * 60 * 60);
        if (hoursOld < 24)       breakdown.recency = 20;
        else if (hoursOld < 72)  breakdown.recency = 10;
        else if (hoursOld < 168) breakdown.recency = 5;
    }

    const total = Math.min(100,
        breakdown.source + breakdown.program + breakdown.phone + breakdown.notes + breakdown.recency
    );

    return { total, breakdown };
}
