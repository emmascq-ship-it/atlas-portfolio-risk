"""Interactive portfolio risk intelligence dashboard (Streamlit)."""

import pandas as pd
import hashlib
import json
import streamlit as st
import plotly.graph_objects as go
from ui_style import CSS, style_chart, section_heading
from overview_style import OVERVIEW_CSS, overview_chart
from module_style import MODULE_CSS, module_chart
from html import escape
from model_benchmark import compare_var_models
from market_data import MARKET_TICKERS, download_etf_prices
from market_integrity import compare_adjusted_prices
from tiingo_reference import validate_tiingo_reference
from risk_brief import make_risk_brief
from factor_engine import factor_attribution, FACTOR_DESCRIPTIONS
from briefing_workflow import (
    approve_brief, approval_is_current, evidence_pack, evidence_digest,
    export_review_bundle, rules_based_draft,
    validate_draft_evidence,
)
from validation_extensions import (
    CLASSES, christoffersen_independence, combined_coverage_test, scenario_impact_custom,
)
from research_packet import generate_packet, packet_bytes, inputs_fingerprint
from risk_engine import (
    ASSETS, ASSET_CLASS, DEFAULT_WEIGHTS, SCENARIOS,
    component_volatility, generate_synthetic_prices, portfolio_returns,
    kupiec_unconditional_coverage, rolling_var_backtest, scenario_impact,
    summarize_risk, validate_prices,
)


@st.cache_data(ttl=3600, show_spinner="Downloading adjusted ETF prices…")
def load_market_prices(period):
    """Auditable Adj Close/action download, cache schema v2."""
    return download_etf_prices(period)


def section_header(title):
    st.markdown(section_heading(title), unsafe_allow_html=True)


st.set_page_config(page_title="ATLAS | Portfolio Risk Intelligence", page_icon="📊", layout="wide")
st.html(CSS + OVERVIEW_CSS + MODULE_CSS)
with st.container(key="atlas_legacy_header"):
    st.caption("Portfolio research · Risk surveillance · Model governance")
    st.title("ATLAS | Portfolio Risk Intelligence")
    st.caption("Transparent risk metrics with reproducible assumptions and human-controlled review. Research prototype; not investment advice.")

with st.sidebar:
    with st.container(key="overview_sidebar_brand"):
        st.markdown('<div class="overview-brand"><span class="overview-monogram">A</span><div><strong>ATLAS</strong><small>Portfolio intelligence</small></div></div>', unsafe_allow_html=True)
    with st.container(key="atlas_sidebar_controls"):
        with st.expander("Portfolio settings", expanded=False):
            st.header("Portfolio controls")
            data_source = st.radio("Data source", ["Synthetic demo", "Market ETF proxies", "Upload CSV"])
            if data_source == "Market ETF proxies":
                history = st.selectbox("Historical ETF lookback", ["3y", "5y", "10y"], index=1)
                reference_file = st.file_uploader("Independent adjusted-price reference (optional CSV)", type=['csv'],
                    help="Date plus the seven asset columns, full analysis interval, same USD dividend/split-adjusted convention.")
                reference_source = st.text_input("Independent reference provider / dataset", value="")
            elif data_source == "Upload CSV":
                uploaded = st.file_uploader("Upload historical prices (CSV)", type=["csv"], help="Date column plus seven named asset columns. Prices must be positive and complete.")
            confidence = st.select_slider("Confidence level", options=[.90, .95, .975, .99], value=.95, format_func=lambda v: f"{v:.1%}")
            window = st.selectbox("Backtest lookback", [250, 500], index=0)
            portfolio_value = st.number_input("Portfolio notional (USD)", min_value=10000, max_value=1000000000, value=1000000, step=100000)
            section_header("Target asset weights")
            raw = {a: st.number_input(a, min_value=0.0, max_value=100.0, value=float(DEFAULT_WEIGHTS[a] * 100), step=1.0, key=a) for a in ASSETS}
            st.caption("Weights must total 100%; no short selling in this model.")
    with st.container(key="atlas_scenario_controls"):
        with st.expander("Scenario controls", expanded=True):
            scenario = st.selectbox("Stress scenario", [*SCENARIOS, "Custom scenario"])
            if scenario == "Custom scenario":
                st.caption("Define simultaneous, instantaneous asset-class return shocks.")
                custom_shocks = {c: st.number_input(f"{c} shock (%)", min_value=-100.0, max_value=200.0,
                                                  value=0.0, step=1.0, key=f"shock_{c}") / 100 for c in CLASSES}
            else:
                custom_shocks = SCENARIOS[scenario].copy()

weights = pd.Series(raw) / 100
overview_header = st.container(key="atlas_overview_header")

