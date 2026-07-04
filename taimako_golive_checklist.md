# Taimako — Go-Live Checklist

**For:** Taimako operators (you), not customers.
**Purpose:** Everything that must be true before Taimako can responsibly
accept paying customers in production.
**Status convention:** `[ ]` open, `[~]` in progress, `[x]` done, `[NA]`
explicitly out of scope.

Ordered by "what stops you from selling" first, "what stops you from
scaling" second, "what keeps you out of legal trouble" throughout.

---

## 1. Meta / WhatsApp platform

Without these, customers physically cannot connect. This is the longest
lead-time section — start here.

- [ ] **Meta Business Verification** for Taimako's own Business Manager
      at `business.facebook.com/settings/business-verification`.
      Requires: company registration documents, domain, business phone.
      Lead time: a few days to a couple of weeks.
- [ ] **App Review** submitted and approved for the Taimako Meta app with
      permissions `whatsapp_business_messaging` and
      `whatsapp_business_management`. Requires a live demo, a privacy
      policy URL, and business use-case video. Lead time: 3–10 business
      days after submission.
- [ ] **Tech Provider** designation configured on the Meta app (under
      App Dashboard → WhatsApp → Configuration → Tech Provider settings).
- [ ] **Solution ID** registered and stored in `settings` for Embedded
      Signup. Blocks v1.1.8 from shipping.
- [ ] **Production webhook URL** (`https://<prod-domain>/whatsapp/webhook`)
      verified in the Meta app Configuration page; subscribed to
      `messages` and `message_template_status_update` fields.
- [ ] **Production `WHATSAPP_VERIFY_TOKEN`** and
      **`WHATSAPP_APP_SECRET`** generated fresh (not the dev values), set
      in prod env, rotated before any first paid customer.
- [ ] **Meta Business Support contact** established — submit a ticket
      early to get a named BSP/Tech Provider representative. Useful when
      templates get stuck in PENDING or numbers hit unexpected caps.

---

## 2. Legal & company

Skipping this section is how founders get personally sued.

- [ ] Company legally incorporated in operating jurisdiction (Nigeria /
      US Delaware C-corp / UK Ltd — whichever fits your GTM market).
- [ ] Business bank account in the company name.
- [ ] **Privacy Policy** published at `/privacy` — must mention WhatsApp
      data collection, retention, third-party processors (Meta, Google
      for Gemini, Paystack, host).
- [ ] **Terms of Service** published at `/terms` — include acceptable
      use (no unsolicited marketing, honor STOP replies, no scraping),
      the customer's obligation to comply with Meta's policies, and
      liability limits.
- [ ] **Data Processing Agreement (DPA)** template ready for any customer
      who asks — table-stakes for B2B.
- [ ] **NDPR / GDPR** posture documented (which applies depends on your
      market; NDPR for Nigeria, GDPR for EU). Register with the NDPC as
      a data controller if operating in Nigeria.
- [ ] **Cookie banner** on marketing site if serving EU traffic.
- [ ] **Incident response plan** written down: who is paged, who notifies
      customers, breach-notification SLA.
- [ ] **DMCA / abuse** contact email listed on site.

---

## 3. Infrastructure & reliability

- [ ] **Production domain** with SSL via Let's Encrypt or Cloudflare.
      Already using `taimako.dubem.xyz` — move to a brand domain before
      launch (e.g. `app.taimako.com` + `api.taimako.com`).
- [ ] **DNS + HTTPS redirects** set; root domain → marketing, `app` →
      dashboard, `api` → backend.
- [ ] **Staging environment** separate from production, same shape (same
      Postgres flavor + version, same ChromaDB, same env vars with staging
      values). CI/CD should deploy to staging before production.
- [ ] **Production Postgres** with:
      - [ ] Automated daily backups
      - [ ] Point-in-time recovery enabled
      - [ ] A documented and *tested* restore procedure
      - [ ] Connection pool sized for expected concurrency
- [ ] **ChromaDB** hosted durably (managed service or VM-attached
      persistent volume — not ephemeral container storage).
- [ ] **Secrets** managed outside the repo. At minimum: GitHub Actions
      secrets for CI + `.env` files on the host only readable by the
      service user. Consider HashiCorp Vault / AWS Secrets Manager /
      Doppler if growing.
