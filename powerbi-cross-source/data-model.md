# Data Model & Power Query M

---

## Star Schema

```
                ┌────────────────────────────┐
                │     fact_quiz_leads        │
                │  (Source: HubSpot)         │
                │  ────────────────────────  │
                │  ContactID (PK)            │
                │  Email (Business Key)      │
                │  QuizScore                 │
                │  QuizTier                  │
                │  QuizCompletedAt (FK→date) │
                │  LifecycleStage (FK)       │
                │  Owner                     │
                │  MentorID (FK)             │
                │  ProgramID (FK)            │
                │  LTV                       │
                │  NPS                       │
                └─────────┬──────────────────┘
                          │
       ┌─────────┬────────┼──────────┬──────────────┐
       ▼         ▼        ▼          ▼              ▼
┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐
│dim_date │ │dim_stage │ │dim_    │ │dim_      │ │fact_sessions │
│         │ │          │ │mentor  │ │program   │ │(Airtable)    │
│DateKey  │ │StageKey  │ │MentorID│ │ProgramID │ │SessionID     │
│Year     │ │Name      │ │Name    │ │Name      │ │ContactID(FK) │
│Quarter  │ │Order     │ │City    │ │Price     │ │MentorID(FK)  │
│Month    │ │          │ │Capacity│ │Duration  │ │Date          │
│Week     │ │          │ │        │ │          │ │NPS           │
└─────────┘ └──────────┘ └────────┘ └──────────┘ │Duration      │
                                                  └──────────────┘
```

---

## Power Query M — HubSpot Contacts

```m
let
    Token        = "Bearer " & HubSpotToken,  // aus Parameter
    BaseUrl      = "https://api.hubapi.com/crm/v3/objects/contacts",
    Properties   = Text.Combine({
        "email","firstname","lastname","phone","country",
        "lifecyclestage","hs_lead_status","hubspot_owner_id",
        "quiz_score","quiz_business_field","quiz_monthly_revenue",
        "quiz_main_wish","quiz_time_budget","quiz_completed_at",
        "mentor_id","mentor_name","program","program_start","ltv","nps",
        "createdate","lastmodifieddate"
    }, ","),

    GetPage = (after as nullable text) =>
        let
            params = if after = null
                then [limit="100", properties=Properties]
                else [limit="100", properties=Properties, after=after],
            response = Json.Document(Web.Contents(BaseUrl, [
                Query = params,
                Headers = [Authorization = Token]
            ]))
        in response,

    Aggregate = List.Generate(
        () => [page = GetPage(null), after = null, results = {}],
        each [page] <> null,
        each [
            results = [results] & [page][results],
            after = try [page][paging][next][after] otherwise null,
            page = if after = null then null else GetPage(after)
        ],
        each [results]
    ),
    Flat = List.Combine(Aggregate),
    AsTable = Table.FromList(Flat, Splitter.SplitByNothing(), {"row"}),

    Expanded = Table.ExpandRecordColumn(AsTable, "row",
        {"id","properties","createdAt","updatedAt"},
        {"ContactID","props","CreatedAtRaw","UpdatedAtRaw"}),

    ExpandProps = Table.ExpandRecordColumn(Expanded, "props",
        Text.Split(Properties, ","),
        List.Transform(Text.Split(Properties, ","), each "p_" & _)),

    Typed = Table.TransformColumnTypes(ExpandProps, {
        {"ContactID", type text},
        {"p_email", type text},
        {"p_quiz_score", Int64.Type},
        {"p_quiz_completed_at", type datetime},
        {"p_ltv", type number},
        {"p_nps", Int64.Type},
        {"CreatedAtRaw", type datetime},
        {"UpdatedAtRaw", type datetime}
    }),

    Renamed = Table.RenameColumns(Typed, {
        {"p_email", "Email"},
        {"p_firstname", "FirstName"},
        {"p_lastname", "LastName"},
        {"p_lifecyclestage", "LifecycleStage"},
        {"p_hubspot_owner_id", "Owner"},
        {"p_quiz_score", "QuizScore"},
        {"p_quiz_business_field", "QuizBusinessField"},
        {"p_quiz_monthly_revenue", "QuizMonthlyRevenue"},
        {"p_quiz_completed_at", "QuizCompletedAt"},
        {"p_mentor_id", "MentorID"},
        {"p_program", "ProgramID"},
        {"p_ltv", "LTV"},
        {"p_nps", "NPS"}
    })
in
    Renamed
```