source_details = None
reference_status = ""
if data_source == "Upload CSV":
    if uploaded is None:
        st.info("Upload a CSV with the seven asset price columns to run this mode.")
        st.stop()
    try:
        source = pd.read_csv(uploaded)
        if "Date" not in source.columns:
            raise ValueError("CSV must have a Date column")
        dates = pd.to_datetime(source.pop("Date"), errors="raise")
        prices = source.set_axis(dates)
        prices.index.name = "Date"
        if set(prices.columns) != set(ASSETS):
            raise ValueError("Required columns: " + ", ".join(ASSETS))
        prices = prices[ASSETS]
        source_details = f"User-supplied CSV · {len(prices)} price observations"
        st.success("Local CSV loaded. The app does not transmit this file to a market-data service.")
    except Exception as exc:
        st.error(f"Could not read price file: {exc}")
        st.stop()
elif data_source == "Market ETF proxies":
    try:
        prices, metadata = load_market_prices(history)
    except Exception as exc:
        st.error(f"ETF data unavailable: {exc}. Try again later or upload your own adjusted-price CSV.")
        st.stop()
    ticker_description = " · ".join(f"{asset}: {symbol}" for asset, symbol in MARKET_TICKERS.items())
    st.success(f"**Market-data mode** · {metadata['rows_used']:,} complete trading dates "
               f"({metadata['first_date']} to {metadata['last_date']}).")
    st.caption("Yahoo Finance via yfinance · split/dividend-adjusted USD ETF proxies. "
               "Data may be delayed or revised; third-party data quality and usage restrictions apply.")
    st.warning("Independent market-data verification is incomplete. Provider checks do not establish price accuracy or usage rights.")
    with st.expander("Optional Tiingo $0 Starter independent check (private use only)"):
        st.caption("No signup, upgrade, payment or subscription is performed. Seven EOD requests maximum per click, "
                   "no retries. Use only an existing $0 Starter account. Provider data are not included in the public demo.")
        tiingo_token = st.text_input("Tiingo Starter API token", type='password')
        free_confirmed = st.checkbox("I am using a $0 Tiingo Starter account and will not incur charges.")
        reference_key = hashlib.sha256((prices.to_csv(float_format='%.17g') +
            json.dumps(metadata.get('corporate_actions', []), sort_keys=True)).encode()).hexdigest()
        if st.button("Run free independent check", disabled=not (tiingo_token.strip() and free_confirmed)):
            result = validate_tiingo_reference(prices, metadata, tiingo_token, confirm_free_starter=free_confirmed)
            st.session_state.tiingo_result = (reference_key, result)
        cached_reference = st.session_state.get('tiingo_result')
        tiingo_result = (cached_reference[1] if cached_reference and cached_reference[0] == reference_key
                         else {'status':'PENDING', 'reason':'Optional free reference not configured or not checked for these prices/actions'})
        if tiingo_result['status'] == 'FAILED':
            st.error("Independent market-data check FAILED: " + tiingo_result['reason'])
            st.stop()
        elif tiingo_result['status'] == 'PENDING':
            st.info("Live independent validation: PENDING. " + tiingo_result['reason'])
            reference_status = '; independent validation PENDING'
        else:
            st.success("Tiingo reference price/action checks passed for this private snapshot; no certification implied.")
            reference_status = '; Tiingo Starter EOD adjusted-return and corporate-action reference checks passed'
    if reference_file is not None:
        try:
            reference = pd.read_csv(reference_file)
            reference.index = pd.to_datetime(reference.pop('Date'), errors='raise')
            result = compare_adjusted_prices(prices, reference, reference_source)
            reference_status = (f"; reference adjusted returns matched {result['reference_source']} "
                                f"(CSV SHA-256 {hashlib.sha256(reference_file.getvalue()).hexdigest()}); "
                                "independent corporate-action review remains required")
            st.success(f"Independent reference adjusted returns match within {result['tolerance_bps']} bps. Corporate actions require separate review.")
        except Exception as exc:
            st.error(f"Independent market-data check failed: {exc}")
            st.stop()
    with st.expander("ETF proxies and data-quality review"):
        st.write(ticker_description)
        st.write(f"Downloaded trading dates: **{metadata['rows_received']}** · "
                 f"Current/incomplete trading dates excluded: **{metadata['rows_excluded_pending_session']}** · "
                 f"Rows discarded due to at least one missing ETF price: **{metadata['rows_dropped_missing']}** · "
                 f"Complete dates used: **{metadata['rows_used']}**.")
        st.caption("The current trading date is excluded even if a provisional quote exists. Missing observations "
                   "are excluded, never forward-filled. BIL is a Treasury-bill ETF, not uninvested cash.")
        st.write(metadata.get('provider_adjustment_check', 'Provider action audit unavailable'))
        st.write(f"Dividend events checked: {metadata.get('dividend_events_checked', 'unavailable')}; "
                 f"dropped dates: {metadata.get('dates_dropped_missing', [])}")