- [ ] **Monitoring**:
      - [ ] Uptime monitor (UptimeRobot / BetterStack) on `/health`,
            webhook endpoint, frontend.
      - [ ] Error tracking (Sentry) wired into both FastAPI and Next.js.
      - [ ] Log aggregation (Loki / Datadog / Axiom) for
            `backend`, `whatsapp-worker`, `frontend` containers.
      - [ ] Worker-specific alert: no claimed campaigns in > N minutes
            during business hours.
      - [ ] Database alert: connections > 80% pool, disk > 80% full.
- [ ] **Rate limiting / DDoS**: Cloudflare in front of `api.taimako.*`
      with WAF rules on `/auth/*` and `/whatsapp/webhook`.
- [ ] **CORS + CSP** reviewed for production domains (current config in
      `backend/app/core/config.py` already narrows in `ProductionConfig`).
- [ ] **CDN** for frontend static assets (Vercel / Cloudflare Pages) if
      not already via Next.js deploy.

---

## 4. Security posture

- [ ] **v1.1 compliance items shipped** (see `whatsapp_roadmap.md`):
      - [ ] 1.1.1 STOP/UNSUBSCRIBE auto-opt-out
      - [ ] 1.1.2 WABA token encryption at rest
      - [ ] 1.1.3 24-hour customer service window enforcement
      - [ ] 1.1.4 Per-recipient rate limit + quality guardrail
      - [ ] 1.1.5 Template category/opt-in coupling
      - [ ] 1.1.6 Webhook signature verification on all paths
      - [ ] 1.1.7 Audit log
- [ ] **Dependency scanning** enabled (GitHub Dependabot at minimum;
      Snyk if you can afford it).
- [ ] **Secret scanning** on the repo (GitHub secret scanning is free).
- [ ] **JWT_SECRET** rotated from dev default; rotation procedure
      documented.
- [ ] **Admin access audit**: list every human / service account with
      production DB or server access. Remove anyone who left.
- [ ] **2FA mandatory** on Meta, GHCR, cloud host, Paystack dashboard,
      company Google Workspace.
- [ ] **Penetration test** (external) — ideally once before public launch
      and annually thereafter. Pick a firm that knows OWASP Top 10 and
      has done SaaS reviews.
- [ ] **Backup encryption** verified (both at rest and in transit to
      backup storage).
- [ ] **Data retention policy** documented — how long chat logs, guest
      messages, campaign messages are kept; what happens when a customer
      cancels.

---

## 5. Billing & payments

- [ ] **Paystack production credentials** in prod env
      (`PAYSTACK_LIVE_SECRET_KEY`, `PAYSTACK_LIVE_PUBLIC_KEY`).
- [ ] **Plan pricing finalized** in the DB — not just hard-coded
      constants. Whether you sell in NGN / USD / multi-currency.
- [ ] **Webhook signature verification** working for Paystack events
      (already implemented in `backend/app/services/subscription/paystack.py`
      — just verify the prod webhook URL is registered).
- [ ] **Subscription lifecycle tested end-to-end** in staging with real
      (test-mode) Paystack:
      - [ ] Successful charge → plan upgraded → credits topped up
      - [ ] Failed charge → dunning email sent → service downgrades
            after grace period
      - [ ] Voluntary cancellation → stays active until period end
      - [ ] Refunds processed correctly
- [ ] **Invoices** generated (PDF downloadable from dashboard) — most
      B2B customers will ask.
- [ ] **Tax handling** decided: VAT, NG VAT, sales tax. Talk to an
      accountant in your operating jurisdiction before first paid
      invoice goes out.
- [ ] **Revenue recognition / accounting** set up (Xero, QuickBooks,
      Wave).

---

## 6. Customer-facing polish

- [ ] **Public marketing site** at the root domain — landing, features,
      pricing, contact. Separate from the dashboard app.
- [ ] **Public documentation site** — see task (B) below for scope.
- [ ] **In-app onboarding** (first-run checklist: complete business
      profile → upload docs → connect WhatsApp → create first template).
      Current dashboard lacks this.
- [ ] **Status page** at `status.taimako.com` (e.g. via Instatus or
      BetterStack — show uptime of API, webhook, worker, frontend).