---

## Power Query M — Airtable Sessions

```m
let
    Token        = "Bearer " & AirtableToken,
    BaseId       = AirtableBaseId,
    BaseUrl      = "https://api.airtable.com/v0/" & BaseId & "/Sessions",

    GetPage = (offset as nullable text) =>
        let
            params = if offset = null
                then [pageSize="100"]
                else [pageSize="100", offset=offset],
            response = Json.Document(Web.Contents(BaseUrl, [
                Query = params,
                Headers = [Authorization = Token]
            ]))
        in response,

    Aggregate = List.Generate(
        () => [page = GetPage(null), offset = null, records = {}],
        each [page] <> null,
        each [
            records = [records] & [page][records],
            offset = try [page][offset] otherwise null,
            page = if offset = null then null else GetPage(offset)
        ],
        each [records]
    ),
    Flat = List.Combine(Aggregate),
    AsTable = Table.FromList(Flat, Splitter.SplitByNothing(), {"row"}),

    Expanded = Table.ExpandRecordColumn(AsTable, "row",
        {"id","fields","createdTime"},
        {"SessionID","fields","CreatedAt"}),

    ExpandFields = Table.ExpandRecordColumn(Expanded, "fields",
        {"Contact Email","Mentor","Date","Duration (min)","NPS","Notes"},
        {"Email","MentorID","SessionDate","DurationMin","NPS","Notes"}),

    Typed = Table.TransformColumnTypes(ExpandFields, {
        {"SessionID", type text},
        {"SessionDate", type datetime},
        {"DurationMin", Int64.Type},
        {"NPS", Int64.Type}
    })
in
    Typed
```

---

## dim_date

Klassische Date-Dimension mit M:

```m
let
    Start = #date(2024, 1, 1),
    End   = #date(2027, 12, 31),
    Days  = Duration.Days(End - Start) + 1,
    List  = List.Dates(Start, Days, #duration(1,0,0,0)),
    Table = Table.FromList(List, Splitter.SplitByNothing(), {"Date"}),
    Typed = Table.TransformColumnTypes(Table, {{"Date", type date}}),
    AddCols = Table.AddColumn(
        Table.AddColumn(
            Table.AddColumn(
                Table.AddColumn(
                    Table.AddColumn(Typed, "Year", each Date.Year([Date]), Int64.Type),
                    "Quarter", each "Q" & Number.ToText(Date.QuarterOfYear([Date])), type text),
                "Month", each Date.MonthName([Date]), type text),
            "MonthNum", each Date.Month([Date]), Int64.Type),
        "WeekISO", each Date.WeekOfYear([Date]), Int64.Type)
in
    AddCols
```

---

## Beziehungen (Manage Relationships)

| From | To | Type | Direction | Active |
|---|---|---|---|---|
| `fact_quiz_leads[QuizCompletedAt]` | `dim_date[Date]` | * → 1 | Single | Yes |
| `fact_quiz_leads[MentorID]` | `dim_mentor[MentorID]` | * → 1 | Single | Yes |
| `fact_quiz_leads[ProgramID]` | `dim_program[ProgramID]` | * → 1 | Single | Yes |
| `fact_quiz_leads[LifecycleStage]` | `dim_stage[StageKey]` | * → 1 | Single | Yes |
| `fact_sessions[Email]` | `fact_quiz_leads[Email]` | * → 1 | Single | Yes |
| `fact_sessions[MentorID]` | `dim_mentor[MentorID]` | * → 1 | Single | No (Inactive — Konflikt mit obigem; via USERELATIONSHIP) |
| `fact_sessions[SessionDate]` | `dim_date[Date]` | * → 1 | Single | Yes |

---

## Storage Mode

Phase E: **Import** (alle Tabellen). Refresh manuell.

Bei Skalierung: **DirectQuery** für `fact_sessions` (groß, häufig
geändert), Import für `dim_*`.
