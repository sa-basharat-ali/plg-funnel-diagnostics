# Funnel diagnostics for a product-led GTM platform

```
python3 run.py      # stdlib only, no install, under a second
```

3,000 companies, 6,390 workspaces, 12,890 signups, a 16-metro event test and 220 agency usage
curves. Generated with a fixed seed; no real company, person or campaign is represented. The
shape comes from public information about a GTM data platform with a free plan, unlimited seats,
usage metered in actions, and growth driven by creators, agencies and community.

---

## Six findings

### 1. With unlimited seats, "lead" has three grains

62% of companies have two or more workspaces; the median enterprise has 14 signups. Signup-to-paid
reads **28.0% counted per signup and 19.4% per company**. 17 companies cross the usage bar in total
but stay under it in every single workspace, so a per-workspace rule never routes them.

### 2. Usage predicts buying better than the form

Take the 1,097 companies whose form says 200+ employees, and the same number ranked by actions used
in their first 14 days. Paid rate: **29.8% by form, 42.1% by usage.** They overlap on 502; the form
misses 595 of the heaviest users.

### 3. One unmapped form drops 1,490 signups

Every signup should land in exactly one state. Counting them does it: sales 4,121, self-serve
5,449, nurture 1,830, **no state 1,490**. All 1,490 come from one form (the template gallery) that
routing never mapped, and 933 belong to mid-market or enterprise companies. Separately, 2,068
personal-email signups go to nurture, and 1,571 of them share a workspace with a work email and can
be resolved to their company.

### 4. Last-touch can't see the ecosystem

| channel | truth | last-touch | self-report |
|---|---|---|---|
| creator | 23.2% | 8.3% | 29.7% |
| agency | 9.3% | 0.0% | 6.5% |
| community | 13.0% | 0.0% | 12.7% |
| search | 16.7% | 21.7% | 16.8% |
| paid ads | 13.1% | 12.1% | 7.1% |
| event | 8.7% | 0.0% | 5.7% |
| direct / word of mouth | 16.1% | 57.9% | 21.7% |

Last-touch puts 57.9% into "direct" and gives agencies, community and events nothing. Self-report
is much closer, but only 55.5% answer it and it has its own bias: people who saw a LinkedIn ad say
"LinkedIn", so creators look 6.5 points bigger than they are and paid ads half their size. Neither
source is the answer alone; the useful number comes from reconciling the two with affiliate-link data.

### 5. A stunt's naive lift is mostly the product launch

A stunt ran in 4 of 16 metros for two weeks, the same weeks a product launch lifted every metro.
Pre/post in the stunt metros says **+38.7%**. Difference-in-differences against the 12 control
metros says **+8.2%**, against a true built-in lift of 10.0%.

### 6. Which agencies will hit the actions cap

On a 40,000-actions-a-month plan, 138 of 220 heavy agency workspaces (62.7%) will exceed it this
month. A straight run-rate calls it correctly for 76.8% of agencies on day 5, 83.2% on day 10 and
92.7% on day 20. Early in the month the call is a range, not a number, which is exactly when
customer success needs to reach out.

## What surprised me

I expected account-level routing to be the big win. Routing on combined usage per company sent 158
more accounts to sales and produced 7 more paid companies in 60 days. The unmapped form and the
usage score mattered far more.

## The part I got wrong

In the first version, self-reported attribution matched the truth almost exactly, because I had
written it as the truth plus missing answers. Real recall isn't like that. Adding the two most
common mix-ups (ads remembered as LinkedIn, events remembered as a colleague's tip) is what made
self-report useful but biased, and the reconciliation argument came out of that.

## Files

| | |
|---|---|
| `world.py` | companies, workspaces, signups, channels, the event test, agency usage |
| `run.py` | routing, scoring, leak reconciliation, attribution, incrementality, cap forecasting |

## Where this comes from

Through my own consulting practice I was the CEO's data person at a VC-backed computer vision
startup, where I found an 80% data loss that every dashboard reported as healthy. Before that I
spent two years at Geidea, Saudi Arabia's largest payments processor, on its executive strategy
team, where churn and revenue models behind a retention strategy cut merchant churn from 35% to
about 10%.

Syed Ahmed Basharat Ali · sabasharat.ali@gmail.com · basharat.net
