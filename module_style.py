"""Phase 2 presentation: reuse the approved shell without financial logic."""
import base64
from pathlib import Path
from overview_style import _RULES, _scoped, overview_chart

_svg = (Path(__file__).parent / 'assets/icons/phosphor-duotone/chart-bar.svg').read_text().replace('currentColor', '#377cf6')
_icon = 'data:image/svg+xml;base64,' + base64.b64encode(_svg.encode()).decode()
_metric_rules = []
for selector, rules in _RULES.items():
    if '.st-key-overview_kpis' in selector and ':nth-child' not in selector:
        _metric_rules.append(_scoped(selector.replace('.st-key-overview_kpis', '[class*="st-key-atlas_kpis_"]')) + '{' + rules + '}')
MODULE_CSS = '<style>\n' + '\n'.join(_metric_rules) + '''
.atlas-module-title{display:none}
[class*="st-key-atlas_panel_"]{background:#fff;padding:18px 20px;border:1px solid #e7ebf1;border-radius:12px;min-width:0}
[class*="st-key-atlas_panel_"] [data-testid="stVerticalBlock"]{gap:9px}
[class*="st-key-atlas_panel_"] h3{font-size:1.05rem!important;font-weight:650;margin:0;padding:0;letter-spacing:-.3px;color:#24304b}
[class*="st-key-atlas_panel_"] [data-testid="stCaptionContainer"], [class*="st-key-atlas_panel_"] [data-testid="stCaptionContainer"] p{color:#526078;font-size:12px;line-height:1.6}
[class*="st-key-atlas_kpis_"] [data-testid="stMetricValue"]{overflow-wrap:anywhere;white-space:normal}
.st-key-atlas_kpis_scenario_loss [data-testid="stColumn"]:nth-child(-n+2) [data-testid="stMetricValue"]{color:#a83e48}
.st-key-atlas_kpis_scenario_gain [data-testid="stColumn"]:nth-child(-n+2) [data-testid="stMetricValue"]{color:#237d73}
.st-key-atlas_kpis_scenario_loss [data-testid="stColumn"]:last-child [data-testid="stMetricValue"],.st-key-atlas_kpis_scenario_gain [data-testid="stColumn"]:last-child [data-testid="stMetricValue"]{font-size:1.7rem}
.st-key-atlas_review_status [data-testid="stAlert"]{margin:0;border-radius:9px}
.st-key-atlas_panel_review_report textarea{font-size:13px;line-height:1.75;color:#34435c}
.st-key-atlas_report_preview{border-top:1px solid #e7ebf1;padding-top:16px;color:#34435c}
.st-key-atlas_report_preview p,.st-key-atlas_report_preview li{font-size:14px;line-height:1.8;overflow-wrap:anywhere}
.st-key-atlas_report_preview h1{font-size:1.5rem!important;line-height:1.3;letter-spacing:-.5px;color:#24304b;padding:0 0 12px}
.st-key-atlas_report_preview h2{font-size:1.15rem!important;line-height:1.4;padding:14px 0 8px;color:#24304b}
.st-key-atlas_report_preview h3{padding:12px 0 6px!important}
.st-key-atlas_report_preview code{color:#34435c;background:#f1f4f9;overflow-wrap:anywhere}
.st-key-atlas_panel_review_controls [data-testid="stDownloadButton"] button{width:100%;min-height:44px}
.st-key-atlas_panel_review_controls [data-testid="stButton"] button{width:100%;min-height:44px}
.st-key-atlas_scenario_controls{display:none}
''' + '[class*="st-key-atlas_kpis_"]{--overview-icon:url("' + _icon + '")}'
for i in range(1,6):
    MODULE_CSS += 'body:has([data-testid="stTabs"] [role="tab"]:nth-child('+str(i)+')[aria-selected="true"]) .atlas-title-'+str(i)+'{display:block}'
MODULE_CSS += '''
body:has([data-testid="stTabs"] [role="tab"]:nth-child(3)[aria-selected="true"]) .st-key-atlas_scenario_controls{display:block}
@media(max-width:850px){
[class*="st-key-atlas_kpis_"] [data-testid="stHorizontalBlock"]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
[class*="st-key-atlas_kpis_"] [data-testid="stColumn"]{width:100%!important;min-width:0!important}
[class*="st-key-atlas_kpis_"] [data-testid="stMetric"]{padding:12px;min-height:109px}
[class*="st-key-atlas_kpis_"] [data-testid="stMetricLabel"] p{font-size:11px;line-height:1.4}
[class*="st-key-atlas_kpis_"] [data-testid="stMetricValue"]{font-size:1.7rem;margin-top:7px}
.st-key-atlas_kpis_factors [data-testid="stColumn"]:last-child,.st-key-atlas_kpis_scenario_loss [data-testid="stColumn"]:last-child,.st-key-atlas_kpis_scenario_gain [data-testid="stColumn"]:last-child{grid-column:1/-1}
[class*="st-key-atlas_panel_"]{padding:16px;min-width:0}
.st-key-atlas_panel_review_report textarea{font-size:12px}
}
</style>
'''


# Match the shell's specificity for semantic colors and responsive metric sizing.
MODULE_CSS += '<style>' + _scoped(' .st-key-atlas_kpis_scenario_loss [data-testid="stColumn"]:nth-child(-n+2) [data-testid="stMetricValue"]') + '{color:#a83e48;}' + _scoped(' .st-key-atlas_kpis_scenario_gain [data-testid="stColumn"]:nth-child(-n+2) [data-testid="stMetricValue"]') + '{color:#237d73;}' + _scoped(' .st-key-atlas_kpis_scenario_loss [data-testid="stColumn"]:last-child [data-testid="stMetricValue"], .st-key-atlas_kpis_scenario_gain [data-testid="stColumn"]:last-child [data-testid="stMetricValue"]') + '{font-size:1.7rem;}' + _scoped(' [data-testid="stSidebar"] summary') + '{background:#f8f9fc;color:#34435c;}' + _scoped(' [data-testid="stSidebar"] summary *') + '{color:#34435c;}' + '@media(max-width:850px){' + _scoped(' [class*="st-key-atlas_kpis_"] [data-testid="stMetric"]') + '{padding:12px;min-height:109px;}' + _scoped(' [class*="st-key-atlas_kpis_"] [data-testid="stMetricValue"]') + '{font-size:1.7rem;margin-top:7px;}' + _scoped(' [class*="st-key-atlas_kpis_"] [data-testid="stMetricLabel"] p') + '{font-size:11px;line-height:1.4;}' + '}</style>'


def module_chart(figure):
    """Match approved chart styling; preserve trace data and units."""
    overview_chart(figure)
    if len(figure.data) > 1:
        figure.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0,
                                         font=dict(size=10), entrywidth=150))
    return figure


# Keep methodological notes legible against the approved light canvas.
MODULE_CSS += '<style>' + _scoped(' [data-testid="stCaptionContainer"]') + '{opacity:1;}' + _scoped(' [data-testid="stCaptionContainer"] p') + '{color:#526078;line-height:1.65;}' + '</style>'
