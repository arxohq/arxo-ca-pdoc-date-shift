# PDOC uses the previous day's amounts on the first day of a new edition

On the first day of a new edition (1 January or 1 July), the CRA Payroll Deductions Online Calculator (PDOC)
gives the amounts of the previous day when the computer's time zone is east of Eastern time: Atlantic,
Newfoundland and Labrador time. The result screen still shows the selected date. In Halifax time the PDF of the
result is dated one day early, on every date we tried. Eastern and Pacific time give the new amounts. We saw this on 23 October 2026 in 183
automated runs of the public form, with the same entries and only the browser time zone changed.

Arxo · contact: hi@arxo.io

Arxo has no link to the Canada Revenue Agency (CRA). This is not tax or payroll advice. We report what the
public calculator showed on the screen and in the PDF.

## Main result

Salary, monthly pay of 4,000.00 CAD, no year-to-date amounts. The three edition changes we tried, by time zone of
the browser:

| First day of the edition | Amount shown | Halifax (Atlantic) | St. John's (Newfoundland) | UTC (control) | Toronto (Eastern) | Vancouver (Pacific) | Day before, all zones | Day after, all zones |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-07-01, British Columbia, TD1 16,452 / 13,216 | provincial tax | 132.21 | 132.21 | 132.21 | 160.43 | 160.43 | 132.21 | 160.43 |
| 2026-01-01, Ontario, TD1 as PDOC fills it in | federal tax | 314.59 | 314.59 | 314.59 | 310.53 | 310.53 | 314.59 | 310.53 |
| 2025-07-01, Ontario, TD1 as PDOC fills it in | federal tax | 337.06 | 337.06 | 337.06 | 314.59 | 314.59 | 337.06 | 314.59 |

- On the first day, Halifax, St. John's and UTC give the amount of the day before. Toronto and Vancouver give the
  amount of the day after, which is the new edition.
- On the day before and the day after, all time zones give the same result.
- For British Columbia on 1 July 2026 we also ran Winnipeg, Regina and Edmonton (160.43, like Toronto) and
  Moscow time as a second control (132.21, like Halifax). Remittance amount: 1,040.52 in Halifax, 1,068.74 in
  Toronto.
- Of the 51 input sets that we ran in more than one time zone, 37 give the same result in every zone. The 14 that
  differ are all on the first day of an edition.

## Other amounts that change on the first day

Every amount that the new edition changes can be off: federal tax, provincial tax, EI and the TD1 amounts that
PDOC fills in. The error goes both ways.

| Case (monthly unless noted) | Halifax or St. John's | Toronto |
|---|---|---|
| 2026-01-01, Ontario, TD1 as PDOC fills it in | TD1 16,129 / 12,747 (2025 amounts); federal 314.59, Ontario 171.40, EI 65.60 | TD1 16,452 / 12,989; federal 310.53, Ontario 170.40, EI 65.20 |
| 2026-01-01, Ontario, 2026 TD1 typed by hand | federal 310.82, Ontario 170.38, EI 65.60 | federal 310.53, Ontario 170.40, EI 65.20 |
| 2026-01-01, British Columbia, TD1 as PDOC fills it in | provincial 133.39 | provincial 132.21 |
| 2026-07-01, Newfoundland and Labrador, provincial TD1 as PDOC fills it in | St. John's: TD1 11,188; provincial 255.95 | TD1 15,000; provincial 228.31 |
| 2026-07-01, Prince Edward Island, 20,000.00 CAD | Halifax: provincial 3,068.72 (same as on 30 June) | provincial 3,131.11 (new 21% rate above $200,000) |
| 2026-07-01, British Columbia, weekly 923.08 CAD | provincial 30.51 | provincial 37.02 |
| 2026-07-01, British Columbia, bi-weekly 1,846.15 CAD | provincial 61.02 | provincial 74.04 |
| 2026-07-01, British Columbia, semi-monthly 2,000.00 CAD | provincial 66.10 | provincial 80.21 |

- Labrador time (America/Goose_Bay) on 1 July 2026 gives the same as St. John's: TD1 11,188, provincial 255.95.
- Newfoundland and Labrador with 15,000 typed by hand: 228.31 in both zones. Only the value PDOC fills in differs.
- Nova Scotia and New Brunswick did not change on 1 July 2026. On our entries the time zone made no difference
  there.

All 14 input sets that depend on the zone: [data/zone-differences.tsv](data/zone-differences.tsv).

## The PDF is dated one day early

"View results in PDF", British Columbia, monthly 4,000.00 CAD, and Ontario on the new year:

