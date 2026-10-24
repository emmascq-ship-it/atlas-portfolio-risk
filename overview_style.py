"""Approved shared financial-workbench shell and Overview presentation."""
from ui_style import style_chart

_ACTIVE = 'body:has([data-testid="stTabs"] [role="tablist"] [role="tab"][aria-selected="true"])'
_RULES = {
    '': 'background:#f6f6f8;color:#24304b;',
    ' [data-testid="stAppViewContainer"]': 'background:#f6f6f8;',
    ' [data-testid="stHeader"]': 'background:#f6f6f8;',
    ' .block-container': 'max-width:1600px;padding:3.4rem 2rem 3rem;',
    ' .st-key-atlas_legacy_header': 'display:none;',
    ' .st-key-atlas_overview_header': 'display:block;',
    ' .st-key-overview_sidebar_brand': 'display:block;',
    ' [data-testid="stSidebar"]': 'background:#fff;border-right:1px solid #e9ebf0;',
    ' [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3': 'color:#24304b;',
    ' [data-testid="stSidebar"] label, [data-testid="stSidebar"] label p': 'color:#58657b;',
    ' [data-testid="stSidebar"] [data-testid="stCaptionContainer"]': 'color:#647087;',
    ' [data-testid="stSidebar"] input': 'color:#24304b;-webkit-text-fill-color:#24304b;background:#f6f7fb;',
    ' [data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-baseweb="select"]>div': 'background:#f6f7fb;color:#24304b;',
    ' [data-testid="stSidebar"] [data-testid="stNumberInputContainer"]': 'background:#f6f7fb;color:#24304b;',
    ' [data-testid="stSidebar"] [data-testid="stNumberInput"] button': 'color:#58657b;',
    ' [data-testid="stSidebar"] .atlas-heading-icon': 'display:none;',
    ' .st-key-atlas_sidebar_controls': 'padding-top:288px;',
    ' [data-testid="stTabs"] [role="tablist"]': 'position:fixed;top:145px;left:16px;width:268px;height:auto;z-index:1000000;display:flex;flex-direction:column;align-items:stretch;gap:6px;border:0;background:#fff;padding:6px 0 12px;',
    ' [data-testid="stTabs"] [role="tab"]': 'justify-content:flex-start;min-height:44px;padding:10px 14px;border-radius:9px;color:#65718a;font-weight:550;white-space:normal;',
    ' [data-testid="stTabs"] [role="tab"][aria-selected="true"]': 'background:#377cf6;color:#fff;',
    ' [data-testid="stTabs"] [role="tab"]:hover': 'background:#eaf1ff;color:#285eaf;',
    ' [data-testid="stTabs"] [role="tab"][aria-selected="true"]:hover': 'background:#2f6fdf;color:#fff;',
    ' [data-testid="stTabs"] [role="tab"]:focus-visible': 'outline:2px solid #1d4e9c;outline-offset:2px;',
    ' [data-testid="stTabs"] [data-testid="stTabHighlight"]': 'display:none;',
    ' [data-testid="stTabs"] .react-aria-SelectionIndicator': 'display:none;',
    ' [data-testid="stTabs"] [role="tablist"]::after, [data-testid="stTabs"] [role="tab"]::before, [data-testid="stTabs"] [role="tab"]::after': 'display:none;',
    ' [data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:first-child': 'background:#fff;border:1px solid #b6c1d3;',
    ' [data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:first-child>div': 'background:transparent;',
    ' [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked)>div>div:first-child': 'border-color:#377cf6;',
    ' [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked)>div>div:first-child>div': 'background:#377cf6;',

    ' .st-key-overview_kpis [data-testid="stMetric"]': 'background:#fff;border:1px solid #edf0f4;border-radius:12px;box-shadow:none;padding:19px 20px;min-height:125px;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"]': 'display:block;color:#6a7486;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"]::before': 'display:none;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"] p': 'font-size:12px;line-height:1.5;white-space:normal;',
    ' .st-key-overview_kpis [data-testid="stMetricValue"]': 'color:#24304b;font-size:clamp(1.7rem,2.4vw,2.2rem);font-weight:700;margin-top:12px;letter-spacing:-.6px;',
    ' .st-key-overview_primary_chart, .st-key-overview_contribution_chart, .st-key-overview_holdings': 'background:#fff;padding:20px 22px;border:1px solid #edf0f4;border-radius:12px;min-width:0;',
    ' .st-key-overview_primary_chart h3, .st-key-overview_contribution_chart h3, .st-key-overview_holdings h3': 'font-size:1.05rem;font-weight:650;margin:0;letter-spacing:-.3px;',
    ' .st-key-overview_notional [data-testid="stText"]': 'font-size:12px;color:#5e6a7d;white-space:normal;line-height:1.6;',
    ' [data-testid="stAlert"]': 'border-radius:9px;',
    ' [data-testid="stDataFrame"]': 'border:0;border-radius:8px;',
}
# Compact Phase 1 refinement, scoped to Overview only.
_RULES.update({
    ' .block-container': 'max-width:1600px;padding:3rem 2rem 2.5rem;',
    ' .st-key-overview_legacy_synthetic_notice, .st-key-overview_legacy_validation, .st-key-overview_legacy_metadata': 'display:none;',
    ' [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]': 'gap:.7rem;',
    ' [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p': 'color:#526078;font-size:12px;line-height:1.55;',
    ' .st-key-overview_kpis [data-testid="stMetric"]': 'background:#fff;border:1px solid #e7ebf1;border-radius:12px;box-shadow:none;padding:15px 18px;min-height:116px;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"]': 'display:flex;flex-direction:row;align-items:center;gap:8px;min-height:32px;max-width:100%;color:#56647a;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"] p': 'font-size:12px;line-height:1.4;white-space:normal;font-weight:550;color:#56647a;',
    ' .st-key-overview_kpis [data-testid="stMetricLabel"]::before': 'content:"";display:block;flex:0 0 26px;width:26px;height:26px;border-radius:8px;margin:0;background:#edf3ff var(--overview-icon) center/19px no-repeat;',
    ' .st-key-overview_kpis [data-testid="stMetricValue"]': 'color:#24304b;font-size:clamp(1.8rem,2.6vw,2.25rem);font-weight:720;line-height:1.2;margin-top:9px;letter-spacing:-.7px;font-variant-numeric:tabular-nums;',
    ' .st-key-overview_kpis [data-testid="stColumn"]:nth-child(4) [data-testid="stMetricValue"]': 'color:#a83e48;',
    ' .st-key-overview_context [data-testid="stVerticalBlock"]': 'gap:2px;',
    ' .st-key-overview_context [data-testid="stText"]': 'font-size:12px;font-weight:550;color:#3e4d65;line-height:1.6;white-space:normal;',
    ' .st-key-overview_primary_chart, .st-key-overview_contribution_chart, .st-key-overview_holdings': 'background:#fff;padding:18px 20px;border:1px solid #e7ebf1;border-radius:12px;min-width:0;',
    ' .st-key-overview_primary_chart [data-testid="stVerticalBlock"], .st-key-overview_contribution_chart [data-testid="stVerticalBlock"]': 'gap:6px;',
    ' .st-key-overview_primary_chart h3, .st-key-overview_contribution_chart h3, .st-key-overview_holdings h3': 'font-size:1.05rem;font-weight:650;margin:0;padding:0;letter-spacing:-.3px;color:#24304b;',
    ' [data-testid="stSidebar"] [data-testid="stExpander"]': 'background:#f8f9fc;border:1px solid #e5eaf2;border-radius:10px;color:#24304b;',
    ' [data-testid="stSidebar"] summary': 'font-weight:600;font-size:13px;color:#34435c;min-height:44px;',
})
_RULES[' .st-key-overview_kpis [data-testid="stColumn"]:nth-child(1)'] = '--overview-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2IiBmaWxsPSIjMzc3Y2Y2Ij48cGF0aCBkPSJNMjI0LDEyOGE5Niw5NiwwLDAsMS05Niw5NlYxNjhhNDAsNDAsMCwwLDAsMC04MFYzMkE5Niw5NiwwLDAsMSwyMjQsMTI4WiIgb3BhY2l0eT0iMC4yIi8+PHBhdGggZD0iTTEyOCwyNGE4LDgsMCwwLDAtOCw4Vjg4YTgsOCwwLDAsMCw4LDgsMzIsMzIsMCwxLDEtMjcuNzIsMTYsOCw4LDAsMCwwLTIuOTMtMTAuOTNsLTQ4LjUtMjhBOCw4LDAsMCwwLDM3LjkyLDc2LDEwNCwxMDQsMCwxLDAsMTI4LDI0Wk00OC4wOSw5MS4xLDgzLDExMS4yNkE0OC4wOSw0OC4wOSwwLDAsMCw4MCwxMjhjMCwxLjUzLjA4LDMsLjIyLDQuNTJMNDEuMjgsMTQzQTg4LjE2LDg4LjE2LDAsMCwxLDQ4LjA5LDkxLjFabS0yLjY3LDY3LjMxLDM5LTEwLjQ0QTQ4LjEsNDguMSwwLDAsMCwxMjAsMTc1LjMydjQwLjMxQTg4LjIsODguMiwwLDAsMSw0NS40MiwxNTguNDFaTTEzNiwyMTUuNjNWMTc1LjMyYTQ4LDQ4LDAsMCwwLDAtOTQuNjVWNDAuMzZhODgsODgsMCwwLDEsMCwxNzUuMjdaIi8+PC9zdmc+");'
_RULES[' .st-key-overview_kpis [data-testid="stColumn"]:nth-child(2)'] = '--overview-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2IiBmaWxsPSIjMzc3Y2Y2Ij48cGF0aCBkPSJNMjA4LDQwVjIwOEgxNTJWNDBaIiBvcGFjaXR5PSIwLjIiLz48cGF0aCBkPSJNMjI0LDIwMGgtOFY0MGE4LDgsMCwwLDAtOC04SDE1MmE4LDgsMCwwLDAtOCw4VjgwSDk2YTgsOCwwLDAsMC04LDh2NDBINDhhOCw4LDAsMCwwLTgsOHY2NEgzMmE4LDgsMCwwLDAsMCwxNkgyMjRhOCw4LDAsMCwwLDAtMTZaTTE2MCw0OGg0MFYyMDBIMTYwWk0xMDQsOTZoNDBWMjAwSDEwNFpNNTYsMTQ0SDg4djU2SDU2WiIvPjwvc3ZnPg==");'
_RULES[' .st-key-overview_kpis [data-testid="stColumn"]:nth-child(3)'] = '--overview-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2IiBmaWxsPSIjMzc3Y2Y2Ij48cGF0aCBkPSJNMjMyLDEyOGMtNTIsMTEwLjg1LTc4LDU1LjQzLTEwNCwwWk0yNCwxMjhIMTI4QzEwMiw3Mi41Nyw3NiwxNy4xNSwyNCwxMjhaIiBvcGFjaXR5PSIwLjIiLz48cGF0aCBkPSJNMjM5LjI0LDEzMS40Yy0yMiw0Ni44LTQxLjQsNjguNi02MS4yLDY4LjYtMjUuMSwwLTQwLjczLTMzLjMyLTU3LjI4LTY4LjZDMTA3LjcsMTAzLjU2LDkyLjksNzIsNzgsNzJjLTE2LjQsMC0zNi4zMSwzNy4yMS00Ni43Miw1OS40YTgsOCwwLDAsMS0xNC40OC02LjhDMzguNzEsNzcuOCw1OC4xNiw1Niw3OCw1NmMyNS4xLDAsNDAuNzMsMzMuMzIsNTcuMjgsNjguNkMxNDguMywxNTIuNDQsMTYzLjEsMTg0LDE3OCwxODRjMTYuNCwwLDM2LjMxLTM3LjIxLDQ2LjcyLTU5LjRhOCw4LDAsMCwxLDE0LjQ4LDYuOFoiLz48L3N2Zz4=");'
_RULES[' .st-key-overview_kpis [data-testid="stColumn"]:nth-child(4)'] = '--overview-icon:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNTYgMjU2IiBmaWxsPSIjMzc3Y2Y2Ij48cGF0aCBkPSJNMjMyLDEyOHY2NEgxNjhaIiBvcGFjaXR5PSIwLjIiLz48cGF0aCBkPSJNMjM1LjA2LDEyMC42MWE4LDgsMCwwLDAtOC43MiwxLjczTDIwMCwxNDguNjksMTQxLjY2LDkwLjM0YTgsOCwwLDAsMC0xMS4zMiwwTDk2LDEyNC42OSwyOS42Niw1OC4zNEE4LDgsMCwwLDAsMTguMzQsNjkuNjZsNzIsNzJhOCw4LDAsMCwwLDExLjMyLDBMMTM2LDEwNy4zMSwxODguNjksMTYwbC0yNi4zNSwyNi4zNEE4LDgsMCwwLDAsMTY4LDIwMGg2NGE4LDgsMCwwLDAsOC04VjEyOEE4LDgsMCwwLDAsMjM1LjA2LDEyMC42MVpNMjI0LDE4NEgxODcuMzFMMjI0LDE0Ny4zMVoiLz48L3N2Zz4=");'

