"""python3 run.py  -- stdlib only, about a second."""
import random
from collections import Counter, defaultdict

import world as W

companies, workspaces, signups, rng = W.build()
comp = {c["company_id"]: c for c in companies}
ws = {w["workspace_id"]: w for w in workspaces}
by_company = defaultdict(list)
for s in signups:
    by_company[s["company_id"]].append(s)


def pct(x):
    return f"{x * 100:.1f}%"


print("=" * 78)
print("Funnel diagnostics for a product-led GTM platform: synthetic world, real failure modes")
print("=" * 78)
print(f"companies {len(companies)} | workspaces {len(workspaces)} | signups {len(signups)}")

# ---- routing: what happens today vs an account-level rule ------------------------------------
MAPPED = {"signup_form", "partner_link"}  # the template gallery form was never mapped


def route_today(s):
    if s["source_form"] not in MAPPED:
        return "unrouted"
    personal = s["email_domain"] == "gmail.com"
    if (s["form_size"] == W.SIZE_ROUTE and not personal) or (ws[s["workspace_id"]]["actions_14d"] > W.PQL_ACTIONS and not personal):
        return "sales"
    if personal:
        return "nurture"
    return "self_serve"


state = {s["signup_id"]: route_today(s) for s in signups}
routed_today = {s["company_id"] for s in signups if state[s["signup_id"]] == "sales"}

usage = defaultdict(int)
for w in workspaces:
    usage[w["company_id"]] += w["actions_14d"]
routed_account = {cid for cid in comp if usage[cid] > W.PQL_ACTIONS or
                  any(s["form_size"] == W.SIZE_ROUTE and s["email_domain"] != "gmail.com" for s in by_company[cid])}

paid_today, _ = W.conversions(companies, workspaces, routed_today, random.Random(W.SEED + 1))
paid_acct, _ = W.conversions(companies, workspaces, routed_account, random.Random(W.SEED + 1))

# 1. grain -----------------------------------------------------------------------------------
print("\n1. WHAT IS A LEAD  (unlimited seats: one company, many signups)")
multi = sum(1 for c in comp if len({s['workspace_id'] for s in by_company[c]}) > 1)
print(f"   companies with 2+ workspaces: {multi} ({pct(multi / len(comp))}); enterprise median signups "
      f"{sorted(len(by_company[c]) for c in comp if comp[c]['segment'] == 'enterprise')[len([c for c in comp if comp[c]['segment'] == 'enterprise']) // 2]}")
paid_signups = sum(1 for s in signups if paid_today[s["company_id"]])
print(f"   'signup to paid' counted per signup: {pct(paid_signups / len(signups))} | per company: "
      f"{pct(sum(paid_today.values()) / len(comp))}")
hidden = [c for c in comp if c not in routed_today and comp[c]["segment"] in ("enterprise", "midmarket")
          and usage[c] > W.PQL_ACTIONS and max(ws[w]["actions_14d"] for w in {s["workspace_id"] for s in by_company[c]}) <= W.PQL_ACTIONS]
print(f"   accounts over the usage bar in total but under it in every single workspace: {len(hidden)} "
      f"(never routed today)")

# 2. scoring ---------------------------------------------------------------------------------
print("\n2. WHO IS READY TO BUY  (form fields vs usage)")
form_only = {c for c in comp if any(s["form_size"] == W.SIZE_ROUTE for s in by_company[c])}
top_use = set(sorted(comp, key=lambda c: -usage[c])[:len(form_only)])
rate = lambda S: sum(paid_acct[c] for c in S) / len(S)
print(f"   companies flagged by 'size 200+' on the form: {len(form_only)}, paid rate {pct(rate(form_only))}")
print(f"   same number of companies ranked by 14-day actions:   {len(top_use)}, paid rate {pct(rate(top_use))}")
lift_both = form_only & top_use
print(f"   overlap: {len(lift_both)}; the form misses {len(top_use - form_only)} high-usage companies")

# 3. leaks -----------------------------------------------------------------------------------
print("\n3. WHERE LEADS GO MISSING  (every signup should land in exactly one state)")
cnt = Counter(state.values())
print(f"   signups in: {len(signups)} | sales {cnt['sales']} | self-serve {cnt['self_serve']} | "
      f"nurture {cnt['nurture']} | no state {cnt['unrouted']}")
