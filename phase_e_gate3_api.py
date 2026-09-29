"""Gate 3 assertions against the real recommendation endpoint.

No canonical IDs/specifications are created. Live pipeline evidence caches may
refresh, just as they do for a normal API request. Exit 1 means incomplete
coverage or a failed assertion; HTTP 200 alone is never Gate 3 success.
"""
import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'python'))

from retailer_product_registry import find_catalogued_mobile_id
from product_evidence_store import variant_text_is_ambiguous, variant_signature_from_text
from product_fit_signal_builder import smartphone_battery_signal, text_blob
from retail_price_evidence import CACHE_MAX_AGE_SECONDS

CASES = (
    ('mobile under 10000', 10000, None),
    ('mobile under 15000', 15000, None),
    ('best phone under 20000', 20000, None),
    ('Samsung phone under 20000', 20000, 'samsung'),
    ('best battery under ₹20k', 20000, None),
    ('best battery under ₹30k', 30000, None),
    ('best battery under ₹50k', 50000, None),
)


def check_payload(payload, http_status, budget, brand=None):
    errors, gaps = [], []
    picks = payload.get('recommendations') or []
    if http_status != 200:
        errors.append(f'HTTP {http_status}')
    if not picks:
        gaps.append('No eligible recommendations')
    elif len(picks) < 3:
        gaps.append(f'Only {len(picks)} eligible recommendations')
    if len(picks) > 3:
        errors.append('More than three recommendations')
    if payload.get('status') is not None and payload['status'] != ('PASS' if len(picks) >= 3 else 'PARTIAL'):
        errors.append('Misleading result sufficiency status')
    if (payload.get('stage_counts') or {}).get('qualifying_unique_models', 0) >= 3 and len(picks) < 3:
        errors.append('Three eligible models available but fewer than three returned')
    asins = [pick.get('asin') for pick in picks]
    if len(set(asins)) != len(asins) or any(not asin for asin in asins):
        errors.append('Duplicate or missing ASIN')
    for pick in picks:
        asin = pick.get('asin')
        try:
            price = float(pick['price'])
            fit = float(pick['fit_percent'])
            if not math.isfinite(price) or not 0 < price <= budget or not 50 <= fit <= 100:
                errors.append(f'{asin}: invalid price/budget/fit')
        except (KeyError, ValueError, TypeError):
            errors.append(f'{asin}: missing price/fit')
        if brand and str(pick.get('brand') or '').casefold() != brand.casefold():
            errors.append(f'{asin}: wrong brand')
        price_evidence = (pick.get('provenance') or {}).get('price_evidence') or {}
        source = urlparse(price_evidence.get('source_url') or '')
        bound_asin = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)', source.path, re.I)
        if (price_evidence.get('verified') is not True
                or price_evidence.get('price') != pick.get('price')
                or source.hostname not in ('amazon.in', 'www.amazon.in')
                or not bound_asin or bound_asin.group(1).upper() != asin):
            errors.append(f'{asin}: unverified or mismatched exact-listing price')
        if price_evidence.get('evidence_method') == 'recent_verified_cache':
            try:
                checked = datetime.fromisoformat(price_evidence['cached_evidence']['verified_at'].replace('Z', '+00:00'))
                if checked.tzinfo is None:
                    checked = checked.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - checked).total_seconds()
                if not 0 <= age <= CACHE_MAX_AGE_SECONDS:
                    raise ValueError('stale')
            except (KeyError, TypeError, ValueError):
                errors.append(f'{asin}: expired or untimestamped cached price')
        identity = pick.get('identity_evidence') or {}
        title = identity.get('source_title') or ''
        if not title or variant_text_is_ambiguous(title):
            errors.append(f'{asin}: missing/ambiguous source identity')
        expected = find_catalogued_mobile_id(
            retailer_product_id=asin or '', candidate_title=title,
            candidate_brand=pick.get('brand') or '',
        )
        if pick.get('canonical_product_id') != expected:
            errors.append(f'{asin}: canonical identity mismatch')
        if not expected:
            gaps.append(f'{asin}: canonical identity unresolved')
        expected_status = 'catalogued_exact_variant' if expected else 'canonical_unresolved'
        if identity.get('status') != expected_status:
            errors.append(f'{asin}: misleading identity status')
        variant = identity.get('variant') or {}
        if variant != variant_signature_from_text(title):
            errors.append(f'{asin}: variant does not match source evidence')
        if not variant.get('ram_gb') or not variant.get('storage_gb'):
            gaps.append(f'{asin}: exact physical RAM/storage not evidenced')

    diagnostics = payload.get('fit_diagnostics') or []
    if picks and not diagnostics:
        errors.append('Missing scoring diagnostics')
    battery_requested = 'good_battery' in (payload.get('intent', {}).get('preferred') or [])
    by_asin = {row.get('profile_asin'): row for row in diagnostics}
    for row in diagnostics:
        battery = row.get('battery_evidence')
        if battery is None:
            errors.append(f"{row.get('profile_asin')}: missing battery evidence")
            continue
        # Recompute from the same reported evidence, never from invented specs.
        expected = smartphone_battery_signal(text_blob(row, separator='; '))
        if battery != expected:
            errors.append(f"{row.get('profile_asin')}: battery evidence/scoring mismatch")
        criterion = next((c for c in row.get('criteria', []) if c.get('criterion') == 'battery'), None)
        if not criterion or criterion.get('match_score') != battery.get('match'):
            errors.append(f"{row.get('profile_asin')}: battery criterion mismatch")
    for pick in picks:
        row = by_asin.get(pick.get('asin'))
        if row is None or pick.get('battery_evidence') != row.get('battery_evidence'):
            errors.append(f"{pick.get('asin')}: recommendation/diagnostic mismatch")
        if battery_requested and (pick.get('battery_evidence') or {}).get('basis') in ('unknown', 'capacity_proxy'):
            gaps.append(f"{pick.get('asin')}: active-use battery endurance unverified")
    return {'status': 'FAIL' if errors else 'INCOMPLETE' if gaps else 'PASS',
            'errors': errors, 'coverage_gaps': gaps}


