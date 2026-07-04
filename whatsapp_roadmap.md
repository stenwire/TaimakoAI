# WhatsApp Roadmap — Post-v1

v1 (shipped on `whatsapp-intg-v1`) gives businesses a working outbound pipeline:
contacts, templates, campaigns, a scheduler, and a monitoring dashboard. It is
**usable for demos and controlled pilots** but is **not ready for real marketing
traffic at scale** until v1.1 compliance items land.

Versions below are ordered by the value-over-effort ratio I'd actually ship
them in. Each item has a rough size, a rationale, and the key policy /
security angle where relevant.

---

## v1.1 — Compliance & security hardening (**blocker for real usage**)

These are not optional if you plan to send marketing templates to real
customers. Meta enforces them via quality rating and template pauses; skipping
them is how tenants get their WABA suspended.

### 1.1.1 STOP / UNSUBSCRIBE auto-opt-out  *(S)*
Extend `backend/app/api/whatsapp.py` so inbound messages matching
`STOP|UNSUBSCRIBE|CANCEL|QUIT|END` (case-insensitive, trimmed) flip the
matching `whatsapp_contacts.opted_in` to `false` and send a one-time
acknowledgement. Worker must honor `opted_in=false` during
`expand_recipients` — already a column, just not enforced.
- **Policy:** Meta requires honoring opt-outs for marketing templates. Non-
  compliance degrades quality rating → template pausing → WABA ban.

### 1.1.2 WABA token encryption at rest  *(S)*
Wrap `widget_settings.whatsapp_access_token` in a Fernet cipher (new
`APP_ENCRYPTION_KEY` env var). Decrypt only in the WhatsApp client layer.
Migration re-encrypts existing plaintext values.
- **Security:** permanent system-user tokens can send templates at scale. DB
  dumps or read-replica leaks currently expose this directly.

### 1.1.3 24-hour customer service window enforcement  *(M)*
Meta allows free-form (non-template) outbound messages only within 24h of the
user's last inbound. Today the inbound AI reply path already respects this
implicitly, but nothing blocks an admin from sending free-form traffic out-of-
window via the broadcast path (if we ever expose it). Add a
`conversation_window_expires_at` column on a per-contact basis, updated by the
inbound webhook, and gate non-template sends on it.
- **Policy:** sending free-form outside the window is a direct policy
  violation; Meta returns `131047` and it counts against quality.

### 1.1.4 Per-recipient rate limit + global quality guardrail  *(S)*
- Hard-limit per (business_id, contact_phone): max N template messages per
  24h (default 1 marketing, 3 utility — configurable per business).
- On Meta quality rating webhook (`account_update` field), if quality drops
  to `RED`, auto-pause all `SCHEDULED` campaigns for that WABA and surface a
  banner in the UI.
- **Policy:** prevents accidental spam from a misconfigured audience import.

### 1.1.5 Template category & opt-in coupling  *(S)*
Marketing category → must target `opted_in=true` contacts.
Utility/Authentication → allowed on any contact inside the 24h window or with
a valid template. Enforce in `campaigns.create_campaign` and surface as a
clear error, not a 500.

### 1.1.6 Webhook signature verification on *all* paths  *(S)*
`backend/app/api/whatsapp.py` already has `verify_webhook_signature` — make
sure the status-update branch I added in v1 also runs it. A spoofed webhook
could flip campaign statuses.

### 1.1.7 Audit log  *(M)*
New `whatsapp_audit_events` table: who created/sent/cancelled what, when,
from what IP. Exposed read-only in the admin panel.
- **Security / compliance:** needed for SOC2, ISO, and most B2B procurement
  reviews. Also protects against insider abuse.

### 1.1.8 Meta Embedded Signup (replaces manual credential paste)  *(L)*
Today users copy-paste three values (Phone Number ID, WABA ID, permanent
access token) from their own Business Manager into Taimako's WhatsApp
settings page. That is technically correct — tenants' WABAs stay in their
own Business Portfolios, so portfolio-level limits (2→20 numbers,
250→unlimited daily tier) are theirs, not Taimako's — but the UX is awful
and has been the #1 source of onboarding failures.

Replace with Meta's **Embedded Signup** flow:

- Prerequisites (one-time, Taimako side):
  - Business-verify Taimako's own Meta Business Manager.
  - Configure the existing Meta app as **Tech Provider** and submit for App
    Review with `whatsapp_business_messaging` +
    `whatsapp_business_management` permissions. Review takes ~3–10 business
    days.
  - Register Taimako's Solution ID in the app settings.

