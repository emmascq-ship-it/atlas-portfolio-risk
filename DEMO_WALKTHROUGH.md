# 90-second technical interview walkthrough

Use the local Streamlit app in Synthetic demo mode. Approximate timing; do not
rush the explicit approval step. The static Pages demo has a different review scope.

**0–15 seconds · Problem and scope**
“ATLAS connects portfolio risk calculations with transparent reporting and human
review. This is a reproducible synthetic seven-asset, USD one-million portfolio,
not a claim about investment returns. Python computes the analytics; Streamlit
and an offline HTML snapshot make the results inspectable.”

**15–30 · Overview**
“Historical VaR and Expected Shortfall describe one-day tail losses. Volatility,
drawdown and asset contributions show complementary risks. Source labels, dates
and assumptions remain visible, and exports retain the exact unrounded snapshot.”

**30–45 · Factors and scenarios**
“These OLS exposures are descriptive ETF-spread proxies, not causal macro factors.
The documented equity-selloff scenario implies minus 13.045 percent. Changing a
shock changes hypothetical P&L, not historical returns or archived VaR.”

**45–60 · Validation**
“Historical and Gaussian VaR use matched trailing windows with no target-day
look-ahead. This fixture has 31 and 30 breaches across 649 forecasts. Coverage
and clustering diagnostics expose weaknesses; a non-rejection is not validation.”

**60–80 · Review Desk**
“Preview is read-only; Edit Draft is separate. A named reviewer must explicitly
acknowledge the claims. Approval binds exact draft and evidence hashes. Here I
approve the synthetic report, then edit it to revoke approval. Reference IDs make
claims traceable; they do not prove truth or authenticate identity.”

**80–90 · Engineering judgment**
“The verified release has 134 Python tests plus static and Streamlit Chromium E2E.
I froze the models, pinned dependencies and kept the public demo synthetic-only.
Independent live-data validation remains optional and pending; nothing here claims
production governance or a verified investment track record.”
