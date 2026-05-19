# DAX Measures

Alle Measures, gruppiert nach Report. Anlegen in einer eigenen
„Measures"-Table (`__Measures`), damit sie im Field-Panel oben stehen.

---

## Grundlegende Counts

```dax
Total Leads = COUNTROWS(fact_quiz_leads)

Total Sessions = COUNTROWS(fact_sessions)

Total Customers =
CALCULATE(
    COUNTROWS(fact_quiz_leads),
    fact_quiz_leads[LifecycleStage] = "customer"
)
```

---

## Marketing Funnel

```dax
Hot Leads =
CALCULATE(
    [Total Leads],
    fact_quiz_leads[QuizScore] >= 70
)

Warm Leads =
CALCULATE(
    [Total Leads],
    fact_quiz_leads[QuizScore] >= 50 && fact_quiz_leads[QuizScore] < 70
)

Hot Lead Rate =
DIVIDE([Hot Leads], [Total Leads], 0)

MQL Conversion Rate =
DIVIDE(
    CALCULATE([Total Leads], fact_quiz_leads[LifecycleStage] = "marketingqualifiedlead"),
    [Total Leads],
    0
)

SQL Conversion Rate =
DIVIDE(
    CALCULATE([Total Leads], fact_quiz_leads[LifecycleStage] = "salesqualifiedlead"),
    [Total Leads],
    0
)

Lead-to-Customer Rate =
DIVIDE([Total Customers], [Total Leads], 0)
```

---

## Sales Pipeline

```dax
Pipeline Value =
SUMX(
    FILTER(fact_quiz_leads, fact_quiz_leads[LifecycleStage] IN { "salesqualifiedlead", "opportunity" }),
    fact_quiz_leads[LTV]
)

Avg Days to MQL =
AVERAGEX(
    FILTER(fact_quiz_leads, fact_quiz_leads[LifecycleStage] = "marketingqualifiedlead"),
    DATEDIFF(fact_quiz_leads[QuizCompletedAt], fact_quiz_leads[MQLDate], DAY)
)

Won Rate by Owner =
DIVIDE(
    CALCULATE(COUNTROWS(fact_quiz_leads), fact_quiz_leads[LifecycleStage] = "customer"),
    CALCULATE(COUNTROWS(fact_quiz_leads), fact_quiz_leads[LifecycleStage] IN { "salesqualifiedlead", "opportunity", "customer" }),
    0
)
```

---

## Mentor Utilization

```dax
Sessions per Week =
DIVIDE(
    [Total Sessions],
    DISTINCTCOUNT(dim_date[WeekISO])
)

Avg Sessions per Customer =
AVERAGEX(
    VALUES(fact_quiz_leads[Email]),
    CALCULATE([Total Sessions])
)

Avg NPS per Mentor =
AVERAGE(fact_sessions[NPS])

Mentor Utilization Pct =
VAR Capacity = SELECTEDVALUE(dim_mentor[Capacity], 10)
VAR Actual = [Sessions per Week]
RETURN
    DIVIDE(Actual, Capacity, 0)

Top Mentor Sessions =
TOPN(1, VALUES(dim_mentor[Name]), [Total Sessions])
```

---

## Customer Health

```dax
Days Since Last Session =
DATEDIFF(
    MAX(fact_sessions[SessionDate]),
    TODAY(),
    DAY
)

Customer Health Score =
VAR Recency =
    SWITCH(TRUE(),
        [Days Since Last Session] <= 7,  100,
        [Days Since Last Session] <= 14, 75,
        [Days Since Last Session] <= 30, 50,
        [Days Since Last Session] <= 60, 25,
        0
    )
VAR Engagement =
    VAR SessionCount = [Total Sessions]
    RETURN SWITCH(TRUE(),
        SessionCount >= 8, 100,
        SessionCount >= 4, 75,
        SessionCount >= 2, 50,
        SessionCount >= 1, 25,
        0
    )
VAR Nps =
    VAR n = AVERAGE(fact_sessions[NPS])
    RETURN SWITCH(TRUE(),
        n >= 9, 100,
        n >= 7, 75,
        n >= 5, 50,
        n >= 3, 25,
        0
    )
RETURN
    ROUND((Recency * 0.4) + (Engagement * 0.4) + (Nps * 0.2), 0)

Churn Risk =
SWITCH(TRUE(),
    [Customer Health Score] >= 70, "Low",
    [Customer Health Score] >= 40, "Medium",
    "High"
)

LTV per Tier =
DIVIDE(
    SUM(fact_quiz_leads[LTV]),
    DISTINCTCOUNT(fact_quiz_leads[Email]),
    0
)
```

---

## Time Intelligence

```dax
Leads MTD =
CALCULATE(
    [Total Leads],
    DATESMTD(dim_date[Date])
)

Leads YoY % =
VAR Curr = [Total Leads]
VAR Prev = CALCULATE([Total Leads], SAMEPERIODLASTYEAR(dim_date[Date]))
RETURN DIVIDE(Curr - Prev, Prev, 0)

Rolling 4-Week Leads =
CALCULATE(
    [Total Leads],
    DATESINPERIOD(dim_date[Date], MAX(dim_date[Date]), -28, DAY)
)
```

---

## Slicer-Helpers

```dax
Selected Tier =
SELECTEDVALUE(fact_quiz_leads[QuizTier], "All")

Selected Mentor =
SELECTEDVALUE(dim_mentor[Name], "All")
```

---

## Format Strings

Im Modeling-View pro Measure:

| Measure | Format |
|---|---|
| `Hot Lead Rate`, `MQL Conversion Rate`, `Won Rate`, `Mentor Utilization Pct` | `0.00%` |
| `Pipeline Value`, `LTV per Tier` | `€ #,##0` |
| `Customer Health Score` | `0` |
| `Avg Days to MQL`, `Days Since Last Session` | `0 "d"` |
| `Avg NPS per Mentor` | `0.0` |
