# Spain eSIOS/aFRR data semantics audit (2026-09-17)

Status: bounded source and raw-response audit. This file records evidence only; it does not change any processed data, production code, or model input.

## 1. Outcome

- The twelve official eSIOS response files listed below were already saved without overwriting an existing file: two July-2025 probes (680/681) and ten full August-2026 indicator responses (630/631/632/633/634/680/681/682/683/2130). This turn only performed read-only verification of those files and their metadata.
- All twelve corresponding `.meta.json` records report HTTP 200. No new authenticated request is claimed in this turn; the current execution environment is subject to a Windows network-permission (`PermissionError`/10013) stop condition, so no alternate channel is used. Credentials are absent from the files and this report.
- The full 2025-01-01—2026-08-31 history was **not** downloaded. No claim of complete historical coverage is made.
- `680/681` MWh semantics are **not evidence-closed**. The API payload says `Energía`, but does not state an SI unit or identify the public series unambiguously with the settlement fields in the balancing guide.

## 2. First-party sources and original locations

All sources below were accessed on 2026-09-17 unless an earlier access date is explicitly stated in the project source register.

| Source | First-party document | URL | Original location used |
|---|---|---|---|
| REE/eSIOS `S-ESIOS-IND-RANGE-2026` | Indicator API date-range documentation | https://api.esios.ree.es/doc/indicator/getting_a_specific_indicator_filtering_values_by_a_date_range.html | Parameter sections 5–16; request sections 19–39; response sections 41–64. Defines date-range requests and returned `datetime`, `datetime_utc`, `magnitud`, `values_updated_at`, and `step_type` fields, but does not define a carry-forward/step-hold rule. |
| REE/eSIOS `S-ESIOS-QH-ADAPT-2022` | Updating of the e.sios public website to the 15-min scheduling project | https://api.esios.ree.es/documents/658/download?locale=en | PDF p.2, Annex I: official indicator names/IDs for 632/633/634 and 682/683. This is an ID/name crosswalk, not proof that 680/681 are settlement fields or that every historical response is complete. |
| REE/eSIOS `S-ESIOS-SRS-GUIDE-2024` | Guía de implantación del Servicio de Regulación Secundaria | https://api.esios.ree.es/documents/2399/download?locale=es | October 2024 guide: pp.4–5 (capacity, MW and €/MW); p.28 (reserve/offer power); pp.50–52 (4-second calculation, 225 cycles per QH, ESECS/ESECB aggregation); pp.46–49 (capacity/energy settlement context). The guide does not provide a public eSIOS-ID-to-field crosswalk for 680/681. |
| CNMC/BOE `S-SP-BOE-2025-RULES` | Resolución de 28 de febrero de 2025, BOE-A-2025-4908 | https://www.boe.es/eli/es/res/2025/02/28/(2) | Annex 2 §1 (IDA schedule and delivery periods). Project source register records publication 2025-03-12 and the intraday quarter-hour production boundary from 2025-03-18. |
| OMIE `S-SP-OMIE-QH-ID-2025` | 15-MTU intraday implementation notice | https://www.omie.es/sites/default/files/2025-03/250318_sco_15mtu_vf-es_0.pdf | PDF pp.1–2: quarter-hour intraday implementation on 2025-03-18, first delivery day 2025-03-19. |
| CNMC/BOE `S-SP-BOE-2026-17570` | 96-round intraday rule amendment | https://www.boe.es/eli/es/res/2026/07/30/(8) | Annex 2 §§5106–5130: current-rule IDA schedule; §§5151–5178: 96/92/100 contract context. This post-2025 amendment is not backfilled into 2025. |

## 3. Raw-response evidence

The response bodies are preserved byte-for-byte by the project eSIOS client. Each row has a companion `.meta.json` containing the safe request URL, parameters, HTTP status, UTC retrieval time, byte count, and SHA-256. Retrieved UTC times are 2026-09-16 17:43:40–17:44:06Z (2026-09-17 in Asia/Shanghai).

### 3.1 Probe around the observed July gap