- Frontend:
  - Add Facebook JS SDK (`FB.login(..., { config_id, response_type,
    override_default_response_type })`) behind a single "Connect WhatsApp
    Business" button on the existing settings page.
  - Handle the embedded popup: user signs in to their own Meta account,
    selects or creates their own Business Portfolio, selects or creates
    their own WABA, and registers their own phone number. Meta returns a
    short-lived code.

- Backend:
  - New endpoint `POST /whatsapp/embedded-signup/exchange` that exchanges
    the code for a permanent system-user access token via Graph API, then
    persists `whatsapp_phone_number_id` / `whatsapp_business_account_id` /
    `whatsapp_access_token` on the tenant's `widget_settings`.
  - Subscribe the tenant's WABA to Taimako's webhook URL
    programmatically via Graph `{waba-id}/subscribed_apps`.

- UI cleanup:
  - Hide the manual paste inputs once a tenant is connected via Embedded
    Signup; still render them for users who connected before this feature
    shipped (migration path — not a data migration, just a conditional).
  - Remove any remaining references to backend env vars, webhook URLs,
    and verify tokens from user-facing copy (the v1.0.2 quick rewrite
    already removed the worst offenders, but the "manual" card stays
    visible until the user connects).

- **Security/SaaS-correctness:** this is the correct onboarding pattern for
  every production WhatsApp SaaS (Wati, Respond.io, 360dialog, Gallabox,
  Interakt all use it). It also eliminates the accidental-leak risk of
  users pasting permanent tokens into logs, screenshots, or support
  chats.
- **Policy:** must be implemented before public launch — Meta increasingly
  flags manual-token-paste flows during App Review as "not production
  grade" for SaaS apps.

---

## v1.2 — Operational polish

### 1.2.1 Real-time template status updates  *(S)*
Subscribe to `message_template_status_update` webhook (already in setup
doc), update `whatsapp_templates.status` on receipt. Today the UI needs a
manual refresh; low-effort high-UX win.

### 1.2.2 Failed-message retry with backoff  *(S)*
Per-message retry for transient Meta errors (`5xx`, rate-limit codes).
`whatsapp_campaign_messages` gets `retry_count` + `next_retry_at`. Worker
skips messages whose next_retry is in the future.

### 1.2.3 Campaign clone & resume  *(S)*
"Duplicate campaign" button; and for a `FAILED` campaign, a "Send only to
unsent" button that creates a child campaign.

### 1.2.4 Per-contact timeline view  *(M)*
Open a contact → see every campaign they've received, every reply, every
status change. Critical for sales follow-up.

### 1.2.5 Better CSV UX  *(S)*
Preview first 5 rows, column auto-mapper, downloadable error report
(`invalid_rows.csv`) instead of a flat error list.

---

## v1.3 — Lead generation

This is where Taimako starts to become a *product* and not just a broadcast
tool. All of these fit inside WABA policy because they are reactive to
inbound intent.

### 1.3.1 Click-to-WhatsApp entry points  *(S)*
- Generate per-business WhatsApp deep-links (`https://wa.me/<phone>?text=<pre-filled>`).
- Embeddable QR code + "Chat on WhatsApp" button for the existing widget.
- Per-link UTM-style `ref` param → stored on the resulting `ChatSession`
  so you can attribute leads to source (Instagram ad, landing page, etc.).

### 1.3.2 Keyword-triggered flows  *(M)*
Business-configurable: when inbound message matches keyword/regex, auto-
send a specific template or kick off a Flow. Think "PRICING" → sends pricing
template, creates lead record.

### 1.3.3 Lead capture with WhatsApp Flows  *(L)*
Meta's new Flows product lets you run multi-step forms (name, email,
interest, budget) inside WhatsApp without leaving. Build a visual Flow
builder in the dashboard that compiles to Meta's Flow JSON. Each completed
Flow becomes a `Lead` record (new table) with status pipeline (NEW →
QUALIFIED → CUSTOMER → LOST).

### 1.3.4 CRM-lite  *(M)*
Custom fields on `whatsapp_contacts` (typed: text, number, date, single-
select). Variable mapping can reference these. This is the table-stakes
feature every competitor ships.

### 1.3.5 AI lead scoring  *(M)*
Plug into Taimako's existing Gemini stack: score each lead 0–100 on
likelihood-to-close based on message history + profile. Surface a "Hot
leads" dashboard. This is Taimako's natural moat — competitors like Wati
bolt on basic CRM but don't have a RAG/AI layer already running.

---

## v1.4 — Interactive & rich messages

