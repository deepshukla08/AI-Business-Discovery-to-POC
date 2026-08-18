# The answer key

The sample inputs are a **test fixture**, not decoration. Each one has something specific
buried in it. This file is what we grade the agent against — if the brief misses these, the
pipeline isn't working, however fluent the output reads.

Keep this file out of anything the model sees.

---

## 1. A question that was asked and never answered

**Where:** `whatsapp_export_zippo.txt`, 06/03 8:12am and again 11/03 9:41am.
Anjali asks for daily order volume. Ravi answers "depends", twice. Priya says "250, 300 on a
good day" in call 2, and Ravi immediately contradicts her — "300 is Diwali time".

**Expected:** listed as an open question. Any brief that states a daily volume as fact has
invented it. A brief that says "estimates conflict: 250–300 claimed, disputed as festival peak,
never confirmed" is correct.

## 2. A contradiction between two sources

**Where:** `current_process.pdf` §3.1 — "Dispatch planning is completed the previous evening",
circulated by 21:00. Versus `call_2_followup.txt` 00:00:36 — Ravi reaches the hub at 5:45am and
assigns then, because the brand files don't arrive until 8–11pm.

**Expected:** flagged as a conflict between the documented process and observed reality, not
silently resolved in favour of one. The document is stale; nobody in any transcript says so.

Same shape, two more instances in the PDF worth catching:
- §5.1 says proof of delivery is a **signature in a paper register**. Reality is a WhatsApp
  photo to Ravi's personal phone.
- §6.2 says COD reconciliation is **weekly**. Reality is a daily cash handover plus monthly
  Tally work.
- §3.1 and §4.2 reference a **"Dispatch Supervisor"** role. No such person appears anywhere in
  the transcripts — it's Ravi doing all of it.

## 3. A requirement mentioned exactly once

**Where:** `call_1_kickoff.txt` at 00:31:02. Sameer: accounts needs a **daily CSV of completed
deliveries by 8pm**, or invoicing slips and brands hold payment. Priya immediately dismisses it
as "a detail". It is never raised again in any source.

**Expected:** appears in the requirements list. This tests whether the pipeline reads everything
or just amplifies whatever gets repeated most.

## 4. A pain point visible only in the screenshot

**Where:** `screenshot_dispatch_sheet.png`. The sheet has both a `Driver` and a `Driver2`
column, with rows BC-88414 and BC-88416 filled in both. The `Status` column contains
"Delivered", "delivered", "done", "DONE", "delvered", "NA", and blanks — six spellings of two
states. Row BC-88417 has no driver and "no driver free" in remarks.

**Expected:** the double-assignment mechanism and the uncontrolled status vocabulary are cited
**to the screenshot**. If the vision input contributes nothing the brief can't reach otherwise,
it isn't earning its place in the pipeline.

WhatsApp 15/03 8:30pm explains the second column, but the evidence of *how often* it happens is
only in the image.

## 5. The stated want is not the real need

**Where:** Priya asks for customer tracking in `call_1_kickoff.txt` 00:00:31, again at
00:17:58, again in WhatsApp 13/03 (competitor launched it). Meanwhile the actual damage —
night calls, double assignment, lost proof photos, wrong driver payouts, late invoicing, cash
mismatches — all traces back to one thing: **order status exists only in Ravi's head and his
phone.**

**Expected:** the brief separates *what the client asked for* from *what the evidence says they
need*, and notes that customer tracking is nearly free once status is captured, but fixes
nothing on its own. Anjali says this out loud at 00:14:41 of call 2, so it is supported — the
agent should reach it from the evidence, not just quote her.

---

## Other things worth catching

| Finding | Source |
|---|---|
| Prior software failed: English-only, password friction, phone storage | call 1 @17:11, call 2 @13:06 |
| Drivers want no-install (a link, not an app store download) | call 2 @13:39, Firoz |
| Hindi/Marathi over English | call 2 @13:11 |
| Drivers swap orders directly and don't tell Ravi → wrong payouts | WhatsApp 11/03 8:40pm |
| Re-attempts aren't tracked as separate events, so counts are wrong | WhatsApp 20/03 7:50pm |
| Lost proof photos cost ~₹60–70k last quarter | call 1 @07:03 |
| Ravi is a single point of failure, no leave in 2 years | call 2 @02:11 |
| Hometown sends orders as photos and typed WhatsApp messages | call 1 @02:38, call 2 @02:58 |
| Two new brands coming: furniture (large items), pharmacy (compliance unknown) | WhatsApp 08/03 |
| BlueCart API access unknown, account manager on leave | call 2 @16:26, WhatsApp 21/03 |
| Contract late-delivery penalty unknown, Priya never checked | call 2 @17:58, WhatsApp 18/03 |

## Unanswered asks (should all land in "missing information")

1. Daily order volume — asked twice, dodged twice
2. Who assigns when Ravi is away — asked 08/03, never answered
3. Last week's sheet — promised 11/03, never sent
4. Contract penalty clause — promised 18/03, never checked
5. Competitor name — promised 13/03, never sent
6. BlueCart API availability — outstanding
7. Pharmacy brand's compliance requirements — unknown
