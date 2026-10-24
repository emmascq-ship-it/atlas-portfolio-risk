"""Actual Streamlit/Chromium E2E. Local synthetic fixtures; no AI or market calls.

Run: python tests/browser_streamlit.py. Starts/stops its own app server.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
TABS = ['01 / Overview', '02 / Factor exposures', '03 / Scenario lab',
        '04 / Model validation', '05 / Review desk']


def download(page, label, folder):
    with page.expect_download() as pending:
        page.get_by_role('button', name=label, exact=True).click()
    item = pending.value
    target = folder / item.suggested_filename
    item.save_as(target)
    assert target.stat().st_size > 0
    return target


def select_labeled_control(page, role, name):
    # Streamlit clips the native input to 1px; its visible wrapping label is
    # the intended pointer target. Keep the native checked-state assertion.
    control = page.get_by_role(role, name=name, exact=True)
    label = page.locator('label').filter(has=control)
    expect(label).to_have_count(1)
    expect(control).to_be_enabled()
    label.click()
    expect(control).to_be_checked()



def open_portfolio_settings(page):
    settings = page.locator('[data-testid="stSidebar"] details').filter(
        has=page.get_by_text('Portfolio settings', exact=True))
    expect(settings).to_have_count(1)
    if settings.get_attribute('open') is None:
        settings.locator('summary').click()
    expect(settings).to_have_attribute('open', '')


def main():
    # Streamlit reruns analytics before delivering server-derived approval state.
    # page.set_default_timeout does NOT change expect's separate 5s default.
    # Poll the actual state within the same bounded budget as browser actions.
    expect.set_options(timeout=60000)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        with (folder / 'server.log').open('w+') as log:
            server = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py',
                '--server.headless=true', f'--server.port={port}', '--server.address=127.0.0.1',
                '--browser.gatherUsageStats=false'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            try:
                url = f'http://127.0.0.1:{port}'
                for _ in range(120):
                    if server.poll() is not None:
                        raise RuntimeError('Streamlit exited before readiness')
                    try:
                        with urlopen(url + '/_stcore/health', timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.25)
                else:
                    raise RuntimeError('Streamlit readiness timeout')
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
                    errors = []
                    context.on('page', lambda page: page.on('pageerror', lambda exc: errors.append(str(exc))))
                    page = context.new_page()
                    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
                    page.goto(url)
                    page.set_default_timeout(60000)
                    expect(page.locator('.overview-disclosure')).to_be_visible()
                    expect(page.locator('.overview-disclosure')).to_contain_text('DEMONSTRATION DATA')
                    open_portfolio_settings(page)
                    for label in TABS:
                        page.get_by_role('tab', name=label, exact=True).click()
                        expect(page.get_by_role('tab', name=label, exact=True)).to_have_attribute('aria-selected', 'true')
                    packet = json.loads(download(page, 'Download research packet (JSON)', folder).read_text())
                    assert packet['approval_status'] == 'UNAPPROVED_RESEARCH'
                    assert abs(packet['scenario']['portfolio_return'] + .13045) < 1e-12
                    assert packet['backtest']['observations'] == 649
                    prices_path = download(page, 'Download analyzed prices (CSV)', folder)
                    assert len(list(csv.DictReader(io.StringIO(prices_path.read_text())))) == 900
                    page.get_by_role('tab', name=TABS[1], exact=True).click()
                    assert len(list(csv.DictReader(download(page, 'Export factor exposures (CSV)', folder).open()))) == 5
                    page.get_by_role('tab', name=TABS[2], exact=True).click()
                    scenario_packet = json.loads(download(page, 'Download scenario research packet (JSON)', folder).read_text())
                    assert scenario_packet == packet
                    page.get_by_role('tab', name=TABS[3], exact=True).click()
                    assert len(list(csv.DictReader(download(page, 'Export rolling backtest (CSV)', folder).open()))) == 649
                    comparison_rows = list(csv.DictReader(download(page, 'Export Historical / Gaussian comparison (CSV)', folder).open()))
                    assert len(comparison_rows) == 649
                    for column in ('Historical VaR', 'Gaussian VaR'):
                        assert all(float(row[column]) >= 0 for row in comparison_rows)
                    for model in ('historical', 'gaussian'):
                        column = 'Historical VaR' if model == 'historical' else 'Gaussian VaR'
                        hits = sum(float(row['Actual loss']) > float(row[column]) for row in comparison_rows)
                        assert hits == packet['model_benchmark']['models'][model]['breaches']
                    page.get_by_role('tab', name=TABS[4], exact=True).click()
                    approve = page.get_by_role('button', name='Approve current evidence-linked draft', exact=True)
                    expect(approve).to_be_disabled()
                    bundle = json.loads(download(page, 'Export evidence and draft (UNAPPROVED JSON)', folder).read_text())
                    assert bundle['status'] == 'UNAPPROVED_DRAFT' and bundle['review'] is None
                    reviewer = page.get_by_label('Reviewer / analyst identifier', exact=True)
                    reviewer.fill('AUTOMATED SYNTHETIC TEST')
                    reviewer.press('Enter')
                    expect(reviewer).to_have_value('AUTOMATED SYNTHETIC TEST')
                    acknowledgment = page.get_by_role('checkbox', name='I reviewed the calculations, assumptions, source labels, and all draft claims.', exact=True)
                    expect(acknowledgment).not_to_be_checked()
                    expect(approve).to_be_disabled()
                    select_labeled_control(page, 'checkbox', 'I reviewed the calculations, assumptions, source labels, and all draft claims.')
                    expect(approve, 'Valid reviewer and explicit acknowledgment must enable approval after the server rerun').to_be_enabled()
                    approve.click()
                    expect(page.get_by_text('ANALYST APPROVED', exact=False)).to_be_visible()
                    approved = json.loads(download(page, 'Export approved audit bundle (JSON)', folder).read_text())
                    assert approved['status'] == 'ANALYST_APPROVED'
                    assert approved['review']['draft_sha256'] == hashlib.sha256(approved['draft_markdown'].encode()).hexdigest()
                    evidence_sha = hashlib.sha256(json.dumps(approved['evidence'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                    assert approved['review']['evidence_sha256'] == evidence_sha
                    expect(page.get_by_label('Editable draft — edits revoke prior approvals', exact=True)).to_have_count(0)
                    select_labeled_control(page, 'radio', 'Edit Draft')
                    expect(page.get_by_text('ANALYST APPROVED', exact=False)).to_be_visible()
                    editor = page.get_by_label('Editable draft — edits revoke prior approvals', exact=True)
                    editor.fill(editor.input_value() + '\nEditorial test note.')
                    editor.press('Tab')
                    expect(page.get_by_text('Status: UNAPPROVED.', exact=False)).to_be_visible()
                    expect(page.get_by_role('button', name='Export approved audit bundle (JSON)', exact=True)).to_have_count(0)
                    select_labeled_control(page, 'radio', 'Preview')
                    expect(page.get_by_text('Editorial test note.', exact=False)).to_be_visible()
                    approve.click()
                    expect(page.get_by_text('ANALYST APPROVED', exact=False)).to_be_visible()
                    notional = page.get_by_label('Portfolio notional (USD)', exact=True)
                    notional.fill('1100000'); notional.press('Enter')
                    expect(page.get_by_text('Status: UNAPPROVED.', exact=False)).to_be_visible()
                    expect(page.get_by_role('button', name='Export approved audit bundle (JSON)', exact=True)).to_have_count(0)
                    # Same genuine exported prices exercise the CSV ingestion path.
                    select_labeled_control(page, 'radio', 'Upload CSV')
                    page.locator('input[type=file]').set_input_files(prices_path)
                    expect(page.get_by_text('Local CSV loaded.', exact=False)).to_be_visible()
                    expect(page.get_by_role('tab', name=TABS[0], exact=True)).to_be_visible()
                    page.get_by_role('button', name='Remove portfolio_prices.csv', exact=True).click()
                    invalid = folder / 'invalid.csv'; invalid.write_text('Wrong,Value\n2026-01-01,100\n')
                    page.locator('input[type=file]').set_input_files(invalid)
                    expect(page.get_by_text('Could not read price file: CSV must have a Date column', exact=True)).to_be_visible()
                    expect(page.get_by_role('tab', name=TABS[0], exact=True)).to_have_count(0)
                    select_labeled_control(page, 'radio', 'Synthetic demo')
                    expect(page.get_by_role('tab', name=TABS[0], exact=True)).to_be_visible()
                    equity = page.get_by_label('US Equity', exact=True)
                    equity.fill('0'); equity.press('Enter')
                    expect(page.get_by_text('Please resolve validation errors before running analytics.', exact=True)).to_be_visible()
                    equity.fill('26'); equity.press('Enter')
                    expect(page.get_by_role('tab', name=TABS[0], exact=True)).to_be_visible()
                    # Test all panels at mobile width; overflowing chart/table internals
                    # may scroll in their containers but the page must not overflow.
                    page.set_viewport_size({'width':390,'height':844})
                    for label in TABS:
                        page.get_by_role('tab', name=label, exact=True).click()
                        expect(page.get_by_role('tab', name=label, exact=True)).to_have_attribute('aria-selected', 'true')
                        page.wait_for_function('document.documentElement.scrollWidth <= window.innerWidth')
                        if os.environ.get('ATLAS_SCREENSHOT_DIR'):
                            evidence = Path(os.environ['ATLAS_SCREENSHOT_DIR'])
                            evidence.mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(evidence / f'streamlit-mobile-{TABS.index(label)}.png'), full_page=True)
                    assert page.locator('[data-testid="stException"]').count() == 0
                    assert not errors, errors
                    browser.close()
                print('PASS: Streamlit five tabs, CSV/JSON payloads, approval hashes/revocation, CSV failures, weights, mobile and JS errors')
            except Exception:
                log.seek(0)
                print(log.read(), file=sys.stderr)
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill(); server.wait()


if __name__ == '__main__':
    main()
