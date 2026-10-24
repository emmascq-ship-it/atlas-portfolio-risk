# Stress-loss reconciliation

The current default is a hypothetical instantaneous linear scenario, not a
realized historical market loss. Arithmetic is weight × explicit class shock:

| Asset | Weight | Shock | Portfolio contribution (percentage points) |
|---|---:|---:|---:|
| US Equity | 26% | -30% | -7.800 |
| Global Equity | 16% | -30% | -4.800 |
| Treasuries | 20% | +3.5% | +0.700 |
| Corp Bonds | 13% | +3.5% | +0.455 |
| Gold | 10% | +6% | +0.600 |
| REITs | 10% | -22% | -2.200 |
| Cash | 5% | 0% | 0.000 |
| **Total** | **100%** | | **-13.045** |

At $1,000,000 hypothetical notional this is -$130,450. A -12.5% loss would be
-$125,000, a difference of 0.545 percentage points (54.5 bps), or $5,450.
Rounding cannot explain the difference.

No archived portfolio, shock vector, dates or historical calculation supporting
12.5% was found in the supplied project. Its provenance is unresolved. A claim
that an earlier model used different assumptions is also unverified without those
inputs. No weights, shocks or financial models were changed to force a match.

Suggested truthful résumé wording: “Built a reproducible portfolio stress-testing
prototype; the documented hypothetical equity-selloff scenario modeled a 13.045%
loss under explicit portfolio weights and asset-class shocks.” Do not describe it
as realized performance, an independently validated forecast or a 12.5% result.

If the original 12.5% claim is retained, archive its input weights, instruments,
shock definitions or dated price interval, source provenance, formula, version
and reproducible calculation separately. The current default remains -13.045%.
