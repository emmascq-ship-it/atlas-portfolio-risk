"""Generate self-contained, no-server GitHub Pages / offline portfolio demo.

Examples:
  python publish_demo.py
  python publish_demo.py --input-csv my_adjusted_prices.csv --output my_report.html
"""
import argparse
from pathlib import Path
import pandas as pd
from risk_engine import ASSETS, DEFAULT_WEIGHTS, generate_synthetic_prices, validate_prices
from static_dashboard import write_dashboard


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate one self-contained public research demo (no API calls).')
    parser.add_argument('--output', default='docs/index.html')
    parser.add_argument('--input-csv', help='Optional complete adjusted price CSV with Date and seven asset columns')
    parser.add_argument('--confidence', type=float, choices=(.90,.95,.975,.99), default=.95)
    parser.add_argument('--window', type=int, choices=(250, 500), default=250)
    parser.add_argument('--confirm-public-data', action='store_true',
                        help='Allow user-supplied CSV observations to be embedded in docs/index.html for publication')
    args = parser.parse_args(argv)
    # GitHub Pages publishes every file inside docs/, not only docs/index.html.
    # Resolve relative and absolute paths (including symlinks) to avoid accidental
    # publication through docs/other.html or an absolute path to docs/index.html.
    public_directory = (Path(__file__).resolve().parent / 'docs').resolve()
    requested_output = Path(args.output).resolve()
    if args.input_csv and requested_output.is_relative_to(public_directory) and not args.confirm_public_data:
        parser.error('Refusing to embed user-supplied data anywhere inside public docs/. '
                     'Use a private output path, or explicitly supply --confirm-public-data.')
    if args.input_csv:
        raw = pd.read_csv(args.input_csv)
        if set(raw.columns) != {'Date', *ASSETS}:
            parser.error('CSV requires Date plus exactly seven named asset columns')
        dates = pd.to_datetime(raw.pop('Date'), errors='raise')
        prices = raw.set_axis(pd.DatetimeIndex(dates)).loc[:, ASSETS]
        source = 'User-supplied adjusted price series (not independently verified)'
    else:
        prices = generate_synthetic_prices()
        source = 'Synthetic demo — NOT market observations'
    checks = validate_prices(prices, DEFAULT_WEIGHTS, min_history=max(261,args.window+1))
    if not all(checks.values()):
        parser.error('Input validation failed: ' + '; '.join(k for k,v in checks.items() if not v))
    payload = write_dashboard(prices, Path(args.output), weights=DEFAULT_WEIGHTS,
                              source_label=source, confidence=args.confidence, window=args.window)
    print(f"Generated offline HTML: {Path(args.output).resolve()}")
    print(f"Source: {source} | Baseline stress: {payload['kpis']['stress']:.3%} | Status: UNAPPROVED")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