| Screen date | Time zone | Date in the PDF file name | "Date the employee is paid" in the PDF | Provincial tax |
|---|---|---|---|---:|
| 2026-06-30 | Halifax | 2026-06-29 | 2026-06-29 | 132.21 |
| 2026-06-30 | Toronto | 2026-06-30 | 2026-06-30 | 132.21 |
| 2026-07-01 | Halifax | 2026-06-30 | 2026-06-30 | 132.21 |
| 2026-07-01 | Toronto | 2026-07-01 | 2026-07-01 | 160.43 |
| 2026-07-02 | Halifax | 2026-07-01 | 2026-07-01 | 160.43 |
| 2026-07-02 | Toronto | 2026-07-02 | 2026-07-02 | 160.43 |
| 2025-12-31 (Ontario) | Halifax | 2025-12-30 | 2025-12-30 | 171.40 |
| 2025-12-31 (Ontario) | Toronto | 2025-12-31 | 2025-12-31 | 171.40 |
| 2026-01-01 (Ontario) | Halifax | 2025-12-31 | 2025-12-31 | 171.40 |
| 2026-01-01 (Ontario) | Toronto | 2026-01-01 | 2026-01-01 | 170.40 |

In Halifax time the PDF carries the day before the screen date on every date we tried, not only on the first day
of an edition. In Toronto time the dates match. The help page says this date goes into the file name of the saved
result.

## Why we think this is not intended

The CRA pages tie the result to the calendar pay date:

- PDOC page, "What's new": "If you enter a “Date the employee is paid” of July 1, 2026 or later, the changes
  below are effective".
- Help page for salaries: the payment date "will determine the employee's income tax rate, as well as CPP/QPP
  and EI related figures".
- FAQ: "The payroll deductions result is determined by the pay date".
- T4127, 123rd edition, Newfoundland and Labrador: "If Form TD1NL is not filed, TCP is $15,000."

We found no words about a time zone, Eastern time, local time or midnight on the PDOC page, the help pages or the
FAQ (read on 23 October 2026; T4127 read on 21 October 2026; addresses and hashes of our copies in
[data/sources.tsv](data/sources.tsv)).

## What the form sends

The form turns the selected date into midnight in the computer's own time zone and sends it as a UTC time stamp
(`datePaid`). For 1 July 2026:

| Time zone | `datePaid` sent | Result |
|---|---|---|
| Vancouver | 2026-07-01T07:00:00.000Z | new amounts |
| Toronto | 2026-07-01T04:00:00.000Z | new amounts |
| Halifax | 2026-07-01T03:00:00.000Z | previous day |
| St. John's | 2026-07-01T02:30:00.000Z | previous day |
| UTC | 2026-07-01T00:00:00.000Z | previous day |

On 1 January 2026, 04:00Z (Halifax) gives the previous day and 05:00Z (Toronto) the new amounts. This fits a
server that reads the time stamp in Eastern time. This is only our reading: we cannot see the server, and the
real cause may be different. The same page asks the server for the rates of the calendar date
(`calculationRates/SALARY/BRITISH_COLUMBIA/2026-07-01`), also in Halifax. Between time zones the saved requests
differ only in `datePaid` and, where PDOC filled in other TD1 amounts, in `td1ClaimAmountFed` and
`td1ClaimAmountProv`.

## Our own calculation

For the 2026 dates we also calculated the amounts ourselves from T4127, 122nd edition (January 1, 2026) and
123rd edition (July 1, 2026), Option 1, with Python `Decimal` ([tools/model.py](tools/model.py),
[tools/model_atlantic.py](tools/model_atlantic.py), [tools/model_boundaries.py](tools/model_boundaries.py)).
The Toronto and Vancouver replies equal our values on every 2026 date. Two small differences do not depend on the
time zone: Nova Scotia, 4,000.00 CAD, gives 324.11 where we get 324.10; Prince Edward Island, 20,000.00 CAD, gives
3,068.72 on 30 June where the 122nd edition table gives 3,068.38. The 120th and 121st editions (2025) are not on
canada.ca, so for 2025 we only compare the time zones with each other.

## Who is affected

People whose computer is set to Atlantic, Newfoundland or Labrador time and who enter a pay date of 1 January or
1 July. Both days are public holidays, so not many pays have these dates. On those days the amounts above can be
lower (British Columbia and Prince Edward Island on 1 July 2026) or higher (Newfoundland and Labrador with the TD1
amount PDOC fills in on 1 July 2026; most amounts on 1 January 2026 and on 1 July 2025).
Anyone who saves the PDF in Atlantic time gets a file dated one day early, on every date we tried.

## How we ran it

