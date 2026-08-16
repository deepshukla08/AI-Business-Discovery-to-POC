Build a clickable prototype of the application described below.

A consultant will open this in a client meeting and say "this is what we understood — click
it". The client will click something, and immediately say "but we also need X". That reaction
is the entire point. You are not building software; you are building the thing that provokes
the correction, while corrections are still free.

## Output

**One self-contained HTML file.** Nothing else. No explanation, no markdown fence, no commentary
before or after. Your entire response is the file, starting with `<!DOCTYPE html>`.

## Hard constraints

- **Everything inline.** One `<style>`, one `<script>`, no external files, no `fetch`, no
  imports, no CDN links, no web fonts, no images from the internet. It must work with the
  network cable pulled out.
- **No build step, no framework.** Plain HTML, CSS and vanilla JavaScript.
- **State lives in a JavaScript variable.** No backend, no localStorage. Refreshing resets it,
  and that is fine.
- Use inline SVG or a text character if you need an icon.

## What must actually work

Pick the **one interaction that carries the whole idea** — usually the step that fixes the
worst pain in the brief — and make it genuinely functional. Clicking it must change what is on
screen: something moves, a status updates, a counter changes, a second screen reflects it.

Everything else can be static. One real interaction beats six fake buttons.

**Enforce the rule the redesign depends on.** If the proposal says a thing becomes impossible,
make it impossible here — disable it, hide it, or refuse it with a visible message. A demo that
still permits the exact mistake being fixed argues against itself.

## Screens

Build every screen in the outline as a section of the same page, with plain navigation between
them (buttons or tabs that show and hide). Do not use a router. Label each screen with the role
who opens it, since a client needs to know whose view they are looking at.

## Data

Invent realistic sample rows that match the client's actual world — their real place names,
brands, staff names, order-number formats and currency, taken from the brief. Generic
`Item 1 / Item 2 / Lorem ipsum` makes the demo feel like a template and kills the effect.

Eight to fifteen rows. Enough to look like a working day, few enough to scan.

## Looks

Clean, plain, legible. System font stack, generous spacing, one accent colour, real alignment.
It should look like an internal tool that works — not a polished marketing page, and not a
wireframe. Do not spend effort on animation or gradients.

Mobile-facing screens (a driver's phone) should be laid out narrow, in a phone-shaped frame,
so the client can see which is which.

## The application

{{OUTLINE}}

## The problems it exists to solve

Read these to ground the sample data and to choose which interaction must genuinely work.

{{BRIEF}}
