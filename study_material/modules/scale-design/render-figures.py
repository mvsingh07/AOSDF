"""Render the scale module's self-contained, browser-safe teaching figures."""
from pathlib import Path
from html import escape

out=Path(__file__).parent/'assets'
out.mkdir(exist_ok=True)
figures={
 'system-map':('THE REQUEST PATH','Start with the source of truth', [('Reader / editor','HTTP request'),('API fleet','Authorize + route'),('Primary DB','Metadata + versions'),('Object store','Document bodies')], 'Every optimization must preserve authorization and version rules.'),
 'requirements':('BEFORE COMPONENTS','State the promise first', [('User action','Open document'),('Access check','Who may see it?'),('Data read','Metadata + body'),('Response','p99 ≤ 400 ms')], 'A measured promise guides the architecture.'),
 'capacity':('DEMAND TO CAPACITY','Average is not peak', [('10M / day','≈ 116 opens/s'),('Peak × 10','≈ 1,160 opens/s'),('120 ms work','≈ 139 in flight'),('p99 target','≤ 400 ms')], 'Peak assumption and latency need production measurements.'),
 'scaling':('SHARED BOTTLENECK','More API workers, one database', [('Load balancer','Healthy routes'),('API A + B','Stateless workers'),('Connection pool','Bounded access'),('Primary DB','Shared limit')], 'Scale the saturated stage, not simply the visible server count.'),
 'api-boundary':('TRUST AT THE EDGE','Route, limit, then authorize', [('Edge proxy','TLS + size'),('API gateway','Route + quota'),('Document API','Resource check'),('Data store','Authorized read')], 'Gateway identity does not replace resource authorization.'),
 'caching':('FRESHNESS CONTRACT','A new version changes the key', [('GET v7','Request'),('Cache v7','Hit or miss'),('Origin','Fill on miss'),('Edit → v8','New cache key')], 'Permission and version belong in the cache policy.'),
 'queries':('DATABASE PRESSURE','Reduce work before adding nodes', [('List page','30 documents'),('Pool','Bound 12 / API'),('Index scan','One planned query'),('N + 1 trap','31 round trips')], 'Inspect plans, query counts, and pool wait time.'),
 'replication':('COPIES AND SPLITS','They solve different constraints', [('Primary','Authoritative writes'),('Replica','Async read copy'),('Shard A','Tenant group A'),('Shard B','Tenant group B')], 'A replica can lag; shards require routing and rebalancing.'),
 'consistency':('READ AFTER WRITE','Version 8 is confirmed', [('Editor save','Submit v7'),('Primary','Commit v8'),('Replica','Still v7'),('Next read','Route to v8')], 'A confirmed save requires an honest visibility rule.'),
 'concurrency':('SIMULTANEOUS EDITS','Compare before update', [('Alice + Bob','Read v7'),('Alice save','v7 → v8'),('Bob save','v7 mismatch'),('Conflict','Reload v8')], 'An affected-row count of zero is a conflict, not success.'),
 'compatibility':('SAFE EVOLUTION','Old and new versions coexist', [('Expand','Add field'),('Migrate','Safe default'),('Observe','Canary + metrics'),('Contract','Enforce later')], 'Every intermediate state needs a rollback path.'),
}
col=['#10263b','#15324a','#18465a','#1e5b65']
for filename,(eyebrow,title,nodes,foot) in figures.items():
    body=[]
    for i,(head,sub) in enumerate(nodes):
        x=28+i*223
        body.append(f'<rect x="{x}" y="144" width="198" height="142" rx="18" fill="{col[i]}" stroke="#46758a" stroke-width="1.5"/>')
        body.append(f'<circle cx="{x+28}" cy="171" r="13" fill="#54d4bd"/><text x="{x+28}" y="176" text-anchor="middle" class="num">{i+1}</text>')
        body.append(f'<text x="{x+18}" y="222" class="node">{escape(head)}</text><text x="{x+18}" y="251" class="sub">{escape(sub)}</text>')
        if i<3 and not (filename in {'replication', 'consistency'} and i>0) and not (filename in {'caching', 'queries', 'system-map'} and i>1):
            body.append(f'<path d="M{x+202} 215 H{x+219}" stroke="#65dfc4" stroke-width="3" marker-end="url(#arrow)"/>')
    if filename in {'consistency', 'system-map'}:
        body.append('<path d="M349 287 V311 H800 V287" fill="none" stroke="#65dfc4" stroke-width="2.5" marker-end="url(#arrow)"/>')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="402" viewBox="0 0 920 402" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(foot)}</desc><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#071a2b"/><stop offset="1" stop-color="#0c3443"/></linearGradient><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M1 1 L7 4 L1 7" fill="none" stroke="#65dfc4" stroke-width="1.5"/></marker></defs>
<style>.eyebrow{{font:700 13px system-ui,sans-serif;letter-spacing:2.1px;fill:#72e2cd}}.heading{{font:700 28px system-ui,sans-serif;fill:#f5fbfc}}.node{{font:700 18px system-ui,sans-serif;fill:#f7fbfc}}.sub{{font:500 14px system-ui,sans-serif;fill:#b6d6df}}.num{{font:700 13px system-ui,sans-serif;fill:#07304a}}.foot{{font:500 16px system-ui,sans-serif;fill:#b6d6df}}</style>
<rect width="920" height="402" rx="22" fill="url(#bg)"/><path d="M0 1 H920" stroke="#5dd9c0" stroke-width="3"/><text x="28" y="48" class="eyebrow">{escape(eyebrow)}</text><text x="28" y="91" class="heading">{escape(title)}</text>{''.join(body)}<path d="M28 331 H892" stroke="#447081"/><text x="28" y="366" class="foot">{escape(foot)}</text></svg>'''
    (out/f'{filename}.svg').write_text(svg)
mark='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" role="img" aria-label="Scale and system design"><rect width="48" height="48" rx="12" fill="#0b2c3e"/><circle cx="12" cy="13" r="4" fill="#69ddc5"/><circle cx="36" cy="13" r="4" fill="#69ddc5"/><circle cx="24" cy="35" r="5" fill="#fff"/><path d="M15 15 22 31M33 15 26 31M16 13h16" fill="none" stroke="#91e2d2" stroke-width="2.5"/></svg>'''
(out/'scale-mark.svg').write_text(mark)
print('Rendered',len(figures)+1,'SVGs')