_RULES[' [data-testid="stLayoutWrapper"]:has(>.st-key-atlas_legacy_header)'] = 'display:none;'
_RULES[' [data-testid="stLayoutWrapper"]:has(>.st-key-overview_legacy_synthetic_notice)'] = 'display:none;'
_RULES[' [data-testid="stLayoutWrapper"]:has(>.st-key-overview_legacy_validation)'] = 'display:none;'
_RULES[' [data-testid="stLayoutWrapper"]:has(>.st-key-overview_legacy_metadata)'] = 'display:none;'

# Scope each comma-separated selector independently; no styles leak to other tabs.
def _scoped(selector):
    return ','.join(_ACTIVE + part for part in selector.split(','))

OVERVIEW_CSS = '<style>\n.st-key-atlas_overview_header,.st-key-overview_sidebar_brand{display:none}\n' + '\n'.join(_scoped(k)+'{'+v+'}' for k,v in _RULES.items()) + '''
.overview-topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;background:#fff;border:1px solid #edf0f4;border-radius:12px;padding:18px 22px;margin-bottom:6px}
.overview-topbar h1{font-size:1.65rem!important;letter-spacing:-.7px;margin:3px 0 0;padding:0;color:#24304b}
.overview-workspace{color:#7c8698;font-size:11px;font-weight:550}.overview-source{font-size:12px;color:#4c607b;line-height:1.5;text-align:right}.overview-source small{display:block;font-size:10px;color:#7c8698;margin-top:3px}.overview-source-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#377cf6;margin-right:7px}
.overview-brand{display:flex;align-items:center;gap:12px;padding:4px 0 18px}.overview-monogram{background:#377cf6;color:#fff;width:37px;height:37px;border-radius:10px;display:grid;place-items:center;font-size:22px;font-weight:750}.overview-brand strong{color:#24304b;font-size:20px;letter-spacing:.02em}.overview-brand small{display:block;color:#8993a4;font-size:10px;margin-top:2px}
''' + _ACTIVE + ':has([data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stTabs"] [role="tablist"]{position:static;width:auto;flex-direction:row;overflow-x:auto;}' + '@media(max-width:850px){' + _scoped(' .block-container')+'{padding:3.8rem 1rem 2rem;}' + _scoped(' [data-testid="stTabs"] [role="tablist"]')+'{position:static;width:auto;flex-direction:row;gap:8px;overflow-x:auto;background:transparent;}' + _scoped(' [data-testid="stTabs"] [role="tab"]')+'{min-height:42px;white-space:nowrap;padding:8px 12px;}' + _scoped(' .st-key-atlas_sidebar_controls')+'{padding-top:0;}' + _scoped(' .st-key-overview_kpis [data-testid="stHorizontalBlock"]')+'{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}' + _scoped(' .st-key-overview_kpis [data-testid="stColumn"]')+'{width:100%!important;min-width:0!important;}' + _scoped(' .st-key-overview_kpis [data-testid="stMetric"]')+'{padding:15px;min-height:119px;}' + '.overview-topbar{padding:16px;gap:12px;align-items:flex-start}.overview-topbar h1{font-size:1.35rem!important}.overview-source{font-size:10px}.overview-workspace{font-size:9px}' + _scoped(' .st-key-overview_primary_chart, .st-key-overview_contribution_chart, .st-key-overview_holdings')+'{padding:16px;}' + '}\n</style>'

