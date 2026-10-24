"""ATLAS presentation tokens; no analytics or external font dependencies."""
CSS = """
<style>
:root { --atlas-ink:#26343b; --atlas-muted:#596971; --atlas-line:#dce1df; }
.block-container { max-width:1400px; padding-top:5rem; padding-bottom:3rem; }
h1,h2,h3 { color:var(--atlas-ink); letter-spacing:-.035em; line-height:1.2; }
[data-testid="stMain"] h1 { font-size:2.35rem; font-weight:750; margin-bottom:.45rem; }
[data-testid="stMain"] h3 { font-size:1.15rem; margin-top:.4rem; }
[data-testid="stMain"] p { max-width:80ch; }
[data-testid="stMetricLabel"] p { font-size:.85rem; line-height:1.4; }
[data-testid="stMetricValue"] { font-size:clamp(1.6rem,2.5vw,2.2rem); }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#237d73; }
[data-testid="stTabs"] [role="tab"]:hover { background:#e8eeea; }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button { min-height:44px; }
textarea { line-height:1.65; }
@media(prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }
[data-testid="stCaptionContainer"], [data-testid="stCaption"] { color:var(--atlas-muted); line-height:1.55; }
[data-testid="stSidebar"] { border-right:1px solid #304555; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color:#eef3f2; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaption"] { color:#bacacb; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--atlas-line); border-radius:8px; padding:16px 18px; height:100%; }
[data-testid="stMetricLabel"] { color:var(--atlas-muted); }
[data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; letter-spacing:-.035em; }
[data-testid="stDataFrame"] { border:1px solid var(--atlas-line); border-radius:10px; }
[data-testid="stTabs"] [role="tablist"] { border-bottom:1px solid var(--atlas-line); gap:12px; }
[data-testid="stTabs"] [role="tab"] { font-weight:600; padding-inline:4px; }
button:focus-visible, input:focus-visible, textarea:focus-visible, a:focus-visible, [role="tab"]:focus-visible { outline:2px solid #496b85; outline-offset:3px; }
[data-testid="stAlert"] { border-radius:8px; }
button, a, input, label { touch-action:manipulation; }
h1,h2,h3 { text-wrap:balance; scroll-margin-top:5rem; }
@media(max-width:640px) {
 .block-container { padding:5rem 1rem 2rem; }
 [data-testid="stMain"] h1 { font-size:1.8rem; }
 [data-testid="stMetric"] { padding:12px 14px; }
}

/* Local MIT-licensed Phosphor Duotone; presentation only. */
.atlas-section-heading{display:flex;align-items:center;gap:10px;margin-block:14px 12px!important}
.atlas-heading-icon{display:inline-flex;flex:0 0 34px;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;background:#e7f2ef;color:#237d73}
[data-testid="stMetric"]{border-radius:14px;padding:18px 20px;border-color:#dde6e1;box-shadow:0 2px 7px #14263804;transition:border-color .16s ease,box-shadow .16s ease}
[data-testid="stMetric"]:hover{border-color:#a9c9bf;box-shadow:0 4px 12px #14263808}
[data-testid="stMetricLabel"]{display:flex;flex-direction:column;align-items:flex-start;gap:0;max-width:100%;height:auto}
[data-testid="stMetricLabel"] p{white-space:normal;overflow:visible;text-overflow:clip;max-width:100%}
[data-testid="stMetricLabel"]::before{content:"";display:block;width:30px;height:30px;margin-bottom:10px;background:#e7f2ef url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2IiBmaWxsPSIjMjM3ZDczIj48cGF0aCBkPSJNMjI0LDEyOGE5Niw5NiwwLDAsMS05Niw5NlYxNjhhNDAsNDAsMCwwLDAsMC04MFYzMkE5Niw5NiwwLDAsMSwyMjQsMTI4WiIgb3BhY2l0eT0iMC4yIi8+PHBhdGggZD0iTTEyOCwyNGE4LDgsMCwwLDAtOCw4Vjg4YTgsOCwwLDAsMCw4LDgsMzIsMzIsMCwxLDEtMjcuNzIsMTYsOCw4LDAsMCwwLTIuOTMtMTAuOTNsLTQ4LjUtMjhBOCw4LDAsMCwwLDM3LjkyLDc2LDEwNCwxMDQsMCwxLDAsMTI4LDI0Wk00OC4wOSw5MS4xLDgzLDExMS4yNkE0OC4wOSw0OC4wOSwwLDAsMCw4MCwxMjhjMCwxLjUzLjA4LDMsLjIyLDQuNTJMNDEuMjgsMTQzQTg4LjE2LDg4LjE2LDAsMCwxLDQ4LjA5LDkxLjFabS0yLjY3LDY3LjMxLDM5LTEwLjQ0QTQ4LjEsNDguMSwwLDAsMCwxMjAsMTc1LjMydjQwLjMxQTg4LjIsODguMiwwLDAsMSw0NS40MiwxNTguNDFaTTEzNiwyMTUuNjNWMTc1LjMyYTQ4LDQ4LDAsMCwwLDAtOTQuNjVWNDAuMzZhODgsODgsMCwwLDEsMCwxNzUuMjdaIi8+PC9zdmc+") center/22px no-repeat;border-radius:9px}
[data-testid="stMetricValue"]{font-weight:650;line-height:1.25}
[data-testid="stDataFrame"]{border-radius:12px}
[data-testid="stTabs"] [role="tab"]{border-radius:6px 6px 0 0;transition:background .16s ease}
[data-testid="stSidebar"] .atlas-heading-icon{color:#8bd1c3;background:#284556}
@media(max-width:640px){[data-testid="stMetricLabel"]{flex-direction:row;align-items:center}[data-testid="stMetric"]{padding:15px 17px}[data-testid="stMetricLabel"]::before{display:inline-block;vertical-align:middle;margin:0 8px 0 0;width:26px;height:26px;background-size:20px}.atlas-section-heading{font-size:1.05rem!important}}
@media(prefers-reduced-motion:reduce){[data-testid="stMetric"],[data-testid="stTabs"] [role="tab"]{transition:none}}
</style>
"""


