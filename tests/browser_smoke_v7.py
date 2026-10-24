"""Real Chromium regression for ATLAS V7; no external scripts or APIs."""
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import io
import json
import os

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'docs/index.html').read_text(encoding='utf-8')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    errors=[]
    page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.on('console',lambda msg: errors.append(msg.text) if msg.type=='error' else None)
    page.set_content(HTML,wait_until='load',timeout=90000)
    page.locator('#var').wait_for(state='visible',timeout=55000)
    assert page.locator('#var').inner_text().endswith('%')
    assert page.locator('#correlation.js-plotly-plot').count()==1
    assert page.locator('#drawdown_chart.js-plotly-plot').count()==1
    assert page.locator('#risk_contrib_chart.js-plotly-plot').count()==1
    for name in ('overview','factors','scenario','validation','review'):
        page.locator(f'[data-target="{name}"]').click()
        assert page.locator(f'#{name}').is_visible()
    with page.expect_download() as event:
        page.locator('#evidencedownload').click()
    with TemporaryDirectory() as temp:
        target=Path(temp)/'evidence.json';event.value.save_as(target)
        assert json.loads(target.read_text())['status']=='UNAPPROVED_DRAFT'
    page.locator('[data-target="validation"]').click()
    assert page.locator('#benchmark_chart.js-plotly-plot').count()==1
    assert page.locator('#benchmark_rows tr').count()==9
    rows=page.locator('#benchmark_rows tr')
    assert '649' in rows.nth(0).inner_text()
    assert '31' in rows.nth(1).inner_text()
    assert '30' in rows.nth(1).inner_text()
    with page.expect_download() as event:
        page.locator('#benchmarkdownload').click()
    with TemporaryDirectory() as temp:
        target=Path(temp)/'test.csv'
        download=event.value
        assert download.suggested_filename=='atlas_var_benchmark_UNAPPROVED.csv'
        download.save_as(target)
        records=list(csv.DictReader(io.StringIO(target.read_text())))
        assert len(records)==649
        assert all(x in records[0] for x in ('Date','Realized Loss','Historical VaR','Gaussian VaR'))
        assert all(float(row['Historical VaR'])>=0 and float(row['Gaussian VaR'])>=0 for row in records)
    page.locator('[data-target="review"]').click()
    assert page.locator('#data_quality div').count()==7
    assert 'Synthetic observations' in page.locator('#quality_flags').inner_text()
    assert 'UNAPPROVED' in page.locator('#review').inner_text()
    page.locator('[data-target="scenario"]').click()
    assert page.locator('#scenario_pct').inner_text()=='-13.045%'
    page.locator('#presets button').nth(1).click()
    assert page.locator('#scenario_pct').inner_text()=='-8.990%'
    with page.expect_download() as event:
        page.locator('#scenarioexport').click()
    with TemporaryDirectory() as temp:
        target=Path(temp)/'scenario.json';event.value.save_as(target)
        result=json.loads(target.read_text())
        assert result['approval_status']=='UNAPPROVED_HYPOTHETICAL'
        assert len(result['baseline_input_sha256'])==64
    page.locator('#reset').click()
    assert page.locator('#scenario_pct').inner_text()=='-13.045%'
    assert not errors,errors
    mobile=browser.new_page(viewport={'width':390,'height':844})
    mobile.on('pageerror',lambda e: errors.append('mobile:'+str(e)))
    mobile.on('console',lambda msg: errors.append('mobile:'+msg.text) if msg.type=='error' else None)
    mobile.set_content(HTML,wait_until='load',timeout=90000)
    mobile.locator('#var').wait_for(state='visible',timeout=55000)
    mobile.locator('[data-target="validation"]').click()
    assert mobile.locator('#benchmark_chart.js-plotly-plot').count()==1
    mobile.wait_for_timeout(1500)  # allow Plotly's asynchronous reflow after opening hidden tab
    assert mobile.evaluate('document.documentElement.scrollWidth')<=390
    for name in ('overview','factors','scenario','validation','review'):
        mobile.locator(f'[data-target="{name}"]').click()
        assert mobile.locator(f'#{name}').is_visible()
        mobile.wait_for_function('document.documentElement.scrollWidth <= 390')
        if os.environ.get('ATLAS_SCREENSHOT_DIR'):
            evidence = Path(os.environ['ATLAS_SCREENSHOT_DIR'])
            evidence.mkdir(parents=True, exist_ok=True)
            mobile.screenshot(path=str(evidence / f'standalone-mobile-{name}.png'), full_page=True)
    assert not errors,errors
    browser.close()
    print('V7 CHROMIUM PASS: two-model plot, 9 diagnostics, CSV, provenance, scenarios, approvals, mobile, no JS errors')
