# The answer key — SmileCraft Dental

Same five traps as the Zippo fixture, in a completely different business. If the pipeline only
works on logistics, it doesn't work.

Keep this file out of anything the model sees.

---

## 1. A question asked and never answered

**Where:** `whatsapp_frontdesk.txt` 11/09 9:15am — Anjali asks how many patients per day.
Kavita: *"Depends on the day"*. Never followed up.
Also `call_1_discovery.txt` @00:03:19 and `call_2_frontdesk.txt` @00:01:29 — the no-show rate,
answered *"depends on the day"* both times, with a guess of "one in five" that nobody measured.
And @00:18:31 Kavita promises the patient count and recall count; it never arrives.

**Expected:** no-show rate and daily volume appear as open questions. A brief that states a
no-show percentage as fact has invented it — "one in five, felt not measured" is the correct
reading.

## 2. Contradictions between the policy and reality

`patient_policy.pdf` is from 2021 and describes a practice that does not exist. Four separate
conflicts, each citable on both sides:

| Policy says | Reality |
|---|---|
| §2.2 double booking "is not permitted under any circumstance" | 09:00 and 10:15 are double-booked in the screenshot; Prakash: *"Paper allows everything sir"* (call 2 @00:06:38) |
| §3.1 confirmed by **automated SMS 48 hours ahead** | Kavita phones on the morning (call 1 @00:02:16); Baner does not confirm at all (call 2 @00:00:41) |
| §4.1 **one patient record across all branches** | Baner is on paper in a cupboard; staff phone each other to read files aloud (call 1 @00:16:58) |
| §5.2 recall list reviewed **weekly** | Last worked through in March (call 2 @00:09:58) |
| §7.2 package balances visible **at every branch** | Kept in a separate paper register per branch (WhatsApp 30/09) |

**Expected:** flagged as conflicts, not silently resolved. Nobody in any transcript says the
policy is out of date.

## 3. A requirement mentioned exactly once

**Where:** `call_1_discovery.txt` @00:14:03. Sunil: insurance **pre-authorisation must be filed
within 24 hours of the consultation** or the claim is rejected outright. Dr. Joshi immediately
dismisses it — *"they're designing a patient app, not an insurance system"*.

Corroborated once, obliquely, in WhatsApp 19/09 — a missed pre-auth worth ₹18,000, in a message
Sunil sent to the wrong group.

**Expected:** appears in requirements. This is the highest-value single sentence in the whole
fixture and the easiest to skim past.

## 4. Evidence only in the screenshot

**Where:** `screenshot_appointment_book.png`.

- **09:00 and 10:15 hold two patients each** — the policy forbids this outright
- **`Conf` is TBC on 11 of 13 rows** — confirmation is theoretically a process and practically isn't
- **Root canal is written four ways in one day**: `RCT`, `Root canal`, `r.c.t sitting 2`, `R.C.T.`
  — so Sunil cannot code claims and Dr. Joshi cannot tell which treatments make money
- **Phone numbers missing on 6 of 11 booked rows** — you cannot confirm a patient you cannot call
- Free-text notes carrying real operational risk: `lab not recd??`, `Baner file?`, `is he coming?`

**Expected:** the vocabulary problem and the double-booking are cited **to the image**. The
missing phone numbers are the sharpest catch — they are invisible in every transcript and they
make the entire "just send reminders" solution partially impossible.

## 5. The stated want is not the real need

Dr. Joshi opens with *"we want an app — patients book online, see their treatment plan, pay"*
(call 1 @00:00:19) and repeats it at @00:32:55 and in WhatsApp 13/09 and 27/09.

The evidence says the money is leaking somewhere else entirely: chairs sitting empty because
nobody confirmed, patients never recalled after treatment, records split across branches so
history is asked rather than known, claims rejected on a 24-hour clock, and one branch that
exists entirely inside one man's head.

Anjali sets it up at @00:32:37 — three people give three different answers and she says they are
the same answer — and deliberately does **not** say what it is.

**Expected:** the goal is about capturing and acting on what already exists, not about a patient
app. Online booking is a consequence of fixing the schedule, not the fix. A brief that leads with
"build a patient mobile app" has been led by the loudest person in the room.

---

## Other things worth catching

| Finding | Source |
|---|---|
| A visiting specialist's schedule lives in a side sheet, so patients get booked for days he isn't coming | call 1 @00:20:37, WhatsApp 17/09 |
| Recall calling **worked** — a week filled from it — and stopped anyway, because it needs a free afternoon | call 2 @00:10:11 |
| A previous WhatsApp reminder tool failed: impersonal, and nobody read the replies | call 1 @00:24:36 |
| Nobody measured no-shows before or after that tool | call 1 @00:25:17 |
| Lab work is tracked on a paper slip in a tray; crowns arrive late once or twice a month | WhatsApp 20/09 |
| Prakash is a single point of failure — 22 years, first leave in 3 years, patients WhatsApp his personal number | call 2 @00:12:36, WhatsApp 26/09 |
| Whatever replaces the diary must be faster than the diary, with a patient standing there | call 2 @00:16:00 |
| Prakash prefers tapping to typing and does not use a Marathi keyboard | call 2 @00:16:28 |
| Migrating Baner means either typing 2,000 paper files or starting patients from blank | call 1 @00:17:19 |
| Package balances tracked in a paper register per branch | WhatsApp 30/09 |

## Unanswered asks (should all land in "missing information")

1. Patients per day — asked, "depends on the day"
2. No-show rate — asked twice, never measured
3. Total patient count and recall count — promised twice, never sent
4. The DentaSoft Excel export / what fields it contains — promised, never sent
5. Whether DentaSoft has an API at all
6. The Bangalore clinic Dr. Joshi wanted to copy — promised, never named
7. What happens to Baner's 2,000 paper files
8. Who covers Baner when Prakash is away — answered "nobody", which is itself the finding
