"""Opt-in live audit against licensed independent CSVs. Never publishes.

Prices: Date plus seven ATLAS asset columns, adjusted USD, full analysis interval.
Actions: Date,Ticker,Dividends,Stock Splits, full interval ledger (zero=no event).
Reviewer must establish independence, completeness and adjustment conventions.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from market_data import download_etf_prices
from market_integrity import compare_adjusted_prices, compare_corporate_actions
from tiingo_reference import validate_tiingo_reference

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--reference-prices',type=Path)
    p.add_argument('--reference-actions',type=Path)
    p.add_argument('--reference-source')
    p.add_argument('--tiingo-free-starter',action='store_true')
    p.add_argument('--confirm-free-starter',action='store_true')
    p.add_argument('--period',choices=['3y','5y','10y'],default='3y')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path(__file__).resolve().parents[1]/'docs').resolve()):
        raise ValueError('Market audit reports must remain outside public docs/')
    if a.tiingo_free_starter:
        token=os.environ.get('TIINGO_API_KEY','')
        if not token.strip() or not a.confirm_free_starter:
            report={'status':'PENDING','reason':'Optional $0 Starter key and explicit free-tier confirmation required'}
        else:
            prices,metadata=download_etf_prices(a.period)
            report=validate_tiingo_reference(prices,metadata,token,confirm_free_starter=True)
        a.output.write_text(json.dumps(report,indent=2))
        print('Live independent validation: '+report['status'])
        return 0 if report['status']=='REFERENCE_CHECKS_PASSED' else 2
    if not (a.reference_prices and a.reference_actions and a.reference_source):
        p.error('Supply --tiingo-free-starter or all three independent CSV reference arguments')
    prices,metadata=download_etf_prices(a.period)
    ref=pd.read_csv(a.reference_prices); ref.index=pd.to_datetime(ref.pop('Date'),errors='raise')
    result=compare_adjusted_prices(prices,ref,a.reference_source)
    primary=pd.DataFrame(metadata['corporate_actions'],columns=['Date','Ticker','Dividends','Stock Splits'])
    actions=compare_corporate_actions(primary,pd.read_csv(a.reference_actions),a.reference_source,
                                    metadata['first_date'],metadata['last_date'])
    report={'status':'SUPPLIED_REFERENCE_CHECKS_PASSED_NOT_CERTIFICATION','prices':result,
            'actions':actions,'provider':metadata,'reference_file_sha256':{
                f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.reference_prices,a.reference_actions)}}
    a.output.write_text(json.dumps(report,indent=2))
    print('PASS: supplied reference checks; provenance and rights require separate review')
    return 0

if __name__=='__main__': raise SystemExit(main())
