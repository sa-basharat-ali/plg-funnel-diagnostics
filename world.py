"""A synthetic product-led funnel shaped like a GTM data platform with a free plan, unlimited
seats, usage metered in actions, and growth driven by creators, agencies and community.

Everything is generated with a fixed seed. No real company, person or campaign is represented.
"""
import math
import random

SEED = 2026
SEGMENTS = {  # share of companies, workspaces per company, intent multiplier
    "startup": (0.55, (1, 2), 1.0),
    "midmarket": (0.25, (1, 4), 1.3),
    "enterprise": (0.08, (2, 9), 1.6),
    "agency": (0.12, (1, 3), 2.2),
}
CHANNELS = ["creator", "agency_referral", "community", "seo", "paid_ads", "event", "word_of_mouth"]
CH_MIX = {"startup": [0.28, 0.10, 0.14, 0.18, 0.10, 0.04, 0.16],
          "midmarket": [0.22, 0.12, 0.12, 0.18, 0.14, 0.08, 0.14],
          "enterprise": [0.14, 0.08, 0.08, 0.16, 0.18, 0.16, 0.20],
          "agency": [0.34, 0.06, 0.26, 0.10, 0.06, 0.06, 0.12]}
# how each true channel shows up in last-touch tracking
LAST_TOUCH = {"creator": [("creator_link", 0.35), ("direct", 0.65)],
              "agency_referral": [("direct", 1.0)],
              "community": [("direct", 0.8), ("organic_search", 0.2)],
              "seo": [("organic_search", 1.0)],
              "paid_ads": [("paid", 0.92), ("direct", 0.08)],
              "event": [("direct", 0.7), ("organic_search", 0.3)],
              "word_of_mouth": [("direct", 1.0)]}
SELF_REPORT = {"creator": "LinkedIn", "agency_referral": "Agency or consultant", "community": "Community / Slack",
               "seo": "Search", "paid_ads": "Ad", "event": "Event", "word_of_mouth": "Friend or colleague"}
FREE_ACTIONS, LAUNCH_ACTIONS, GROWTH_ACTIONS = 500, 15_000, 40_000
PQL_ACTIONS = 300           # current routing: a single workspace over this in 14 days
SIZE_ROUTE = "200+"          # current routing: or a form that says 200+ employees


def _pick(rng, pairs):
    r, acc = rng.random(), 0
    for v, p in pairs:
        acc += p
        if r <= acc:
            return v
    return pairs[-1][0]


def _recall(rng, ch):
    """People misremember: a LinkedIn ad becomes 'LinkedIn', an event becomes a colleague's tip."""
    if ch == "paid_ads" and rng.random() < 0.45:
        return "LinkedIn"
    if ch == "event" and rng.random() < 0.35:
        return "Friend or colleague"
    if ch == "agency_referral" and rng.random() < 0.3:
        return "Friend or colleague"
    return SELF_REPORT[ch]


def build(n_companies=3000):
    rng = random.Random(SEED)
    companies, workspaces, signups = [], [], []
    seg_names = list(SEGMENTS)
    for cid in range(1, n_companies + 1):
        seg = rng.choices(seg_names, [SEGMENTS[s][0] for s in seg_names])[0]
        intent = rng.lognormvariate(0, 0.9) * SEGMENTS[seg][2]
        size = {"startup": "1-50", "midmarket": rng.choice(["51-200", "200+"]),
                "enterprise": "200+", "agency": rng.choice(["1-50", "51-200"])}[seg]
        domain = f"co{cid}.com"
        companies.append({"company_id": cid, "segment": seg, "intent": intent, "size": size, "domain": domain})
        lo, hi = SEGMENTS[seg][1]
        nws = rng.randint(lo, hi)
        for w in range(nws):
            wid = f"w{cid}_{w}"
            ch = rng.choices(CHANNELS, CH_MIX[seg])[0]
            # actions used in the first 14 days: driven by intent, capped by the free plan
            # teams inside one company each try it a little; the company's intent is split across them
            a14 = min(FREE_ACTIONS, int(rng.lognormvariate(math.log(60 * intent / nws ** 0.6), 0.8)))
            workspaces.append({"workspace_id": wid, "company_id": cid, "channel": ch, "actions_14d": a14})
            for p in range(rng.randint(1, 4 if seg in ("enterprise", "midmarket") else 2)):
                personal = rng.random() < 0.16  # signs up with a personal email
                form_size = size if rng.random() < 0.7 else rng.choice(["1-50", "51-200", "200+", ""])
                src = rng.choices(["signup_form", "template_gallery", "partner_link"], [0.8, 0.12, 0.08])[0]
                signups.append({
                    "signup_id": f"s{len(signups) + 1}", "workspace_id": wid, "company_id": cid,
                    "email_domain": "gmail.com" if personal else domain, "form_size": form_size,
                    "source_form": src, "last_touch": _pick(rng, LAST_TOUCH[ch]),
                    "self_report": _recall(rng, ch) if rng.random() < 0.55 else None,
                    "true_channel": ch})
    return companies, workspaces, signups, rng


def conversions(companies, workspaces, routed_companies, rng):
    """Paid conversion within 60 days. Self-serve conversion depends on usage; enterprise
    and large mid-market accounts mostly convert only if sales actually works them."""
    usage = {}
    for w in workspaces:
        usage[w["company_id"]] = usage.get(w["company_id"], 0) + w["actions_14d"]
    paid = {}
    for c in companies:
        u = usage.get(c["company_id"], 0)
        p_self = 1 / (1 + math.exp(-(math.log(u + 1) - 6.0) * 1.6)) * (0.5 if c["segment"] == "enterprise" else 0.8)
        p = p_self
        if c["company_id"] in routed_companies and c["segment"] in ("enterprise", "midmarket"):
            p = min(0.95, p_self + 0.35 * (1 if u > 400 else 0.4))
        paid[c["company_id"]] = rng.random() < p
    return paid, usage


def event_test(rng):
    """Weekly signups for 16 metros over 12 weeks; a stunt runs in 4 metros in weeks 7-8.
    A product launch lifts every metro from week 7 too (the confounder)."""
    metros = [f"metro_{i}" for i in range(16)]
    treated = set(metros[:4])
    rows, true_lift = [], 0
    for m in metros:
        base = rng.uniform(80, 220)
        for wk in range(1, 13):
            season = 1 + 0.02 * wk
            launch = 1.18 if wk >= 7 else 1.0
            stunt = 1.10 if (m in treated and wk in (7, 8)) else 1.0
            mean = base * season * launch * stunt
            y = rng.gauss(mean, mean * 0.04)
            if stunt > 1:
                true_lift += mean - mean / stunt
            rows.append({"metro": m, "week": wk, "treated": m in treated, "signups": y})
    return rows, true_lift


def agencies_usage(rng, n=220):
    """Daily actions for agency workspaces on the Growth plan in their first month after the change."""
    out = []
    for i in range(n):
        level = rng.lognormvariate(math.log(1250), 0.55)  # actions per day
        lumpy = [max(0, rng.gauss(level, level * 0.9)) * (6 if rng.random() < 0.06 else 1) for _ in range(30)]
        out.append({"agency": f"ag{i}", "daily": lumpy, "month_total": sum(lumpy)})
    return out
