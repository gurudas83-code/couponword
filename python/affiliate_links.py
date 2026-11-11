"""Apply the approved public Amazon tracking ID without changing offer eligibility."""
import html
import json
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

AMAZON_TAG = 'guru07cc-21'

def amazon_link(value):
    if not isinstance(value, str):
        return value
    parsed = urlsplit(value)
    if parsed.hostname not in {'amazon.in', 'www.amazon.in'} or parsed.scheme != 'https':
        return value
    pairs = [(key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True) if key != 'tag']
    return urlunsplit(parsed._replace(query=urlencode(pairs + [('tag', AMAZON_TAG)])))

def _tag_json(value):
    if isinstance(value, dict):
        return {key: _tag_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_tag_json(item) for item in value]
    return amazon_link(value) if isinstance(value, str) and value.startswith('https://') else value

def tag_public_artifact(root):
    for path in root.rglob('*.json'):
        path.write_text(json.dumps(_tag_json(json.loads(path.read_text(encoding='utf-8'))), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for path in root.rglob('*.html'):
        text = path.read_text(encoding='utf-8')
        def tag_anchor(match):
            anchor = match.group(0)
            href = re.search(r'href="([^"]+)"', anchor)
            if not href:
                return anchor
            old = html.unescape(href.group(1))
            new = amazon_link(old)
            if urlsplit(old).hostname not in {"amazon.in", "www.amazon.in"}:
                return anchor
            anchor = anchor.replace(href.group(0), 'href="'+html.escape(new, quote=True)+'"')
            rel = re.search(r'rel="([^"]*)"', anchor)
            tokens = set(rel.group(1).split()) if rel else set()
            tokens.update(['sponsored','nofollow','noopener'])
            attr = 'rel="'+' '.join(sorted(tokens))+'"'
            return anchor.replace(rel.group(0),attr) if rel else anchor[:-1]+' '+attr+'>'
        path.write_text(re.sub(r'<a\b[^>]*>',tag_anchor,text),encoding='utf-8')
