# Challenge checklist: what the website needs, page by page

Source: the challenge's minimum demo as recorded in `PROJECT_BRIEF.md`. The official requirements doc
(`docs/HackOHIO_2026_AI_Outage_Concierge_Challenge.docx` in github.com/hackohio/aep_challenge_hack26) has not been read yet,
so check this list against it. Judges score the **submitted video**, so every row should be easy to show on screen.

## What the challenge asks for

| # | Requirement | Where it lives now | Status | Ideas to make it stand out |
|---|---|---|---|---|
| 1 | Customer picks an anonymized location | Sidebar: 3 personas + "Pick another location" (city, road, anonymous code) | Done | Small map with circuit shading (no house points); search by city |
| 2 | Outage-risk prediction **with confidence and explanation** | **Will I lose power?** | Done: band, gauge, 3 reasons, confidence dots | Compare to "average home on this circuit"; one-line plain summary at the top |
| 3 | Damage/restoration **scenarios** give a restoration **range** | **How long will it last?** | Done: 3 sliders + what-if table + "how we got this number" | Simple timeline bar (assess, repair, restore in steps); show the range as a visual band, not just text |
| 4a | Preparation actions | **How do I prepare?** | Done: safety box + checklist, medical steps only when declared | Tick-off checklist; "print / save" view; tailor by expected hours out |
| 4b | Alert eligibility | **Outage alerts** | Done: rules table, timing/channel plan, when a person steps in | Clear yes/no badge at top; mock "sign up" button flow |
| 5 | At least one proactive message | **Messages we send** | Done: 4 messages (before, confirmed, updated, restored) | Phone-frame mockup; show a message changing when the sliders change |
| 6 | Show how **privacy, safety, uncertainty and model limits** are handled | **How this works** + chips on every page + safety box | Done | Split into 4 short cards (Privacy, Safety, Uncertainty, Limits) so each is easy to point at in the video |
| 7 | Judges can **change a scenario input and see the response** | Sidebar storm scenario + sliders | Done: every page updates, slider values carry across pages | Make the scenario switch more visible on each page, not only in the sidebar |

## Rules that must not break (from the brief)

| Rule | How we meet it |
|---|---|
| Never show premise numbers, house numbers, coordinates or the life-support flag | Random one-way location codes; those fields are not in the app's data |
| Never infer medical or sensitive attributes | Medical steps only after the user ticks "Medical equipment at home" |
| Estimates are always ranges and labeled as estimates | Dashed "Model estimate" chip and outline on every estimate |
| Messages keep the "[DEMO]" prefix; don't imply utility endorsement | Prefix in `engine.messages`; footer disclaimer on every page |
| Don't call it a trained or validated model | Wording says "exposure score" and "calibrated on one storm" |

## Pages and what to fix on each

| Page | Answers the question | To review |
|---|---|---|
| Overview | What is this, and what's my situation at a glance? | |
| Will I lose power? | Risk band, confidence, why | |
| How long will it last? | Restoration range and what-ifs | |
| How do I prepare? | Safety and prep steps | |
| Outage alerts | Do I qualify, and what would I get? | |
| Messages we send | The four customer messages | |
| How this works | Data, method, privacy, limits | |

## Still unknown
- Official judging criteria and submission deadline (HackOHI/O Judging Guide), see Open items in `PROJECT_BRIEF.md`.
- Anything in the official challenge doc beyond the minimum demo above.