OVERVIEW_CSS += '<style>' + _scoped(' .overview-topbar') + '{display:block;padding:14px 20px;margin:0;border-color:#e5eaf2;}' + """
.overview-topline{display:flex;justify-content:space-between;align-items:center;gap:14px}
.overview-topbar h1{font-size:1.5rem!important;margin:2px 0 0}.overview-workspace{color:#5e6b80;font-size:10px}.overview-source{color:#40516c}.overview-source small{color:#5e6b80;font-size:10px}
.overview-disclosure{margin-top:11px;padding:9px 11px;border-left:3px solid #d4a955;background:#fff9eb;color:#715721;font-size:11px;line-height:1.55;border-radius:5px}.overview-disclosure strong{font-size:10px;font-weight:750;letter-spacing:.025em}
.overview-metadata{display:flex;flex-wrap:wrap;gap:5px 16px;margin-top:9px;font-size:11px;line-height:1.5;color:#526078}.overview-metadata span+span{border-left:1px solid #dce2ec;padding-left:16px}.overview-brand small{color:#637087}
""" + '@media(max-width:850px){' + _scoped(' .block-container') + '{padding:3.5rem .9rem 2rem;}' + _scoped(' [data-testid="stTabs"] [role="tablist"]') + '{position:static;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;height:auto;width:100%;overflow:visible;padding:0;margin:0;border:0;}' + _scoped(' [data-testid="stTabs"] [role="tab"]') + '{justify-content:center;min-height:42px;white-space:normal;padding:6px 5px;font-size:11px;line-height:1.3;text-align:center;width:100%;}' + _scoped(' [data-testid="stTabs"] [role="tab"] p') + '{font-size:11px;line-height:1.3;white-space:normal;}' + _scoped(' .st-key-overview_kpis [data-testid="stMetric"]') + '{padding:12px;min-height:109px;}' + _scoped(' .st-key-overview_kpis [data-testid="stMetricValue"]') + '{font-size:1.85rem;margin-top:7px;}' + _scoped(' .st-key-overview_kpis [data-testid="stMetricLabel"] p') + '{font-size:11px;}' + _scoped(' .st-key-overview_primary_chart, .st-key-overview_contribution_chart, .st-key-overview_holdings') + '{padding:16px;}' + '.overview-topbar{padding:13px!important}.overview-topbar h1{font-size:1.27rem!important}.overview-source{font-size:10px}.overview-topline{gap:8px;align-items:flex-start}.overview-workspace{font-size:9px}.overview-disclosure{font-size:11px;padding:8px 9px;margin-top:10px}.overview-metadata{font-size:10px;gap:3px 10px;margin-top:8px}.overview-metadata span+span{padding-left:0;border:0}.overview-source small{font-size:9px}' + '}</style>'



def overview_chart(figure):
    """Keep all underlying traces and numbers; adapt chart typography and grids."""
    style_chart(figure)
    figure.update_layout(font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif', size=12, color='#4e5d75'))
    figure.update_xaxes(gridcolor='#edf0f5', zerolinecolor='#dce3ed', tickfont=dict(size=11, color='#526078'), title_font=dict(size=11, color='#526078'), nticks=4)
    figure.update_yaxes(gridcolor='#edf0f5', zerolinecolor='#dce3ed', tickfont=dict(size=11, color='#526078'), title_font=dict(size=11, color='#526078'))
    return figure
