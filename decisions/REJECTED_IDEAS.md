# Rejected Ideas

Ideas evaluated and dismissed. Recorded so we don't relitigate.

---

## 2026-05-22 — Cloudflare bypass for AIOS→Hermes pull bridge

**Idea:** Unblock Railway IP in Cloudflare Access so Hermes can pull from aios.agcoachos.com.

**Why rejected:** Papers over wrong architecture. Laptop sleep/offline silently breaks Hermes context regardless of Cloudflare config. Push model chosen instead.

**Would reconsider if:** AIOS moves to always-on hosting (Railway, etc).

---

## 2026-05-22 — Move AIOS dashboard to Railway

**Idea:** Host AIOS on Railway ($5/mo) so Hermes can reach it.

**Why rejected:** Overkill for a dev dashboard Bryan runs locally. Push model solves the problem without ongoing cost.

**Would reconsider if:** AIOS needs to serve multiple users or run 24/7.

---

## 2026-05-12 — L4 autonomous email replies

**Idea:** Let AIOS send email replies without Bryan's review.

**Why rejected:** Too early. No validation history. Risk of sending wrong tone or bad info to school customers.

**Would reconsider if:** 50+ successful drafts reviewed and approved with <5% edit rate.
