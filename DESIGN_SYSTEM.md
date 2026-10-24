# ATLAS — Institutional Light

Palette: navigation navy #142638; warm canvas #F5F4F0; white analytical
surfaces; charcoal #26343B; muted teal #237D73; risk red #B44E50.
Supporting series use slate blue #496B85. Secondary text #596971.
System sans-serif typography avoids external font requests; financial values
use tabular numerals. Headings use restrained tight tracking and balanced wraps.

Layout:
```
nav / controls | title + source + dates + disclosure
               | primary risk measures
               | charts / tables / scenario assumptions
               | limitations / evidence / explicit review
```
Use 8px analytical surface corners, light borders, no decorative shadows or
entry animations. Keep units in labels and methodology beside results. Red
identifies loss/adverse states; words and numbers must also communicate state.
Preserve native Streamlit input semantics, including visible checkbox labels.
Never style clipped native inputs into custom interaction workarounds.

Five modules retain their existing responsibilities and calculations. Static
exports remain unapproved; Streamlit approval requires a named reviewer and
explicit acknowledgment, with input/draft changes revoking approval.

Responsive: static navigation becomes a horizontally scrollable module rail;
charts stack and scenario fields reduce columns at 760px/440px. Streamlit uses
native responsive columns and tabs. Visible keyboard focus, touch targets,
a skip link and reduced-motion support are retained. Mobile execution must be
verified in the browser suite; desktop inspection alone is insufficient.

## Icon identity

Phosphor Duotone is the sole custom icon family, from the supplied archive.
Local SVG geometry, 20–29px icons, pale teal badges and 14px analytical card
corners. Icons are decorative; explicit financial and approval labels remain.
MIT license retained in assets/icons/phosphor-duotone/LICENSE and generated HTML.
Hover transitions respect reduced-motion; no entry animations added.

## Approved Cloud Finance-inspired Streamlit baseline (Phase 2)

All five Streamlit modules now use #F6F6F8 canvas, white analytical cards,
#377CF6 blue navigation and #24304B text. Keep red for loss/breach states and
explicit units beside each chart. Preserve native keyboard controls, the compact
source disclosure, settings expander and 390px tab grid.

Factors use exposure/variance/correlation panels; scenarios use assumptions and
attribution; validation uses matched forecasts and exception diagnostics; review
uses a status/evidence panel and report. No new financial models are introduced.
The standalone public HTML remains unchanged in this Streamlit-focused phase.