### 1.4.1 Button, list, and quick-reply templates  *(M)*
Template builder supports `buttons: [{type: 'URL'|'QUICK_REPLY'|'PHONE_NUMBER'}]`.
Inbound webhook routes button replies to the right handler (e.g. a
QUICK_REPLY click can auto-tag the contact).

### 1.4.2 Media templates  *(M)*
Header image / video / document uploads. Store in S3 / Cloudflare R2, hand
Meta a signed URL. Needed for anything retail.

### 1.4.3 Catalog & product messages  *(L)*
For e-commerce tenants: sync a product feed, send catalog messages, receive
order_placed webhooks. Ties into Meta Commerce Manager.

### 1.4.4 AI reply suggestions for agents  *(M)*
On the Escalation handoff screen, show 3 AI-drafted reply options (powered
by the existing RAG). Agent clicks → edits → sends. Proven to 2-3× agent
throughput in support tools.

---

## v1.5 — Automation & sequences

### 1.5.1 Drip campaigns  *(L)*
Multi-step sequences: "Send template A on day 0 → wait 3 days → if no reply,
send B → if reply, tag as engaged → send C to engaged after 7 days." Needs a
state machine on `campaign_messages` and the worker grows a scheduler tier.

### 1.5.2 Behavioral segmentation  *(M)*
Dynamic lists: "contacts who replied to campaign X", "contacts who clicked a
button in the last 7 days", "contacts who have not been messaged in 30 days".
Re-evaluated at campaign-create time so audiences stay fresh.

### 1.5.3 A/B testing  *(M)*
Split a campaign's audience 50/50 across two template variants, track
delivered/read/reply/conversion per variant, auto-promote the winner.

### 1.5.4 Event-triggered campaigns  *(M)*
Webhook / API endpoint: "fire campaign X with variables Y for contact Z."
Lets customers trigger from their own backend (e.g. new order → shipping
update template).

---

## v1.6 — Analytics & revenue

### 1.6.1 Conversion attribution  *(M)*
Define a conversion event (button click, webhook ping, reply matching a
pattern). Attribute conversions back to campaigns. Report revenue per
campaign when the customer posts order values.

### 1.6.2 Cost-per-message + Meta pricing integration  *(S)*
Meta charges per conversation (not per message, since July 2025). Pull
their pricing tiers per country, show per-campaign cost, per-lead cost,
ROI. Competitors upcharge blindly on this — being transparent is a
positioning moat.

### 1.6.3 Cohort & retention reports  *(M)*
Standard stuff: opt-out rate trend, reply rate by template, quality rating
history, day-of-week performance.

---

## v1.7 — Enterprise readiness

### 1.7.1 Role-based access control  *(M)*
Today we have `is_admin`. Add: `campaign_creator`, `campaign_approver`,
`viewer`. Approval workflow: creator drafts → approver signs off → only
then can it be scheduled. Needed for any regulated industry.

### 1.7.2 SSO (SAML / OIDC)  *(M)*
Google OAuth alone gates out ~everyone enterprise. Add Okta / Azure AD.

