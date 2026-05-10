# Getting Started with Taimako

**For:** new customers onboarding their WhatsApp Business number.
**Time required:** ~45–60 minutes if you already have a Meta Business
Manager; ~2 hours if you're starting from scratch (plus SMS / voice
verification wait).

This guide will eventually live on a dedicated documentation site. For
now it's the source of truth.

---

## What Taimako does

Taimako connects to your own WhatsApp Business number through Meta's
official Cloud API and lets you:

- **Answer customer chats automatically** with an AI agent trained on
  your own documents (FAQs, product catalogs, policies).
- **Send templated broadcasts** (marketing, utility, authentication) to
  your contact lists and track delivery / read rates.
- **Hand over to a human agent** when the AI needs help.
- **Manage contacts**, upload CSVs, and import people who've already
  chatted with you.

**What Taimako is not:** Taimako does not own your WhatsApp number, does
not send from a pool, and does not share limits with other customers.
Your number lives in your Meta Business Manager; Taimako just sends
through it.

---

## Before you start

You will need:

1. A personal Facebook account you control.
2. A **phone number** that is **not currently registered with WhatsApp**
   (neither personal WhatsApp nor WhatsApp Business app). If it is,
   de-register it first — you cannot use the same number on the Business
   API and the consumer app.
3. Your **company's legal name, address, and website** — needed to
   create a Meta Business Manager.
4. A **business email address** on a custom domain
   (`you@yourcompany.com`), not gmail/yahoo — Meta sometimes flags
   free-mail addresses during display-name review.
5. 5–10 minutes' access to receive an **SMS or voice call** on the phone
   number you're registering.

Optional but recommended:

- **Tax ID / registration certificate** — needed later if you want to
  raise your daily messaging limit past 250/day. You can onboard without
  it and add it later.

---

## Step 1 — Create your Taimako account

1. Go to `https://app.taimako.com/auth/login` *(update when finalized)*
   and sign in with Google.
2. Complete your **Business Profile**: business name, industry, website,
   description. This is what Taimako's AI agent introduces itself as to
   your customers.
3. Pick a plan. The free tier is fine to get started; you can upgrade
   anytime.

---

## Step 2 — Set up Meta Business Manager

Skip this step if you already have a Business Manager at
`business.facebook.com`.

1. Go to **`business.facebook.com/create`** and create a new Business
   Portfolio. Use your **legal business name** — this is what appears on
   invoices and is compared against your documents during verification.
2. Add your business details: address, phone, website.
3. Under **Business Settings → Users → People**, add yourself as an
   admin (you usually are by default).

**Tip:** One Business Portfolio can hold multiple WhatsApp numbers (up
to 2 by default, 20 after business verification). If you're running
several brands, decide now whether they share one portfolio or get
separate ones.

---

## Step 3 — Create a WhatsApp Business Account (WABA)

1. In Business Settings → **Accounts → WhatsApp Accounts**, click **Add
   → Create a WhatsApp Account**.