def check_repeat(before, after):
    """Changed raw evidence is not a repeat-stability failure."""
    def evidence(payload):
        fields = ('profile_asin', 'title', 'brand', 'identity_model', 'price',
                  'features', 'attributes', 'official_source', 'market_source')
        rows = [{key: row.get(key) for key in fields} for row in payload.get('fit_diagnostics', [])]
        return sorted(rows, key=lambda row: str(row.get('profile_asin')))
    unchanged = bool(evidence(before)) and evidence(before) == evidence(after)
    def picks(payload):
        return [(p.get('asin'), p.get('canonical_product_id'), p.get('price'),
                 p.get('fit_percent'), p.get('identity_evidence'))
                for p in payload.get('recommendations', [])]
    return {'evidence_unchanged': unchanged,
            'errors': ['Count/order/fit changed with unchanged evidence']
                      if unchanged and picks(before) != picks(after) else []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery-only', action='store_true')
    args = parser.parse_args()
    from shopping_api import app
    runs = []
    with app.test_client() as client:
        for query, budget, brand in CASES:
            if args.battery_only and 'battery' not in query:
                continue
            previous = None
            for repeat in (1, 2):
                response = client.get('/api/recommend', query_string={'q': query})
                payload = response.get_json(silent=True) or {}
                check = check_payload(payload, response.status_code, budget, brand)
                if previous is not None:
                    stability = check_repeat(previous, payload)
                    check['repeat_stability'] = stability
                    check['errors'].extend(stability['errors'])
                    if check['errors']:
                        check['status'] = 'FAIL'
                previous = payload
                runs.append({'query': query, 'repeat': repeat, 'http': response.status_code,
                             'check': check, 'payload': payload})
                print(query, repeat, check['status'], 'picks=', len(payload.get('recommendations') or []),
                      'errors=', check['errors'], 'gaps=', check['coverage_gaps'], flush=True)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding='utf-8')
    return 0 if all(run['check']['status'] == 'PASS' for run in runs) else 1


if __name__ == '__main__':
    raise SystemExit(main())