else:
    prices = generate_synthetic_prices()
    with st.container(key="overview_legacy_synthetic_notice"):
        st.warning("**DEMONSTRATION DATA** — Synthetic, reproducible prices. Results are illustrative, not estimates from actual market history.")

checks = validate_prices(prices, weights, min_history=max(window + 1, 261))
with st.container(key="overview_legacy_validation"):
    with st.expander("Eight automated input-validation controls", expanded=not all(checks.values())):
        for label, ok in checks.items():
            st.write(("✅ " if ok else "❌ ") + label)

if not all(checks.values()):
    st.error("Please resolve validation errors before running analytics.")
    st.stop()

returns = portfolio_returns(prices, weights)
if len(returns) <= window:
    st.error(f"Requires more than {window} daily return observations.")
    st.stop()

factor = factor_attribution(prices, weights)
risk = summarize_risk(returns, confidence)
backtest = rolling_var_backtest(returns, window, confidence)
comparison = compare_var_models(returns, window=window, confidence=confidence)
breaches = int(backtest["Breach"].sum())
expected = len(backtest) * (1 - confidence)
coverage = kupiec_unconditional_coverage(backtest, confidence)
portfolio_shock, shock_by_asset = scenario_impact_custom(weights, custom_shocks)
independence = christoffersen_independence(backtest)
conditional_lr, conditional_p = combined_coverage_test(coverage.likelihood_ratio, independence.likelihood_ratio)
source_label = ("Synthetic demonstration — NOT market observations" if data_source == "Synthetic demo"
                else "Yahoo Finance ETF adjusted daily proxies" if data_source == "Market ETF proxies"
                else "User-uploaded historical price CSV")
source_label += reference_status
input_sha = inputs_fingerprint(prices, weights, confidence, window, portfolio_value,
                               scenario, custom_shocks, source_label)

packet = generate_packet(prices, weights, confidence=confidence, window=window,
                         notional=portfolio_value, scenario_label=scenario,
                         class_shocks=custom_shocks, source_label=source_label)

with overview_header:
    if data_source == "Synthetic demo":
        disclosure = '<strong>DEMONSTRATION DATA</strong> — Synthetic, reproducible prices. Results are illustrative, not estimates from actual market history.'
    else:
        disclosure = escape(source_label) + '. Research only; source accuracy requires independent review.'
    st.markdown(
        '<div class="overview-topbar"><div class="overview-topline"><div><span class="overview-workspace">ATLAS / Research workspace</span><h1 class="atlas-module-title atlas-title-1">Portfolio overview</h1><h1 class="atlas-module-title atlas-title-2">Factor exposures</h1><h1 class="atlas-module-title atlas-title-3">Scenario lab</h1><h1 class="atlas-module-title atlas-title-4">Model validation</h1><h1 class="atlas-module-title atlas-title-5">Review desk</h1></div>'
        '<div class="overview-source"><span class="overview-source-dot"></span>' + escape(data_source) + '<small>Research only · USD</small></div></div>'
        '<div class="overview-disclosure" role="note">' + disclosure + '</div>'
        '<div class="overview-metadata"><span>' + f'{prices.index.min():%d %b %Y} – {prices.index.max():%d %b %Y}' + '</span><span>'
        + f'{len(prices):,} price dates / {len(returns):,} daily returns' + '</span><span>' + f'{sum(checks.values())} / {len(checks)} input checks passed'
        + '</span></div></div>', unsafe_allow_html=True)
with st.container(key="overview_legacy_metadata"):
    st.caption(f"{data_source} · USD · {prices.index.min():%Y-%m-%d} to {prices.index.max():%Y-%m-%d} · "
               f"{len(prices):,} complete price dates · {len(returns):,} daily returns")

# Dashboard panels use the same immutable-at-render inputs and evidence snapshot.
overview_tab, factors_tab, scenario_tab, validation_tab, review_tab = st.tabs(
    ["01 / Overview", "02 / Factor exposures", "03 / Scenario lab", "04 / Model validation", "05 / Review desk"]
)