| Indicator | API name in `indicator.name` | `magnitud` | `step_type` | Returned UTC timestamps | Raw path | SHA-256 |
|---:|---|---|---|---|---|---|
| 680 | Energía activada de regulación secundaria a subir en el sepe | Energía | step | 2025-07-08 07:00, 11:15, 11:30, 16:00 | `data/raw/ES/esios/2026-09-17_probe/probe_680_20250708.json` | `435722f2e82c0cbeebeb7c791c9c49b05686ae1e41859b4a4b0e29776d43a947` |
| 681 | Energía activada de regulación secundaria a bajar en el sepe | Energía | step | 2025-07-08 07:00, 11:15, 11:30, 16:00 | `data/raw/ES/esios/2026-09-17_probe/probe_681_20250708.json` | `dc795ae8ddeeebb04c2e3c506f007c53801006af708d3eff3e1625545dd3f466` |

The probe query was local time `2025-07-08T09:00:00+02:00` through `18:00:00+02:00`, with `time_trunc=fifteen_minutes`. A nine-hour interval has 36 quarter-hour intervals under a half-open convention (37 boundary timestamps if both endpoints are counted), while the response contains four explicit records. `step_type=step` is recorded as an API field only; the API documentation does not define its hold/forward-fill semantics. The four returned timestamps therefore do **not** prove a change-point mechanism, constant intervening QH values, or permissible forward filling. No forward fill, interpolation, clipping, or value transformation is performed here.

### 3.2 August-2026 raw batch

All ten requests used local time `2026-08-01T00:00:00+02:00` through `2026-08-31T23:59:59+02:00`, with `time_trunc=fifteen_minutes`. Each returned 2,976 values, spanning `2026-07-31T22:00Z` through `2026-08-31T21:45Z`, which is the expected UTC representation of the requested local August window.

