"""Optional real-Chromium smoke test. Install playwright + browser or use system Chromium.

Run: python tests/browser_smoke_v6.py
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'docs/index.html').read_text(encoding='utf-8')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    errors=[]
    page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
    page.on('pageerror',lambda e: errors.append(str(e)))
    # Local file:// is blocked by some sandbox policies; set_content tests the exact generated page.
    page.set_content(HTML,wait_until='load',timeout=60000)
    page.locator('#var').wait_for(state='visible',timeout=50000)
    assert page.locator('#var').inner_text().endswith('%')
    assert page.locator('#correlation.js-plotly-plot').count()==1
    assert page.locator('#drawdown_chart.js-plotly-plot').count()==1
    assert page.locator('#risk_contrib_chart.js-plotly-plot').count()==1
    assert page.locator('#positions tr').count()==7
    page.locator('[data-target="scenario"]').click()
    assert page.locator('#scenario_pct').inner_text()=='-13.045%'
    assert page.locator('#presets button').count()==3
    page.locator('#presets button').nth(1).click()
    assert page.locator('#scenario_pct').inner_text()=='-8.990%'
    assert page.locator('#scenario_state').inner_text()=='MODIFIED'
    with page.expect_download() as d:
        page.locator('#scenarioexport').click()
    download=d.value
    assert download.suggested_filename=='atlas_scenario_UNAPPROVED.json'
    archive=Path('/tmp/atlas_scenario_browser_smoke.json')
    download.save_as(archive)
    data=json.loads(archive.read_text())
    assert data['approval_status']=='UNAPPROVED_HYPOTHETICAL'
    assert abs(data['portfolio_return']+.0899)<1e-9
    assert len(data['asset_contributions'])==7
    assert len(data['baseline_input_sha256'])==64
    page.locator('#reset').click()
    assert page.locator('#scenario_pct').inner_text()=='-13.045%'
    assert page.locator('#scenario_state').inner_text()=='BASELINE'
    page.locator('[data-target="review"]').click()
    assert 'UNAPPROVED' in page.locator('#review').inner_text()
    tab=page.locator('[data-target="review"]');tab.focus();tab.press('Home')
    assert page.locator('[data-target="overview"]').get_attribute('aria-selected')=='true'
    assert not errors,errors
    mobile=browser.new_page(viewport={'width':390,'height':844})
    mobile.on('pageerror',lambda e:errors.append('mobile:'+str(e)))
    mobile.set_content(HTML,wait_until='load',timeout=60000)
    mobile.locator('#var').wait_for(state='visible',timeout=50000)
    assert mobile.evaluate('document.documentElement.scrollWidth') <= 390
    assert not errors,errors
    print('CHROMIUM PASS: charts, navigation, presets, reset, JSON download, provenance, mobile width, JS errors=0')
    browser.close()