leak_big = sum(1 for s in signups if state[s["signup_id"]] == "unrouted" and comp[s["company_id"]]["segment"] in ("enterprise", "midmarket"))
print(f"   unrouted signups come from one unmapped form (template gallery); {leak_big} are mid-market or enterprise")
pers = [s for s in signups if s["email_domain"] == "gmail.com"]
pers_res = sum(1 for s in pers if any(o["email_domain"] != "gmail.com" for o in by_company[s["company_id"]]
                                      if o["workspace_id"] == s["workspace_id"]))
print(f"   personal-email signups sent to nurture: {len(pers)}; {pers_res} share a workspace with a work email "
      f"and can be resolved to a company")
print(f"   accounts sent to sales: {len(routed_today)} today vs {len(routed_account)} with an account-level rule")
gain = sum(paid_acct.values()) - sum(paid_today.values())
print(f"   paid companies in 60 days: {sum(paid_today.values())} today vs {sum(paid_acct.values())} account-level ({gain:+d})")

# 4. attribution -----------------------------------------------------------------------------
print("\n4. WHO GETS CREDIT  (ecosystem channels vs last-touch tracking)")
truth = Counter(s["true_channel"] for s in signups)
lt = Counter(s["last_touch"] for s in signups)
sr = Counter(s["self_report"] for s in signups if s["self_report"])
n, nsr = len(signups), sum(sr.values())
print(f"   {'channel':<16}{'truth':>8}{'last-touch':>12}{'self-report':>13}")
rows = [("creator", truth["creator"], lt["creator_link"], sr["LinkedIn"]),
        ("agency", truth["agency_referral"], 0, sr["Agency or consultant"]),
        ("community", truth["community"], 0, sr["Community / Slack"]),
        ("search", truth["seo"], lt["organic_search"], sr["Search"]),
        ("paid ads", truth["paid_ads"], lt["paid"], sr["Ad"]),
        ("event", truth["event"], 0, sr["Event"]),
        ("direct / WOM", truth["word_of_mouth"], lt["direct"], sr["Friend or colleague"])]
for name, t, l, r in rows:
    print(f"   {name:<16}{pct(t / n):>8}{pct(l / n):>12}{pct(r / nsr):>13}")
print(f"   answered the 'how did you hear' question: {pct(nsr / n)}")

# 5. incrementality --------------------------------------------------------------------------
print("\n5. DID THE STUNT WORK  (pre/post vs a control group)")
ev, true_lift = W.event_test(random.Random(W.SEED + 2))
def mean(xs): return sum(xs) / len(xs)
tr_pre = mean([r["signups"] for r in ev if r["treated"] and r["week"] <= 6])
tr_post = mean([r["signups"] for r in ev if r["treated"] and r["week"] in (7, 8)])
co_pre = mean([r["signups"] for r in ev if not r["treated"] and r["week"] <= 6])
co_post = mean([r["signups"] for r in ev if not r["treated"] and r["week"] in (7, 8)])
naive = tr_post / tr_pre - 1
did = (tr_post / tr_pre) / (co_post / co_pre) - 1
true_pct = true_lift / sum(r["signups"] for r in ev if r["treated"] and r["week"] in (7, 8))
print(f"   naive pre/post lift in stunt metros: {pct(naive)}")
print(f"   difference-in-differences vs 12 control metros: {pct(did)}  (true lift built in: 10.0%)")

# 6. pricing -----------------------------------------------------------------------------------
print("\n6. WHICH AGENCIES WILL HIT THE WALL  (actions metering, Growth plan 40,000 a month)")
ag = W.agencies_usage(random.Random(W.SEED + 3))
over = [a for a in ag if a["month_total"] > W.GROWTH_ACTIONS]
print(f"   agencies that will exceed the plan this month: {len(over)} of {len(ag)} ({pct(len(over) / len(ag))})")
for day in (5, 10, 15, 20):
    hit = sum(1 for a in ag if (sum(a["daily"][:day]) / day * 30 > W.GROWTH_ACTIONS) == (a["month_total"] > W.GROWTH_ACTIONS))
    print(f"   day {day:>2} run-rate calls it right for {pct(hit / len(ag))} of agencies")