| ID | API `indicator.name` (abbreviated) | `magnitud` | `step_type` | Raw file | SHA-256 |
|---:|---|---|---|---|---|
| 630 | Requerimientos reserva secundaria a subir | Potencia | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_630.json` | `6f2a05c15da1f29e5d8add024cefaf49a34242abef7fde8d8c7aee3ec9ff2698` |
| 631 | Requerimientos reserva secundaria a bajar | Potencia | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_631.json` | `24ace01d6502c1d6ffe5c2cbc552f9f64de55b7dd7ae28da945f4cdcb3786583` |
| 632 | Asignación reserva secundaria a subir | Potencia | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_632.json` | `5ce059b2377a0c7b219a819560e5bd30b1c2ec2bb8c015ec6f20d8301ee71526` |
| 633 | Asignación reserva secundaria a bajar | Potencia | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_633.json` | `bf6536e384d7589552cd4c3a4c8a5c56afa0d762d49bf2b2beed0b17e82ed0ec` |
| 634 | Precio reserva secundaria a bajar | Precio €/MW | linear | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_634.json` | `f4ec34f6e563eb0adf7aa59e5100da2ef1a3c85ab8d999c2beb7cb3b24308ca3` |
| 680 | Energía activada secundaria a subir | Energía | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_680.json` | `f55f442d02c8aac4282aa18452f4ab70695323e2b8e97f72b4d87ce3b0171866` |
| 681 | Energía activada secundaria a bajar | Energía | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_681.json` | `4912bd5f20e32cea2f5777eb4fb5b1325e10a6eb47d7d4d056f84b407cdf813d` |
| 682 | Precio energía secundaria a subir | Precio €/MWh | linear | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_682.json` | `f45d6b18a95d1dee860288ff4e39286663435b7a16ec169b40c23abe13d20a1d` |
| 683 | Precio energía secundaria a bajar | Precio €/MWh | linear | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_683.json` | `b2db16d52201b046cc14b51ee8b0581cb2ce3afdd1cc4876ce57746f23a85cb4` |
| 2130 | Precio reserva secundaria a subir | Precio €/MW | step | `data/raw/ES/esios/2026-08/20260917T000000Z_history_probe/fetch_2130.json` | `163b4a7448f21e2da9d8433697c582f6c436eb9b7aa66eb88504488a5a179460` |

## 4. Semantics: confirmed facts versus interpretation

### 4.1 Confirmed from official payloads and rules

1. 680 and 681 are directional public eSIOS indicators whose names identify activated secondary-regulation energy, respectively up and down. Their payload `magnitud` is the literal label `Energía`, their requested time resolution is 15 minutes, and the tested response has `step_type=step`.
2. 632 and 633 are directional secondary-regulation reserve allocation indicators. Their payload label is `Potencia`, their geography is `Península`, and their values are on the same QH API route as the activation candidates. The SRS guide describes reserve/offer quantities as power in MW and separates up/down capacity; the API payload itself does not add a more precise SI-unit field.
3. 634 and 2130 are reserve-capacity price indicators (`Precio €/MW`), not capacity quantities. 682 and 683 are energy-price indicators (`Precio €/MWh`), not activated-energy quantities.
4. The SRS guide calculates aFRR accepted power/energy on 4-second control cycles and aggregates 225 cycles per quarter-hour. This establishes the rule-layer dimensional pathway from MW over seconds to an energy quantity, but it does not prove that public 680/681 are exactly the guide's ESECS/ESECB fields, nor does it state the public API base unit beyond `Energía`.

### 4.2 Conditional research interpretation (not a production rule)

- A ratio such as `680 / (632 × 0.25)` or `681 / (633 × 0.25)` is dimensionally meaningful only if 680/681 are confirmed QH MWh and 632/633 are a constant MW reserve allocation for that QH. It is a system-level descriptive diagnostic, not site activation, dispatch, or a capacity-compliance test.
- The four July probe timestamps show only the records returned by that query. Neither the API documentation nor the probe supplies an official step-hold definition or a preceding anchor proving carry-forward across every missing QH. Therefore the 361 fewer explicit records in the existing 680–683 series remain **step-expansion semantics to be verified**, not a license to fill them.
- The four `681/(633×0.25)>1` observations should be retained. The SRS guide's five-minute post-last-activation settlement window and 4-second-to-QH aggregation are candidate explanations for boundary spill, but they do not prove the cause. Public aggregate timing, reserve allocation timing, and revision status may also differ.

### 4.3 Unresolved / prohibited assumptions

- Do not label 680/681 as MWh in a production dataset until REE confirms the public indicator-to-settlement field/unit mapping or an official metadata field closes that gap.
- Do not infer a negative sign for 681 from the word “bajar”. The official guide uses positive/negative Ptarget and accepted-power signs for control logic; the public directional series is nonnegative in the inspected records. Any `+680/-681` signed transformation is a separate modeling convention and is not made here.
- Do not use 632/633 as activated energy, 634/2130 as energy price, or 682/683 as activation volume.
- Do not clip ratio outliers or treat the public peninsular aggregate as an independent storage site's activation.

## 5. IDA3 daily delivery range

For the 2025 quarter-hour intraday regime, the official BOE/CNMC rule source `S-SP-BOE-2025-RULES`, Annex 2 §1, records:

| Session | Gate window (CET) | Result time | Normal-day delivery range |
|---|---:|---:|---|
| IDA1 | 14:00–15:00 | about 15:20 | D+1 periods 1–96 |
| IDA2 | 21:00–22:00 | about 22:20 | D+1 periods 1–96 |
| IDA3 | 09:00–10:00 | about 10:20 | delivery day D periods 49–96, i.e. 48 QH / the latter 12 hours |

On 23-hour/25-hour DST days, the same rule source gives IDA3 ranges 45–92 / 53–100. OMIE's 2025 implementation notice establishes the QH intraday boundary from 2025-03-18 (first delivery 2025-03-19); 2025-01-01—03-17 must not be silently treated as the later QH regime. The 2026 96-round amendment has a separate post-2025 application boundary and is not backfilled into this history.

## 6. Coverage and next boundary

- This audit verifies the already-saved August-2026 raw responses and July-08 probes only. It does not fill January–June 2025 or re-fetch the existing 630/631 missing day.
- Existing project statistics identify 632/633/634/2130 at 38,016 explicit records, 680–683 at 37,655, and 630/631 at 37,920 for the existing July-2025—July-2026 batch. Those counts are explicit API records, not necessarily QH-expanded records; the step semantics and full-history count remain open.
- The project target of 58,364 QH is retained as the accepted UTC/Europe-Madrid DST-aware target from the main-thread arithmetic check. This report does not alter that target or claim that the present explicit-record counts meet it.
- No full-period raw download or processed-file rewrite is claimed in this phase. Any future step expansion must retain raw sparse responses, state the anchor rule, preserve UTC and Europe/Madrid timestamps, and record a separate derived-data hash.