2. Give it a name (internal only — customers won't see it).
3. Assign yourself as an admin on the WABA.

---

## Step 4 — Register your phone number

1. Still in WhatsApp Accounts, click your new WABA → **Settings → Phone
   Numbers → Add phone number**.
2. Enter the number, choose SMS or voice verification, and enter the
   code when it arrives.
3. Set your **Display Name**. This is what customers see in WhatsApp
   above your messages.

**Display Name rules that trip people up:**

- Must match your brand (can't just be "Pizza" — needs to be "Pizza
  Palace Lagos" or similar).
- No URLs, hashtags, phone numbers, or generic terms like "Chat" /
  "Support Bot".
- Length 3–40 characters.
- Approval is usually instant, sometimes ~24 hours. If rejected, the
  error message tells you why — fix and resubmit.

---

## Step 5 — Generate a permanent access token

This is the most confusing part for most users, but it's a one-time
setup. When Taimako ships **Embedded Signup** (coming soon) this step
will disappear — you'll just click "Connect" and skip to Step 6.

1. In **Business Settings → Users → System Users**, click **Add →
   Create System User**.
2. Name it something recognizable, e.g. `Taimako Integration`.
3. Set the role to **Admin** and click Create.
4. In the system user's detail page, click **Add Assets → WhatsApp
   Accounts**. Select the WABA you created in Step 3 and grant **Full
   control**.
5. Back on the system user page, click **Generate New Token**.
6. **Select your Meta App** — if you have one; if not, click the link
   to create a minimal dev-mode app (just needed as a container for the
   token; you don't have to submit it for review).
7. Under **Permissions**, tick:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
8. **Set token expiration to "Never"**. Default is 60 days — you don't
   want to reconnect every two months.
9. Click **Generate Token** and **copy it immediately** — you'll never
   see it again. If you lose it, just generate a new one here.

---

## Step 6 — Grab your Phone Number ID and WABA ID

1. Go to **WhatsApp Manager** (top-right app picker at
   `business.facebook.com` → WhatsApp).
2. Click your phone number.
3. In the right-hand panel, copy:
   - **Phone Number ID** (string of digits)
   - **WhatsApp Business Account ID** (usually shown near the top)

---

## Step 7 — Connect to Taimako

1. In Taimako, go to **Dashboard → Settings → WhatsApp**.
2. Paste your **Phone Number**, **Phone Number ID**, **Business Account
   ID**, and **Access Token** from the previous steps.
3. *(Optional)* Set your **Send Rate** — messages per second the broadcast
   worker will pace sends at. Default is fine for the free tier; if
   Meta has moved you to a higher messaging tier (10K/day or more), you
   can bump this to 40–60. Leave blank for the Taimako default.
4. Flip the **WhatsApp Channel** toggle to ON.
5. Click **Save**.

Taimako will validate the credentials with Meta within a few seconds.
If you see "WhatsApp API credentials are configured" in green, you're
good. If you see an error, the most common causes are:

- Token was copied with a trailing space.
- Token doesn't have both scopes — regenerate with the correct
  permissions.
- Phone Number ID pasted instead of WABA ID or vice versa.

---

## Step 8 — Test the inbound flow

1. From your personal WhatsApp, send a message to your registered
   business number.
2. Within a few seconds you should see an AI reply (the welcome message
   you configured in Business Profile).
3. In Taimako dashboard → **Sessions**, the conversation appears in
   real time.

If nothing happens, check: (1) your Taimako backend is reachable over
HTTPS; (2) the WhatsApp Channel toggle is ON; (3) the system user token
has the right scopes.

---

## Step 9 — Upload documents (train your AI)

1. Dashboard → **Documents → Upload**.
2. Drop in your FAQs, product catalogs, return policies — anything your
   AI should know. PDFs, Word, Markdown, plain text all work.
3. Processing takes a minute or two per document. Watch the indexing
   status turn green.
4. Send another WhatsApp message to your business number and ask
   something from the documents. The AI should answer accurately.

**Tip:** quality in, quality out. One well-written FAQ document beats
ten messy PDFs. Trim repeated headers, boilerplate, legal disclaimers
before uploading.

---

## Step 10 — Create your first broadcast template

Meta requires that *outbound* marketing messages use a template they've
pre-approved. Templates take minutes to hours to approve.

1. Dashboard → **WhatsApp → Templates → New Template**.
2. Fill in:
   - **Name** (lowercase, underscores only — e.g. `weekend_special`)
   - **Category**:
     - `MARKETING` — promotional
     - `UTILITY` — transactional (order updates, appointment reminders)
     - `AUTHENTICATION` — OTPs (has stricter rules)
   - **Language** (e.g. `en_US`)
   - **Body** with `{{1}}`, `{{2}}` placeholders for per-recipient
     variables. Example: `Hi {{1}}, your order {{2}} is ready for
     pickup at {{3}}.`
3. Optionally add a **header**, **footer**, or **buttons**.
4. Click **Save** (status = DRAFT), then **Submit** (status = PENDING).
5. Wait for Meta's approval — usually minutes, sometimes hours.
   Rejected templates come back with a reason; fix and resubmit.

**Tip:** already have approved templates in Meta Business Manager? Click
**Import from Meta** on the Templates page to pull them into Taimako.

---

## Step 11 — Add contacts

Three ways:

1. **Manual** — Dashboard → WhatsApp → Contacts → Add Contact. Enter
   name + phone (E.164 format, e.g. `+2348012345678`).
2. **CSV upload** — prepare a CSV with columns `phone`, `name`, `tags`.
   Phone column required, rest optional. Invalid rows are skipped with
   an error report.
3. **Import from WhatsApp chats** — imports everyone who has already
   messaged your business number. Great for launching a marketing
   campaign to engaged leads.

Group contacts into **Lists** (e.g. "VIP customers", "Lagos branch")
for easier targeting.

---

## Step 12 — Send your first campaign

1. Dashboard → **WhatsApp → Campaigns → New Campaign**.
2. Name it, pick your approved template, pick the audience (List or
   ad-hoc), map the template variables (literal strings or contact
   fields like `@name`), schedule for now or later.
3. Click **Create → Send**.
4. Open the campaign detail page to watch delivery in real time (Sent →
   Delivered → Read funnel).

Start small. **Always send your first real campaign to yourself plus
one colleague first**, then scale up.

---

## Messaging tiers — how to grow your daily limit

Meta limits how many unique contacts you can message per 24-hour
period, at the **Business Portfolio** level.

| Tier | Unique contacts / 24h | How to unlock |
|---|---|---|
| Unverified | 250 | Default starting state |
| Verified starter | 1,000 | Complete Meta Business Verification |
| Tier 2 | 10,000 | Send high-quality messages consistently; Meta auto-promotes |
| Tier 3 | 100,000 | Continued quality + volume — usually takes months |
| Tier 4 | Unlimited | Enterprise-scale; rare |

**Quality rating** (GREEN / YELLOW / RED) drives tier promotion. You
keep it GREEN by:

- Only messaging people who expect to hear from you.
- Honoring opt-outs immediately (Taimako does this for you).
- Sending relevant content that gets replies, not silence.
- Avoiding complaints and blocks (big red flag for Meta).

---

## Compliance basics — read this once

WhatsApp is stricter than SMS or email marketing. Violating these can
permanently ban your number.

- **Only message opted-in contacts** for marketing templates.
  Opt-in can be a website form, a chat reply, a physical form, a QR
  code scan — whatever, but you must be able to show proof if Meta asks.
- **Honor STOP replies.** If someone replies "STOP", "UNSUBSCRIBE",
  "CANCEL", etc., stop messaging them immediately. Taimako flips their
  `opted_in` flag automatically.
- **Stay in the 24-hour window for free-form replies.** Outside 24h
  from the customer's last message, only pre-approved templates are
  allowed.
- **Don't buy contact lists.** Fast track to RED quality rating and
  number ban.
- **Match the template category** to the actual content. Sending
  marketing content through a UTILITY template is a policy violation
  Meta catches.
- **Respect local law.** NDPR (Nigeria), GDPR (EU), TCPA (US) all have
  their own opt-in, disclosure, and retention rules that sit *on top*
  of Meta's. Talk to a lawyer if you're at scale.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Credentials saved but WhatsApp Channel toggle resets to off" | Wrong scope on system-user token | Regenerate token with `whatsapp_business_messaging` + `whatsapp_business_management` |
| Inbound messages not reaching Taimako | Webhook not subscribed to `messages` field, or your WABA isn't subscribed to the Taimako app | Ask Taimako support to re-subscribe your WABA |
| Template stuck in PENDING > 24h | Meta reviewer backlog | Don't resubmit (that resets the queue). Wait 48h, then contact Meta support |
| Template REJECTED with no clear reason | Usually "promotional content in UTILITY category" or "not in local language" | Switch category or language, fix content, resubmit |
| Campaign marked FAILED immediately | Token expired or revoked on the Meta side | Generate new token in Meta Business Manager, paste into Taimako |
| Delivered but not Read forever | Recipient has not opened the message or has read receipts off | Normal — don't use "Read" as a delivery metric |
| Hit "250/day" cap | Unverified portfolio | Complete Meta Business Verification, then raise via support ticket |

---

## Getting help

- **Dashboard → Help** for in-app docs.
- **`support@taimako.com`** for account / billing issues.
- **Meta Business Help Center** (`business.facebook.com/business/help`)
  for anything WhatsApp-policy or template-approval related — Taimako
  can't override Meta's rulings.

---

## What's next after you're live

- **Automate replies for common questions** — see the docs on custom
  agent instructions.
- **Segment contacts with tags** and run separate campaigns per segment.
- **Route to a human** — set up escalation so complex queries reach a
  live agent in Taimako.
- **Monitor quality rating weekly** — it's a leading indicator of
  problems.

Welcome to Taimako.

---

*Last updated: 2026-04-19. If you spot anything outdated, email
docs@taimako.com.*