- Public form https://apps.cra-arc.gc.ca/ebci/rhpd/beta/entry/en, type "Salary", no account. PDOC reported
  application version 2026.02 and screen version 2026-06-11.
- Automated Google Chrome 155 (headless), driven by Playwright. A new browser session for every run, locale
  en-CA, the time zone set in the browser (for the page this is the time zone of the computer).
- The script only selects and types values in the normal fields and presses the normal buttons. It never writes
  the date sent to the server; the form builds it.
- 183 runs on 23 October 2026: British Columbia in 9 time zones on 30 June, 1 July and 2 July 2026 (27 runs);
  Nova Scotia, New Brunswick, Prince Edward Island and Newfoundland and Labrador in their own zone and in Toronto
  (36 runs); 1 July 2025, the new year 2026, other pay frequencies, Labrador time and the PDF (120 runs).
- We have not repeated this by hand on an ordinary computer set to Atlantic time.

## What we do not claim

- We do not know what employers actually withheld. We did not check any real payroll.
- We do not know the cause on the server.
- We did not test 1 January 2027 (PDOC offers 2023 to 2026), commission, pension, bonus, retroactive and vacation
  pay, non-zero year-to-date amounts or the French interface.

## How to repeat

Offline, from this folder (Python 3.10 or later, no extra packages, no network):

```
python3 tools/check_saved.py
```

It checks every file against [SHA256SUMS](SHA256SUMS) and the hashes written at capture time, recomputes our
T4127 values, checks that the time zones disagree only on the first day of an edition, checks every figure of this
README against the saved CRA replies and the PDF dates, and rebuilds [data/all-runs.tsv](data/all-runs.tsv) and
[data/zone-differences.tsv](data/zone-differences.tsv) from `runs/`. A PASS means the saved runs and the tables
agree; it is not a new run of PDOC.

Live, against the current public PDOC (six new calculations; network, Playwright and Chrome or Chromium):

```
python3 -m venv .repro-venv
.repro-venv/bin/python -m pip install -r tools/requirements.txt
.repro-venv/bin/python -m playwright install chromium   # or set CHROME_PATH to an installed Chrome
.repro-venv/bin/python tools/live_repeat.py
```

It runs British Columbia on 1 July 2026 (with the PDF), Ontario on 1 January 2026 and Newfoundland and Labrador
on 1 July 2026, each in Atlantic or Newfoundland time and in Toronto time, and writes to `new-runs/`. If CRA has
changed PDOC since 23 October 2026, the results may differ. The full sets can be run again with
`tools/browser_runner.py`, `tools/run_atlantic.py` and `tools/run_boundaries.py`.

## Files

- [data/all-runs.tsv](data/all-runs.tsv): one line per run (183), built from `runs/` by
  [tools/summarize.py](tools/summarize.py).
- [data/zone-differences.tsv](data/zone-differences.tsv): the 14 input sets whose result depends on the zone.
- `data/live-20261023*/`: tables made at the time of the runs (`observations.tsv`, `observations.json`,
  `comparison.json`) for the three sets. Columns such as `edition_applied`, `editions_matching_reply`,
  `matches_expected` and `server_reads_as_eastern` are our reading, not fields of the CRA reply.
- `runs/<set>/<zone>/<case>--<zone>/`: what the browser sent and received. See [runs/README.md](runs/README.md).
- `inputs/`: the entries of every case. `tools/`: the browser runners, the drivers, our T4127 calculation, the
  summary and the checks.

Not included: the scripts and style sheets of the CRA web page (saved during the runs and referenced by hash in
`metadata.json`), the saved HTML of the result pages, and the screenshots except four
(British Columbia on 1 July 2026 and Ontario on 1 January 2026, Halifax and Toronto). The text of every result
screen is in `result.txt`.

## Who was informed

- 2026-10-23: CRA, PDOC team, through the feedback form of the PDOC page.
- 2026-10-23: CRA, payroll deductions formulas (T4127), through the feedback form of the T4127 page (the small form-name error in Chapter 5, Prince Edward Island).
- 2026-10-23: CRA Accessibility Service Feedback, by e-mail (the Schedule 8 e-text differences).
- 2026-10-23: National Payroll Institute, by e-mail.
- CRA service feedback (form RC193) with the full report: to follow.

## Corrections

If you find an error here, or a rule or input that explains these results, write to hi@arxo.io. Corrections will
be listed here.

## History

- 2026-10-23: runs and first version; reports sent (see "Who was informed").

## License

Code and notes: Apache License 2.0 ([LICENSE](LICENSE)). The saved requests, replies, result texts, PDFs and
screenshots come from the public PDOC of the Canada Revenue Agency; they are kept as evidence of what the
calculator returned.
