# Saved runs

One folder per run: `runs/<set>/<time zone>/<case>--<time zone>/`. All runs were made on 23 October 2026 (UTC
time in `metadata.json`, field `accessed_utc`).

| Set | Runs | What |
|---|---:|---|
| `live-20261023` | 27 | British Columbia, monthly 4,000.00 CAD, 30 June, 1 July and 2 July 2026, in 9 time zones |
| `live-20261023-atlantic` | 36 | Nova Scotia, New Brunswick, Prince Edward Island, Newfoundland and Labrador, in their own zone and in Toronto |
| `live-20261023-boundaries` | 120 | 1 July 2025, the new year 2026, other pay frequencies, Labrador time, the PDF |

Files in a run folder:

- `request.json`: the body the browser sent to `.../calculator/SALARY/calculate`;
- `reply.raw.txt`, `reply.json`: the reply as received, and parsed;
- `result.txt`: the text of the result screen;
- `prefill.json`: the text fields as PDOC filled them in before our entry (TD1 amounts are fields 1 and 3);
- `claim-amounts.json`: the request and reply that fill in the TD1 amounts (set `live-20261023-boundaries`);
- `ui-inputs.json`: the form fields just before "Calculate";
- `metadata.json`: entries of the case, browser, time zone, time, PDOC versions, rate requests and hashes;
- `result.pdf`, `result-pdf.txt`, `getpdf-request.json`: the PDF of "View results in PDF", its text, and the
  request that made it (10 runs);
- `result.png`: screenshot of the result screen (4 runs only).

`metadata.json` lists the scripts and style sheets of the CRA page by address and hash (`resource_records`).
These files themselves, and the saved HTML of the result pages, are not part of this repository.

Note on `live-20261023`: the field `accessed_client_date` in its 27 `metadata.json` files says `2026-10-21`. This
is a fixed value written by the runner used for this set (`tools/browser_runner.py`). The runs were made on
2026-10-23, between 15:24 and 15:39 UTC (field `accessed_utc`). The files were not changed.

`run-log*.txt`, `run-log--*.json` and `console-*.log` are the logs of the drivers.