- [ ] **Support channel**:
      - [ ] `support@taimako.*` monitored address or shared inbox
            (Front / Helpscout)
      - [ ] In-app "Report a bug" link
      - [ ] SLA documented (e.g. first-response within 1 business day for
            paid plans)
- [ ] **Changelog / release notes** surface (either a `/changelog` page
      or in-app toast on new features).
- [ ] **Email deliverability**: warm up the sending domain, set SPF /
      DKIM / DMARC. Use a transactional provider (Postmark, Resend,
      SendGrid) — not SMTP from an unwarm IP.
- [ ] **Transactional email templates** audited: welcome, verification,
      plan upgraded, payment failed, campaign completed, escalation
      assigned.

---

## 7. Operations readiness

- [ ] **Runbooks** written for:
      - Worker crash / stuck
      - Meta token expired / revoked by customer
      - Meta webhook verify handshake failing
      - Postgres connection pool exhausted
      - ChromaDB corruption / rebuild-from-source
      - Paystack webhook backlog
      - Customer template stuck in PENDING > 24h
- [ ] **On-call rotation** — even if it's just one person, it needs
      coverage windows.
- [ ] **Deployment process** documented: who approves prod deploys,
      rollback procedure, post-deploy smoke test checklist.
- [ ] **Database migration policy**: never run destructive migrations
      during business hours; always have a rollback migration; snapshot
      before any risky change.
- [ ] **Admin impersonation** for support — log in as a customer with a
      flag so the audit log knows it was support, not the customer.
      (Not yet implemented; add an `impersonated_by` column on the audit
      log in 1.1.7.)
- [ ] **Feature flag system** — even a simple one (`flags` table keyed
      by `business_id`) — so you can gate risky features per-tenant.

---

## 8. Meta-specific operational hygiene

Things that will trip you in production if you haven't thought about them:

- [ ] **Template approval SLA** — track p50 / p90 approval time across
      your customer base. If it creeps up, raise with Meta support.
- [ ] **Quality rating dashboard** — consume Meta's `account_update`
      webhook and surface each tenant's current rating (GREEN / YELLOW /
      RED). Part of v1.1.4.
- [ ] **Phone number limits** — document internally that customers hit
      caps at the *portfolio* level (2 → 20 numbers after Meta support
      ticket + business verification). Support needs to know this or
      they'll tell customers the wrong thing.
- [ ] **Display-name policy** — customers often get their display name
      rejected. Have a FAQ ready (no tracking terms, brand match,
      length limits).
- [ ] **Token expiry handling** — if a customer rotates their Meta
      password, system-user tokens can get invalidated. Detect the `190`
      error code on sends, pause the tenant's campaigns, email them to
      reconnect. Part of v1.1.8 (Embedded Signup) cleanup.

---

## 9. Pre-launch smoke test

The 48 hours before flipping the public signup flag:

- [ ] Run the full test suite green on staging.
- [ ] Seed staging with three realistic tenants and run a marketing
      campaign end-to-end, observing webhooks and aggregate counts.
- [ ] Throttle-test: push 500 recipients through a campaign, confirm
      the worker stays under the configured rate and doesn't starve the
      API under load.
- [ ] Backup restore test on staging — destroy the staging DB, restore
      from last night's backup, confirm the app comes up clean.
- [ ] Verify SSL, HSTS, security headers (`securityheaders.com` audit).
- [ ] Ensure the marketing site doesn't leak staging endpoints.
- [ ] Dry-run the billing flow with a real Paystack card.
- [ ] Write a post-launch playbook: first-48-hours what-to-watch, who
      responds to what alert.

---

## 10. What to explicitly **not** do at launch

- Don't offer an SLA > 99.5% until you've run on production for 90+ days.
- Don't enable auto-approval of marketing templates without human review
  for the first 20 customers — you'll catch policy mistakes that would
  tank their quality rating.
- Don't advertise multi-WABA support — the schema is 1 WABA per business
  (v1.1 follow-up, not launch-blocker).
- Don't take enterprise contracts with custom BAAs / SOC2 questionnaires
  until you've actually been audited.

---

*Last updated: 2026-04-19. Review monthly.*