def style_chart(figure):
    figure.update_layout(template='plotly_white', font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',size=12,color='#26343b'),
                         paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
                         colorway=['#237d73','#496b85','#b44e50','#596971'],
                         hoverlabel=dict(font_size=12, bgcolor='#ffffff'),
                         legend=dict(orientation='h',yanchor='bottom',y=1.02,x=0))
    figure.update_xaxes(gridcolor='#dce1df',zerolinecolor='#dce1df',automargin=True)
    figure.update_yaxes(gridcolor='#dce1df',zerolinecolor='#dce1df',automargin=True)
    return figure


def section_heading(title):
    """Decorative local Phosphor SVG beside an escaped semantic heading."""
    from html import escape
    from pathlib import Path
    choices = {
        'Historical $1 growth': 'chart-line-up', 'Asset allocation': 'chart-pie-slice',
        '21-day rolling volatility': 'wave-sine', 'Asset contribution to volatility': 'chart-bar',
        'ETF-spread factor sensitivity': 'stack',
        'Scenario transmission and loss attribution': 'sliders-horizontal',
        'Matched-window VaR comparison': 'shield-check',
        'Exception clustering / conditional coverage': 'shield-check',
        'Evidence-grounded analyst briefing': 'check-square',
        'Reproducible research packet': 'fingerprint',
        'Target asset weights': 'chart-pie-slice',
    }
    name = choices.get(title, 'chart-line-up')
    svg = (Path(__file__).parent / 'assets' / 'icons' / 'phosphor-duotone' / (name + '.svg')).read_text()
    svg = svg.replace('<svg ', '<svg aria-hidden="true" focusable="false" width="24" height="24" ')
    return '<h3 class="atlas-section-heading"><span class="atlas-heading-icon">' + svg + '</span>' + escape(title) + '</h3>'