with overview_tab:
    with st.container(key="overview_kpis"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("1-day Historical VaR", f"{risk.var:.2%}")
        c2.metric("1-day Expected Shortfall", f"{risk.es:.2%}")
        c3.metric("Annualized Volatility", f"{risk.annualized_vol:.2%}")
        c4.metric("Maximum Drawdown", f"{risk.max_drawdown:.2%}")
    with st.container(key="overview_context"):
        st.text(f"Illustrative portfolio: ${portfolio_value:,.0f} USD  |  "
                f"1-day VaR: ${risk.var * portfolio_value:,.0f}  |  "
                f"1-day ES: ${risk.es * portfolio_value:,.0f}")
        st.caption(f"{confidence:.1%} confidence · constant weights, daily rebalancing · 252 sessions/year. "
                   "Positive VaR and ES measure loss size, not guaranteed limits.")
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with st.container(key="overview_primary_chart"):
            st.subheader("21-day rolling volatility")
            st.caption("Annualized portfolio volatility (%) · daily observations")
            rolling_vol = returns.rolling(21).std() * (252 ** 0.5)
            fig = go.Figure(go.Scatter(x=rolling_vol.index, y=rolling_vol*100, mode="lines",
                                       line=dict(color="#377cf6", width=2.5),
                                       fill="tozeroy", fillcolor="rgba(55,124,246,0.07)",
                                       hovertemplate="%{x|%Y-%m-%d}<br>Volatility: %{y:.2f}%<extra></extra>"))
            fig.update_layout(yaxis_title="Annualized volatility (%)", height=285,
                              margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(overview_chart(fig), width="stretch", theme=None)
    with right:
        with st.container(key="overview_contribution_chart"):
            st.subheader("Risk contribution")
            st.caption("Euler decomposition · annualized percentage points")
            contrib = component_volatility(prices, weights)
            fig = go.Figure(go.Bar(x=contrib.values * 100, y=contrib.index,
                                   orientation="h", marker_color=["#b44e50" if v < 0 else "#377cf6" for v in contrib],
                                   hovertemplate="%{y}<br>%{x:.3f} pp<extra></extra>"))
            fig.update_layout(xaxis_title="Contribution (pp)",
                              yaxis=dict(autorange="reversed"), height=285,
                              margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(overview_chart(fig), width="stretch", theme=None)
    st.caption("Euler contributions can be negative; they sum to annualized portfolio volatility.")
    with st.container(key="overview_holdings"):
        st.subheader("Portfolio holdings & exposures")
        st.caption("Target-weight model portfolio. USD exposures use the hypothetical notional; these are not custody positions.")
        holdings = pd.DataFrame({
            "Asset": weights.index,
            "Asset class": [ASSET_CLASS[a] for a in weights.index],
            "Target weight (%)": weights.values * 100,
            "Hypothetical exposure (USD)": weights.values * portfolio_value,
            "Volatility contribution (pp)": contrib.reindex(weights.index).values * 100,
        })
        st.dataframe(holdings, hide_index=True, width="stretch", column_config={
            "Target weight (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Hypothetical exposure (USD)": st.column_config.NumberColumn(format="$%,.0f"),
            "Volatility contribution (pp)": st.column_config.NumberColumn(format="%.3f"),
        })
    with st.expander("Allocation and cumulative growth"):
        left, right = st.columns([1.45, 1])
        with left:
            section_header("Historical $1 growth")
            growth = (1 + returns).cumprod()
            fig = go.Figure(go.Scatter(x=growth.index, y=growth, mode="lines", line=dict(color="#237d73", width=2)))
            fig.update_layout(yaxis_title="Growth of $1", height=335, margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(style_chart(fig), width="stretch", theme=None)
        with right:
            section_header("Asset allocation")
            fig = go.Figure(go.Bar(x=(weights * 100), y=weights.index, orientation="h", marker_color="#496b85"))
            fig.update_layout(xaxis_title="Target weight (%)", yaxis=dict(autorange="reversed"),
                              height=335, margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(style_chart(fig), width="stretch", theme=None)
    with st.expander("Eight automated input-validation controls"):
        for label, ok in checks.items():
            st.write(("✅ " if ok else "❌ ") + label)
    st.caption(f"Input fingerprint · {input_sha[:16]}… · {len(prices):,} complete price dates")

with factors_tab:
    st.caption("Descriptive OLS regression of daily portfolio returns on five ETF-spread factors; "
               "these are practical proxies, not isolated structural risk factors or causal exposures.")
    with st.container(key="atlas_kpis_factors"):
        c1, c2, c3 = st.columns(3)
        c1.metric("OLS R²", f"{factor.r_squared:.1%}")
        c2.metric("Fitted factor volatility", f"{factor.fitted_annualized_vol:.2%}")
        c3.metric("Unexplained residual volatility", f"{factor.residual_annualized_vol:.2%}")
    left, right = st.columns(2)
    with left:
        with st.container(key="atlas_panel_factor_beta"):
            st.subheader("Factor sensitivity")
            st.caption("OLS beta · descriptive ETF-spread exposures")
            fig = go.Figure(go.Bar(x=factor.betas.values, y=factor.betas.index, orientation="h",
                                   marker_color="#377cf6", hovertemplate="%{y}<br>Beta: %{x:+.3f}<extra></extra>"))
            fig.update_layout(height=315, xaxis_title="OLS beta", yaxis=dict(autorange="reversed"),
                              margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(module_chart(fig), width="stretch", theme=None)
    with right:
        with st.container(key="atlas_panel_factor_variance"):
            st.subheader("Fitted variance attribution")
            st.caption("Annualized return²/year · may include negative covariance terms")
            values = factor.fitted_variance_contributions
            fig = go.Figure(go.Bar(x=values.values, y=values.index, orientation="h", marker_color="#7186b6",
                                   hovertemplate="%{y}<br>%{x:+.5f} return²/year<extra></extra>"))
            fig.update_layout(height=315, xaxis_title="Contribution (return²/year)", yaxis=dict(autorange="reversed"),
                              margin=dict(l=5,r=5,t=12,b=10))
            st.plotly_chart(module_chart(fig), width="stretch", theme=None)
            st.caption("These contributions sum to fitted variance, NOT to portfolio volatility; negative contributions reflect covariance.")
    with st.container(key="atlas_panel_factor_correlation"):
        st.subheader("Cross-asset correlation")
        st.caption("Aligned daily asset returns · Pearson correlation (−1 to +1).")
        correlation = prices[ASSETS].pct_change().dropna().corr()
        fig = go.Figure(go.Heatmap(z=correlation.values, x=correlation.columns, y=correlation.index,
                                  zmin=-1, zmax=1, zmid=0,
                                  colorscale=[[0,"#7186b6"],[.5,"#f4f6fa"],[1,"#377cf6"]],
                                  texttemplate="%{z:.2f}", textfont=dict(size=10),
                                  colorbar=dict(title="ρ", thickness=10, len=.8),
                                  hovertemplate="%{y} / %{x}<br>Correlation: %{z:.3f}<extra></extra>"))
        fig.update_layout(height=340, margin=dict(l=5,r=5,t=12,b=10))
        module_chart(fig)
        fig.update_xaxes(tickmode="array", tickvals=list(correlation.columns), tickangle=-30)
        fig.update_yaxes(tickmode="array", tickvals=list(correlation.index), autorange="reversed")
        st.plotly_chart(fig, width="stretch", theme=None)
        st.caption("Correlation is descriptive co-movement, not a forecast, causal estimate or diversification guarantee.")
        with st.expander("Exact correlation values"):
            st.dataframe(correlation.style.format("{:.3f}"), width="stretch")
    with st.container(key="atlas_panel_factor_methodology"):
        st.subheader("Methodology & exact estimates")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Estimated factor betas**")
            st.dataframe(factor.betas.to_frame("OLS beta").style.format({"OLS beta": "{:+.3f}"}), width="stretch")
        with col2:
            st.markdown("**Factor contribution to fitted annualized variance**")
            st.dataframe(factor.fitted_variance_contributions.to_frame("Contribution (return²/year)")
                         .style.format({"Contribution (return²/year)": "{:+.5f}"}), width="stretch")
        with st.expander("Factor construction and regression diagnostics", expanded=True):
            st.dataframe(pd.Series(FACTOR_DESCRIPTIONS, name="ETF-spread definition"))
            st.write(f"**Aligned observations:** {factor.observations} · "
                     f"**Daily intercept:** {factor.intercept_daily:+.5%} · "
                     f"**Design matrix condition number:** {factor.condition_number:,.1f}")
            st.caption("Spread factors share underlying ETFs and may exhibit multicollinearity; "
                       "regression betas can change with sample window, asset mix, and instrument selection. "
                       "The model has no independent macroeconomic factor data or econometric standard-error claims.")
        st.download_button("Export factor exposures (CSV)",
                           factor.betas.to_csv(header=True).encode("utf-8"),
                           "factor_exposures.csv", mime="text/csv")

with scenario_tab:
    st.caption("Use Scenario controls in the sidebar to choose a preset or enter custom class shocks. "
               "Losses are deterministic linear shocks applied to target weights, not Monte Carlo simulations or estimates of scenario likelihood.")
    with st.container(key="atlas_kpis_scenario_loss" if portfolio_shock < 0 else "atlas_kpis_scenario_gain"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Scenario P&L", f"{portfolio_shock:+.3%}")
        c2.metric("USD impact", f"${portfolio_shock * portfolio_value:+,.0f}")
        c3.metric("Largest absolute driver", shock_by_asset.abs().idxmax())
    left, right = st.columns([3, 2])
    with left:
        with st.container(key="atlas_panel_scenario_attribution"):
            st.subheader("Loss attribution")
            st.caption("P&L contribution by asset · percentage points")
            ordered = shock_by_asset.sort_values()
            fig = go.Figure(go.Bar(x=ordered*100, y=ordered.index, orientation="h",
                marker_color=["#b44e50" if value < 0 else "#377cf6" for value in ordered]))
            fig.add_vline(x=0, line_width=1, line_color="#9aaab3")
            fig.update_layout(xaxis_title="Impact on portfolio return (pp)", height=320,
                              margin=dict(l=5,r=5,t=12,b=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(module_chart(fig), width="stretch", theme=None)
    with right:
        with st.container(key="atlas_panel_scenario_assumptions"):
            st.subheader("Scenario assumptions")
            st.caption(f"Selected: {scenario} · instantaneous class-level return shocks")
            assumptions = pd.Series(custom_shocks, name="Shock")
            st.dataframe(assumptions.to_frame().style.format({"Shock":"{:+.1%}"}), width="stretch")
            st.info("Hypothetical assumptions. No scenario probability or forecast is assigned.")
    with st.container(key="atlas_panel_scenario_comparison"):
        st.subheader("Preset comparison")
        st.caption("Illustrative presets at the current portfolio weights. This comparison does not alter the selected scenario.")
        preset_returns = pd.Series({name:scenario_impact_custom(weights, shocks)[0] for name, shocks in SCENARIOS.items()})
        fig = go.Figure(go.Bar(x=preset_returns.values*100, y=preset_returns.index, orientation="h",
                               marker_color=["#b44e50" if v < 0 else "#377cf6" for v in preset_returns],
                               hovertemplate="%{y}<br>Portfolio return: %{x:+.3f}%<extra></extra>"))
        fig.update_layout(height=220, xaxis_title="Hypothetical portfolio return (%)", yaxis=dict(autorange="reversed"),
                          margin=dict(l=5,r=5,t=12,b=10))
        st.plotly_chart(module_chart(fig), width="stretch", theme=None)
    with st.container(key="atlas_panel_scenario_details"):
        st.subheader("Asset-level exposure and modeled P&L")
        contribution_table = pd.DataFrame({"Asset class":pd.Series(ASSET_CLASS),
            "Weight":weights, "Assumed return":pd.Series({a:custom_shocks[ASSET_CLASS[a]] for a in ASSETS}),
            "Portfolio impact":shock_by_asset, "USD P&L":shock_by_asset*portfolio_value})
        st.dataframe(contribution_table.style.format({"Weight":"{:.1%}",
            "Assumed return":"{:+.1%}","Portfolio impact":"{:+.2%}","USD P&L":"${:+,.0f}"}), width="stretch")
        st.download_button("Download scenario research packet (JSON)", packet_bytes(packet),
                           file_name="portfolio_risk_research_UNAPPROVED.json", mime="application/json")
        st.caption("Same unapproved research packet and provenance as the shared report export; no analyst sign-off is implied.")
    st.info("All scenario inputs are explicit and editable. These hypothetical asset-class shocks do not estimate likelihood or future losses.")

with validation_tab:
    st.caption("Matched-window forecasts, historical coverage and exception diagnostics. Approximate tests do not establish model validity.")
    matched = comparison["backtest"]
    latest = matched.iloc[-1]
    with st.container(key="atlas_kpis_validation_forecasts"):
        hist_col, gauss_col = st.columns(2)
        hist_col.metric("Latest Historical VaR forecast", f"{latest['Historical VaR']:.3%}")
        gauss_col.metric("Latest Gaussian VaR forecast", f"{latest['Gaussian VaR']:.3%}")
    st.caption(f"Forecast for {matched.index[-1]:%Y-%m-%d}, using only the preceding {window} returns at {confidence:.1%} confidence. "
               "These trailing-window forecasts differ from the full-history overview estimates.")
    with st.container(key="atlas_panel_validation_forecasts"):
        st.subheader("Historical vs Gaussian VaR")
        st.caption("One-day forecasts from the same prior observation window · % of portfolio value")
        fig = go.Figure()
        for column, color, dash in [("Historical VaR", "#377cf6", "solid"), ("Gaussian VaR", "#8174b9", "dash")]:
            fig.add_trace(go.Scatter(x=matched.index, y=matched[column]*100, name=column,
                                     mode="lines", line=dict(color=color, dash=dash, width=2)))
        fig.update_layout(height=290, yaxis_title="Forecast loss (%)", margin=dict(l=5,r=5,t=45,b=10))
        st.plotly_chart(module_chart(fig), width="stretch", theme=None)
    comparison_table = pd.DataFrame(comparison['models']).T[
        ['observations','breaches','observed_breach_rate','kupiec_p_approx','mean_breach_excess','worst_breach_excess']]
    comparison_table.index = ['Historical simulation','Gaussian mean / variance']
    with st.container(key="atlas_panel_validation_comparison"):
        st.subheader("Model comparison & tail diagnostics")
        st.dataframe(comparison_table.style.format({'observations':'{:.0f}','breaches':'{:.0f}',
            'observed_breach_rate':'{:.2%}','kupiec_p_approx':'{:.3f}',
            'mean_breach_excess':'{:.3%}','worst_breach_excess':'{:.3%}'}), width='stretch',
            column_config={
                'observations':st.column_config.Column('Forecasts'),
                'breaches':st.column_config.Column('Breaches'),
                'observed_breach_rate':st.column_config.Column('Breach rate'),
                'kupiec_p_approx':st.column_config.Column('Kupiec p-value'),
                'mean_breach_excess':st.column_config.Column('Mean excess loss'),
                'worst_breach_excess':st.column_config.Column('Worst excess loss'),
            })
        st.caption("Breach rate and excess loss are fractions of portfolio value; p-values are approximate, not proof of validity.")
        for name, diagnostics in comparison['models'].items():
            for warning in diagnostics['warnings']:
                st.warning(f"{name.title()}: {warning}")
        st.download_button("Export Historical / Gaussian comparison (CSV)", matched.to_csv(index_label='Date').encode(),
                           'var_model_comparison.csv', mime='text/csv')
    with st.container(key="atlas_panel_validation_backtest"):
        st.subheader(f"Out-of-sample {window}-observation historical VaR backtest")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=backtest.index, y=backtest["Actual loss"] * 100, mode="lines",
                                 name="Actual daily loss (%)", line=dict(color="#66808e")))
        fig.add_trace(go.Scatter(x=backtest.index, y=backtest["VaR forecast"] * 100, mode="lines",
                                 name="Prior-window VaR (%)", line=dict(color="#377cf6")))
        fail = backtest[backtest.Breach]
        fig.add_trace(go.Scatter(x=fail.index, y=fail["Actual loss"] * 100, mode="markers",
                                 name="VaR breach", marker=dict(color="#b84851", size=7)))
        fig.update_layout(yaxis_title="Loss (%)", height=330, margin=dict(l=5,r=5,t=12,b=10))
        st.plotly_chart(module_chart(fig), width="stretch", theme=None)
    with st.container(key="atlas_kpis_validation_coverage"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Realized exceptions", f"{coverage.breaches} / {coverage.observations}")
        c2.metric("Expected exceptions", f"{coverage.expected_breaches:.1f}")
        c3.metric("Kupiec LRuc", f"{coverage.likelihood_ratio:.3f}")
        c4.metric("Approximate p-value", f"{coverage.p_value:.3f}")
    if coverage.expected_breaches < 10:
        st.warning("Fewer than 10 expected exceptions: the asymptotic p-value may be unreliable.")
    if coverage.p_value < .05:
        st.error("Observed exception frequency is inconsistent with nominal coverage under the approximate Kupiec test.")
    else:
        st.info("The test does not reject nominal exception frequency. This is NOT proof the model is valid.")
    st.subheader("Exception clustering / conditional coverage")
    with st.container(key="atlas_kpis_validation_independence"):
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Christoffersen LRind", f"{independence.likelihood_ratio:.3f}")
        d2.metric("Independence p-value", f"{independence.p_value:.3f}")
        d3.metric("Conditional coverage LRcc", f"{conditional_lr:.3f}")
        d4.metric("Combined p-value", f"{conditional_p:.3f}")
    st.write(f"**Transition counts:** n00={independence.n00}, n01={independence.n01}, "
             f"n10={independence.n10}, n11={independence.n11}.")
    if independence.warning:
        st.warning(independence.warning)
    if independence.p_value < .05 or conditional_p < .05:
        st.warning("At least one approximate exception-independence or conditional-coverage test rejects at 5%.")
    else:
        st.info("No rejection at 5% does NOT demonstrate independence or validate the risk model.")
    st.caption("Day t VaR uses only prior observations (no look-ahead). LRuc assesses unconditional coverage; "
               "LRind tests first-order exception dependence; LRcc sums both LR statistics. "
               "Sparse exceptions weaken chi-square approximations.")
    st.download_button("Export rolling backtest (CSV)", backtest.to_csv().encode("utf-8"),
                       "var_backtest.csv", mime="text/csv")

with review_tab:

    contrib = component_volatility(prices, weights)
    evidence = evidence_pack(risk, coverage, factor, weights, scenario, portfolio_shock,
                             portfolio_value, confidence, source_label,
                             prices.index.min().date().isoformat(), prices.index.max().date().isoformat(), window,
                             input_digest=input_sha)
    digest = evidence_digest(evidence)
    st.caption("Traceable evidence IDs; offline drafting with external AI disabled for the $0 project. "
               "Citation IDs do not fact-check claims. Every input change revokes prior sign-off.")
    mode = "Rule-based evidence brief (offline)"
    st.info("$0 mode: deterministic evidence brief only. External AI API requests are disabled.")
    if "brief_snapshot" not in st.session_state:
        st.session_state.brief_snapshot = {}
    snapshot = st.session_state.brief_snapshot
    # Input changes invalidate the prior draft and any sign-off; no stale approval exports.
    if snapshot.get("digest") != digest:
        st.session_state.brief_snapshot = {"digest": digest,
                                           "draft": rules_based_draft(evidence),
                                           "method": "Rule-based, not generative AI", "approval": None}
        snapshot = st.session_state.brief_snapshot
        st.session_state.current_draft = snapshot["draft"]
    if mode == "Rule-based evidence brief (offline)" and snapshot["method"] != "Rule-based, not generative AI":
        if st.button("Reset to verified rule-based draft"):
            snapshot.update(draft=rules_based_draft(evidence), method="Rule-based, not generative AI", approval=None)
            st.session_state.current_draft = snapshot["draft"]
    report_col, review_col = st.columns([3, 2])
    with report_col:
        with st.container(key="atlas_panel_review_report"):
            st.subheader("1 · Draft report")
            st.caption(f"{snapshot['method']} · Preview and exports use the same draft.")
            report_mode = st.radio("Report mode", ["Preview", "Edit Draft"], horizontal=True,
                                   key="review_report_mode")
            if report_mode == "Edit Draft":
                # The snapshot survives widget cleanup when the editor is unmounted.
                # Commit edits in the callback before a mode-switch reruns the app.
                def save_draft_edit():
                    current = st.session_state.brief_snapshot
                    edited = st.session_state.current_draft
                    if edited != current["draft"]:
                        current.update(draft=edited, approval=None)

                st.session_state.current_draft = snapshot["draft"]
                st.text_area("Editable draft — edits revoke prior approvals", height=480,
                             key="current_draft", on_change=save_draft_edit)
            else:
                with st.container(key="atlas_report_preview"):
                    # Currency is prose, not inline LaTeX. Only the display is escaped;
                    # the exact draft remains unchanged for hashing and exports.
                    st.markdown(snapshot["draft"].replace("$", r"\$"))
            issues = validate_draft_evidence(snapshot["draft"], evidence)
            if issues:
                st.warning("Citation gate flagged: " + "; ".join(issues))
            else:
                st.info("Evidence references are present. This checks reference IDs only; it does not validate financial claims. Human review remains mandatory.")
            st.download_button("Download unapproved draft (Markdown)", snapshot["draft"].encode(),
                               file_name="risk_brief_DRAFT.md", mime="text/markdown")
    with review_col:
        with st.container(key="atlas_panel_review_controls"):
            approval_status_panel = st.container(key="atlas_review_status")
            st.subheader("2 · Evidence review")
            st.caption("Compare every claim with the calculations, assumptions and source provenance. Reference checks are not a financial audit.")
            with st.expander("View exact evidence inventory and provenance"):
                for eid, fact in evidence["observations"].items():
                    st.markdown(f"**{eid}** · {fact}")
                st.caption("Evidence snapshot · SHA-256")
                st.code(digest, language=None)
            st.subheader("3 · Analyst approval")
            st.caption("Review the report and exact evidence before acknowledging the claims.")
            reviewer = st.text_input("Reviewer / analyst identifier", placeholder="Your name")
            confirmed = st.checkbox("I reviewed the calculations, assumptions, source labels, and all draft claims.")
            if st.button("Approve current evidence-linked draft", type="primary", disabled=bool(issues) or not confirmed or not reviewer.strip()):
                try:
                    snapshot["approval"] = approve_brief(snapshot["draft"], evidence, reviewer, confirmed)
                    st.success("Analyst approval recorded for this exact draft and evidence snapshot.")
                except Exception as exc:
                    st.error(f"Cannot approve: {exc}")
            with approval_status_panel:
                approval = snapshot.get("approval")
                if approval and approval_is_current(approval, snapshot["draft"], evidence):
                    st.success(f"**ANALYST APPROVED** — {approval.reviewer} · {approval.timestamp_utc}")
                    st.download_button("Export approved audit bundle (JSON)",
                                       export_review_bundle(snapshot["draft"], evidence, approval),
                                       file_name="risk_review_APPROVED.json", mime="application/json")
                else:
                    st.info("Status: UNAPPROVED. Approvals are tied to a SHA-256 hash of the draft and evidence; "
                               "editing or changing inputs revokes them. In-session workflow only, not enterprise authentication.")
                    st.download_button("Export evidence and draft (UNAPPROVED JSON)",
                                       export_review_bundle(snapshot["draft"], evidence, None),
                                       file_name="risk_review_UNAPPROVED.json", mime="application/json")

st.divider()
section_header("Reproducible research packet")
st.caption("Exports machine-readable source and assumption metadata, exact portfolio weights and class shocks, "
           "risk diagnostics, test limitations, and SHA-256 input fingerprint. No implicit analyst approval.")
st.download_button("Download research packet (JSON)", packet_bytes(packet),
                   file_name="portfolio_risk_research_UNAPPROVED.json", mime="application/json")
st.download_button("Download analyzed prices (CSV)", prices.to_csv(index_label="Date").encode(),
                   file_name="portfolio_prices.csv", mime="text/csv")
st.caption("Research prototype · Third-party daily ETF proxies or synthetic data · "
           "Not suitable for execution decisions or regulatory capital; all conclusions require professional review.")
