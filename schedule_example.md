# Peptide Schedule Format Examples

## Supported Schedule Formats

The bot understands natural language peptide schedules in this format:
```
[Peptide Name] [Dosage] [Frequency] for [Duration]
```

### Examples from User:
- GHK-Cu 1.5mg daily for 5 weeks
- Thymosin 1.2mg twice weekly for 10 weeks
- Epithalon 2mg daily for 3 weeks
- BPC-157 500mcg daily for 7 weeks
- TB-500 2mg weekly for 10 weeks

### Additional Supported Formats:
- Ipamorelin 200mcg daily for 12 weeks
- CJC-1295 2mg weekly for 8 weeks
- FOXO4-DRI 5mg EOD for 4 weeks
- Semax 600mcg daily for 30 days
- Selank 250mcg daily for 2 weeks

### Supported Dosage Units:
- `mg` - milligrams
- `mcg` - micrograms (also accepts `μg`)
- `iu` - international units
- `ml` - milliliters
- `cc` - cubic centimeters

### Supported Frequencies:
- `daily` - every day
- `weekly` - once per week
- `twice weekly` - 2x per week
- `EOD` / `every other day` - every 2 days
- `3x weekly` - 3 times per week

### Supported Duration Units:
- `days` - e.g., "30 days"
- `weeks` - e.g., "6 weeks"
- `months` - e.g., "2 months"

### Notes:
- Peptide names can contain letters, numbers, and hyphens
- Decimal dosages are supported (e.g., 1.5mg, 2.5mg)
- Maximum cycle duration: 365 days
- The bot will send reminders at 8:00 AM UTC on scheduled days

| **Peptide**                            | **Dosage**                                                     | **Frequency**                 | **Cycle Duration**                              | **Rest Period**                 | **Notes**                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------------------- | -------------------------------------------------------------- | ----------------------------- | ----------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **GHK-Cu** (Copper Peptide)            | 1–2 mg per dose                                                | Once daily (e.g. Mon–Fri)     | \~4–6 weeks                                     | \~4–6 weeks off                 | Anti-aging & healing peptide (skin, tissue repair). Often cycled a few times per year. Can be injected subcutaneously; some mix a small amount of BPC-157 in the same syringe to reduce injection-site irritation. Best taken in the morning or post-workout for repair.                                                                                                                                                                                                       |
| **FOXO4-DRI** (Senolytic)              | \~3 mg per injection                                           | Every other day (EOD)         | 1 week (e.g. 3 doses over 6 days)               | ≥ 4–6 months off                | Powerful senolytic aimed at clearing senescent cells (anti-aging). Use very sparingly – short "pulse" cycle only **1–3 times per year**. Typically administered subcutaneously. Ensure ample time between cycles; do **not** stack concurrently with other senolytics. Monitor recovery and biomarkers due to limited human data.                                                                                                                                              |
| **Thymosin α-1** (Tα1)                 | 0.8–1.6 mg per dose                                            | Twice weekly (e.g. Mon & Thu) | \~8–12 weeks                                    | \~8–12 weeks off (or as needed) | Immune-modulating peptide for wellness/anti-aging. Standard dosing is 0.8–1.6 mg SC twice weekly. For healthy individuals it's often cycled for a few months at a time (some clinical uses run up to 6–12 months). Take consistent doses each week; no special timing (can be morning or evening). Allows the immune system to recharge during off periods.                                                                                                                    |
| **Epithalon** (Epithalamin)            | \~2 mg per dose                                                | Once daily (bedtime)          | 2–3 weeks (10–20 days)                          | \~6 months off                  | Longevity peptide for telomere support and anti-aging. A typical course is **1–3 mg daily for 10–20 days**. Often done **biannually** – e.g. two cycles per year about 6 months apart. Inject subcutaneously (or IM); commonly taken at night to align with natural hormonal cycles. No ongoing maintenance needed between cycles.                                                                                                                                             |
| **BPC-157** (Body Protection Compound) | 500 mcg/day (e.g. 250 mcg × 2)                                 | Daily (split AM/PM)           | \~6–8 weeks                                     | \~6–8 weeks off                 | Potent healing peptide for injuries, gut and tissue repair. Often dosed **250 mcg twice daily** (total \~0.5 mg) for 4–8 weeks. Injections can be subcutaneous near injury site for localized effect. **Cycle off for \~8 weeks** before repeating to prevent desensitization. Not typically used continuously long-term. Supports joint/tendon recovery; can be stacked with TB-500 during injury rehab.                                                                      |
| **TB-500** (Thymosin β-4)              | **Loading:** 2 mg twice weekly<br>**Maint.:** 2 mg once weekly | 2 × weekly (then 1 × weekly)  | \~4–6 weeks loading <br>+ 4–6 weeks maintenance | \~2–3 months off                | Injury repair peptide for systemic healing (often paired with BPC-157). A common protocol: **loading phase** of \~4–5 mg per week (e.g. 2 mg twice weekly) for 4–6 weeks, then a **maintenance phase** of \~2 mg weekly for another 4–6 weeks. Inject subcutaneously (can rotate sites). After a full cycle (8–12 weeks), take a break (several months) and repeat if needed for new injuries. Enhances collagen synthesis and tissue repair.                                  |
| **AOD-9604** (GH Frag 176-191)         | 300 mcg per dose                                               | Once daily (AM preferred)     | \~12–16 weeks                                   | \~4 weeks off (then assess)     | Fat-loss specific fragment of HGH. Standard dose \~300 mcg SC daily (some use up to 500 mcg). Best taken in the **morning (empty stomach)** or pre-workout to maximize lipolysis. Commonly run for 3–4 months per cycle. If further fat loss is desired, take \~1 month off then repeat. Does not raise IGF-1 or GH significantly, so low risk of GH side effects. Can be combined with lifestyle changes or other metabolic peptides for synergy.                             |
| **CJC-1295 (no DAC)**                  | 100–200 mcg per dose                                           | 1–2× daily (e.g. AM and HS)   | \~8–12 weeks                                    | \~2–4 weeks off                 | Growth Hormone-Releasing Hormone (GHRH analog) for GH pulse enhancement. Typical use: **100–200 mcg subcutaneously** before bed (and/or morning). Often given **5 days on, 2 off** to prevent tolerance. Cycle for \~2–3 months, then take a few weeks off. **Always administer on an empty stomach** (at least 2 hrs after eating) and avoid food \~30 min after to maximize GH release. Commonly *stacked with Ipamorelin* in the same injection for synergistic GH release. |
| **Ipamorelin** (GHRP)                  | 200–300 mcg per day (e.g. 100 mcg × 2)                         | 2× daily (morning & bedtime)  | \~8–12 weeks                                    | \~2–4 weeks off                 | Growth Hormone Releasing Peptide that pairs with CJC-1295. Common dosing is **200–300 mcg split into two daily injections** (morning and night). Administer on an empty stomach, usually **at bedtime (and optionally upon waking)**. Typically cycled \~3 months on, then a short break. Best used **in combination with CJC-1295 (no DAC)** for enhanced GH pulse synergy. Promotes muscle recovery, fat loss, and deep sleep.                                               |
