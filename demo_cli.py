"""Reproduce a complete demo analysis offline without Streamlit or live credentials.

Example: python demo_cli.py --output-dir output/demo
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from risk_engine import ASSETS, DEFAULT_WEIGHTS, SCENARIOS, generate_synthetic_prices, portfolio_returns, rolling_var_backtest
from research_packet import generate_packet, packet_bytes
from briefing_workflow import evidence_pack, rules_based_draft, export_review_bundle
from validation_extensions import christoffersen_independence
from risk_engine import summarize_risk, kupiec_unconditional_coverage, scenario_impact
from factor_engine import factor_attribution


def main(argv=None):
    parser=argparse.ArgumentParser(description='Reproducible portfolio-risk demo; offline by default.')
    parser.add_argument('--output-dir',default='output/demo',help='Location for reproducible demo files')
    parser.add_argument('--input-csv',help='Optional own adjusted price series: Date plus seven asset columns')
    parser.add_argument('--window',type=int,choices=(250,500),default=250)
    parser.add_argument('--confidence',type=float,choices=(.90,.95,.975,.99),default=.95)
    args=parser.parse_args(argv)
    if args.input_csv:
        data=pd.read_csv(args.input_csv)
        if 'Date' not in data.columns or set(data.columns)!={'Date',*ASSETS}:
            parser.error('CSV requires Date and exactly the seven named asset columns')
        dates=pd.to_datetime(data.pop('Date'),errors='raise')
        prices=data.set_axis(pd.DatetimeIndex(dates)).loc[:,ASSETS]
        source='User-uploaded adjusted prices'
    else:
        prices=generate_synthetic_prices()
        source='Synthetic demo — NOT market observations'
    weights=DEFAULT_WEIGHTS
    scenario='Equity selloff'
    shocks=SCENARIOS[scenario]
    packet=generate_packet(prices,weights,confidence=args.confidence,window=args.window,
        notional=1e6,scenario_label=scenario,class_shocks=shocks,source_label=source)
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    (out/'research_packet_UNAPPROVED.json').write_bytes(packet_bytes(packet))
    p_returns=portfolio_returns(prices,weights)
    backtest=rolling_var_backtest(p_returns,args.window,args.confidence)
    backtest.to_csv(out/'var_backtest.csv',index_label='Date')
    prices.to_csv(out/'analysis_prices.csv',index_label='Date')
    risk=summarize_risk(p_returns,args.confidence)
    coverage=kupiec_unconditional_coverage(backtest,args.confidence)
    factor=factor_attribution(prices,weights)
    stress_return,_=scenario_impact(weights,scenario)
    evidence=evidence_pack(risk,coverage,factor,weights,scenario,stress_return,
        1e6,args.confidence,source,prices.index.min().date().isoformat(),
        prices.index.max().date().isoformat(),args.window,
        input_digest=packet['input_sha256'])
    draft=rules_based_draft(evidence)
    (out/'risk_brief_DRAFT.md').write_text(draft,encoding='utf-8')
    (out/'review_bundle_UNAPPROVED.json').write_bytes(export_review_bundle(draft,evidence,None))
    print(f"Generated reproducible, UNAPPROVED research output in {out.resolve()}")
    print(f"Source: {source}; price rows: {len(prices)}; breaches: {coverage.breaches}/{coverage.observations}")
    print(f"Input SHA-256: {packet['input_sha256']}")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
