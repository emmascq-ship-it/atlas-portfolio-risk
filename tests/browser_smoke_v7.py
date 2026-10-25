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


def geometry(page):
    """Actual layout measurements, including cached Plotly surfaces and KPI text."""
    return page.evaluate("""() => {
        const panel = document.querySelector('.panel.active');
        const graphs = [...panel.querySelectorAll('.graph')];
        const values = [...panel.querySelectorAll('.metric .value')];
        return {
            viewport: innerWidth,
            rootOverflow: getComputedStyle(document.documentElement).overflowX,
            bodyOverflow: getComputedStyle(document.body).overflowX,
            document: document.documentElement.scrollWidth,
            graphs: graphs.map(el => ({id: el.id, width: el.clientWidth,
                surface: el.querySelector('.svg-container')?.getBoundingClientRect().width || 0})),
            values: values.map(el => ({id: el.id, width: el.clientWidth, scroll: el.scrollWidth})),
            weightBars: [...panel.querySelectorAll('.weight-bar')].map(el => ({
                width: el.getBoundingClientRect().width,
                track: el.parentElement.getBoundingClientRect().width})),
            offenders: [...document.querySelectorAll('.sidebar, main, .panel.active .card, .panel.active .grid, .panel.active .svg-container')]
                .filter(el => el.getBoundingClientRect().right > innerWidth)
                .map(el => ({id:el.id, class:el.className, right:el.getBoundingClientRect().right}))
        };
    }""")


def assert_geometry(page, width, module):
    measured = geometry(page)
    assert measured['document'] <= width, (module, measured)
    assert measured['rootOverflow'] not in ('hidden', 'clip'), measured
    assert measured['bodyOverflow'] not in ('hidden', 'clip'), measured
    assert not measured['offenders'], (module, measured)
    assert all(0 < g['surface'] <= g['width'] + 1 for g in measured['graphs']), (module, measured)
    assert all(v['scroll'] <= v['width'] + 1 for v in measured['values']), (module, measured)
    assert all(0 < b['width'] <= b['track'] for b in measured['weightBars']), (module, measured)
    assert page.locator('.panel.active').count() == 1
    for inactive in page.locator('.panel:not(.active)').all():
        assert not inactive.is_visible()
    return measured

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
        assert page.evaluate('document.documentElement.scrollWidth') <= 1440
        assert_geometry(page, 1440, name)
        if os.environ.get('ATLAS_SCREENSHOT_DIR'):
            evidence = Path(os.environ['ATLAS_SCREENSHOT_DIR'])
            evidence.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(evidence / f'standalone-desktop-{name}.png'), full_page=True)
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
    assert page.locator('#brief h2').inner_text().startswith('Portfolio Risk Brief')
    assert page.locator('#brief h3').count() > 0
    assert page.locator('#brief').get_attribute('contenteditable') is None
    assert 'only in the full Streamlit application' in page.locator('.workflow-note').inner_text()
    assert page.get_by_role('button', name='Approve', exact=True).count() == 0
    with page.expect_download() as event:
        page.locator('#briefdownload').click()
    with TemporaryDirectory() as temp:
        target = Path(temp) / 'draft.md'
        event.value.save_as(target)
        draft = target.read_text()
        assert draft.startswith('# Portfolio Risk Brief')
        assert 'No recommendation' in draft
    # The read-only preview must contain no executable or interactive report elements.
    assert page.locator('#brief script, #brief iframe, #brief input, #brief button').count() == 0
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
    # Fresh loads at every breakpoint catch hidden-panel default-width overflow
    # immediately after first activation, without sleeps or resize grace periods.
    responsive = []
    for width in (1440, 1024, 768, 390):
        check = browser.new_page(viewport={'width': width, 'height': 900})
        check.on('pageerror', lambda e: errors.append(str(e)))
        check.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        check.set_content(HTML, wait_until='load', timeout=90000)
        check.locator('#var').wait_for(state='visible', timeout=55000)
        for name in ('overview', 'factors', 'scenario', 'validation', 'review'):
            check.locator(f'[data-target="{name}"]').click()
            assert check.locator(f'#{name}').is_visible()
            responsive.append({'module': name, **assert_geometry(check, width, name)})
            if os.environ.get('ATLAS_SCREENSHOT_DIR'):
                evidence = Path(os.environ['ATLAS_SCREENSHOT_DIR'])
                evidence.mkdir(parents=True, exist_ok=True)
                check.screenshot(path=str(evidence / f'responsive-{width}-{name}.png'), full_page=True)
        check.close()
    print('RESPONSIVE GEOMETRY: ' + json.dumps(responsive))
    assert not errors, errors
    browser.close()
    print('V7 CHROMIUM PASS: two-model plot, 9 diagnostics, CSV, provenance, scenarios, read-only report, unapproved exports, mobile, no JS errors')