### 1.7.3 GDPR / NDPR tooling  *(S)*
Per-contact "export all data" and "delete all data" endpoints (NDPR is
Nigeria's equivalent, important for local GTM). The schema already
cascades correctly; just needs a UI and an admin audit trail.

### 1.7.4 Multi-WABA per business  *(L)*
New `whatsapp_accounts` table, `campaign.whatsapp_account_id` FK. Enables
agencies managing many clients under one Taimako tenant.

### 1.7.5 Data residency  *(L)*
For EU/UK buyers: optional EU-region Postgres + ChromaDB. Big lift, but
unlocks a deal-size tier.

---

## v2.0 — Scale

Only worth doing once you have the usage to justify it.

### 2.0.1 Redis + Celery migration  *(L)*
Today's DB-polled worker is fine up to ~low thousands of messages/hour.
Beyond that, `FOR UPDATE SKIP LOCKED` contention and poll latency start
to hurt. Move to Redis-backed Celery with per-WABA queues.

### 2.0.2 Multi-region workers  *(L)*
Pin workers to the region closest to each tenant's WABA / recipients so
delivery latency is tight and Meta's geo-routing stays happy.

### 2.0.3 Warm standby / blue-green for the worker  *(M)*
Today a worker restart during a 10k-contact send just pauses the batch —
fine for v1 but noticeable for paying customers.

---

## Explicitly out of scope (policy)

- **WhatsApp Channels** — not exposed in Business API, no programmatic path.
- **WhatsApp Groups** — not in Business API. Any 3rd-party library (Baileys,
  whatsapp-web.js) that claims to do this runs on the unofficial web protocol
  and will get the tenant's number permanently banned.
- **Scraping contacts from public WhatsApp groups / number lists** — direct
  policy violation, do not build this even if asked.
- **Sending templates to non-opted-in contacts** — covered in v1.1.4/1.1.5.

---

## Suggested shipping order (honest)

1. **v1.1 in full** — non-negotiable before any real traffic. 1–2 weeks.
2. **v1.2.1 + v1.2.2 + v1.3.1** — cheap wins that dramatically improve demos.
3. **v1.3.4 (CRM-lite) + v1.3.5 (AI scoring)** — this is the differentiator.
4. **v1.4.1 (buttons) + v1.4.4 (AI reply suggestions)** — rounds out the
   product into a "conversational commerce" positioning.
5. **v1.5 + v1.6** — needed once you have customers asking "what's my ROI?"
6. **v1.7** — pull forward only when the first enterprise deal is on the
   table; premature otherwise.

---

# Does Taimako solve a real problem? Is it fundable?

Short answer: **yes to the first, conditionally yes to the second.** My
honest read as a working engineer who has seen a lot of "AI chatbot" pitches:

## The real-problem case is genuinely strong

- **SMBs in emerging markets run their businesses on personal WhatsApp.**
  Nigeria, Kenya, SA, India, Indonesia, Brazil, Mexico — the dominant B2C
  channel is WhatsApp, not email and not web chat. The current state is one
  owner answering from their phone at 11pm. That is a real, painful gap that
  US-centric tools (Intercom, Drift, Zendesk) do not solve well because
  they're web-chat-first.
- **WABA tooling is a proven category.** Wati, Gallabox, Respond.io,
  Interakt, MessageBird, 360dialog — all profitable or well-funded. Wati
  alone did ~$20M ARR on essentially this exact feature set before adding
  AI. The TAM is not speculative.
- **The AI layer is where a 2025+ entrant can actually win.** The incumbents
  bolted AI on late and half-heartedly. Taimako starts with RAG + Gemini in
  the core, which means features like AI lead scoring (v1.3.5), AI reply
  suggestions (v1.4.4), and AI-personalized templates are natural
  extensions, not retrofits. That's a real wedge.

## Where I'd push back

- **The support-widget product alone is a commodity.** If Taimako is pitched
  as "AI chat widget" it's competing with fifty near-identical offerings
  including free tiers of Intercom Fin and the default ChatGPT-for-business
  wrappers. Widget-as-the-product has no moat.
- **WhatsApp outbound is also getting commoditized fast.** Meta is pushing
  BSPs hard; prices compress every quarter. Margin on pure message volume
  is not where the business is.
- **The moat has to be the combination**: "AI agent that answers in
  WhatsApp from your docs **and** runs your marketing **and** scores your
  leads, built for African/LATAM SMB." That framing is fundable. "Another
  AI chatbot" is not.

## Funding view

- **Pre-seed / seed (≤$2M):** very reachable if you can show (a) 5–10 real
  paying SMB tenants in one target market, (b) WhatsApp-first positioning,
  (c) founder with domain credibility. African-focused founders have a
  cleaner path here because of funds specifically deploying there
  (Ventures Platform, Future Africa, Norrsken, Raba, Chipper-alum
  networks, and YC with its African cohort).
- **Series A:** needs $1M+ ARR and evidence that the combined AI-support +
  broadcast + lead-gen loop produces better retention than point tools.
  Feasible but not automatic.
- **Comparables worth naming to investors:**
  *Wati* (Series B, Tiger Global, ~$23M raised), *Respond.io* (Series A,
  $27M), *Gallabox* (seed, India/ME), *360dialog* (acquired by Bird),
  *Interakt* (acquired by Jio Haptik). The template is established.
- **Risks investors will ask about:**
  - *Platform risk.* Meta owns the rails. A policy change can tank margin
    overnight. Answer: multi-channel roadmap (v1.8 SMS/email fallback),
    proprietary lead CRM layer that isn't WABA-dependent.
  - *Distribution.* SMB GTM is famously expensive. Answer needs to be
    product-led growth + local partner channel (banks, accountancy firms,
    telcos in target markets).
  - *AI commoditization.* Gemini-specific code is a liability. The
    `agent_factory` already abstracts this, which helps.

## My one-line take

Taimako is a **real product shaped like a real business**, sitting in a
category with proven buyers. Whether it gets funded depends less on the
code (the code is fine) and more on whether the GTM is crisp — pick one
market, one ICP, and show WhatsApp-native retention. If the pitch is
"AI chatbot platform," it's a no. If the pitch is "the operating system
for SMBs that sell on WhatsApp in [specific region]," it's a yes.
