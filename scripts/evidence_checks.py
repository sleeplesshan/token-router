"""Observable retrieval checks; no semantic probabilities or completeness claims."""
import ast


def assess_query_evidence(terms, matched):
    matched = set(matched)
    return {'query_anchor': 'satisfied' if matched else ('missing' if terms else 'unknown'),
            'matched_terms': [t for i, t in enumerate(terms) if i in matched],
            'unmatched_terms': [t for i, t in enumerate(terms) if i not in matched],
            'semantic_sufficiency': 'unknown'}


def complete_python_statements(text, targets, max_span=12, max_added=128):
    """Finish short syntax nodes crossing an excerpt boundary, without dropping cores.

    Large suites/functions are deliberately not expanded. Unknown boundaries remain
    explicit: this only completes short statements/expressions, not dependencies.
    """
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return targets, {'syntax': 'unknown', 'reason': 'parse_failed', 'added_lines': 0}
    selected = {n for t in targets for n in range(t['start_line'], t['end_line']+1)}
    original = len(selected)
    spans = sorted({(n.lineno, n.end_lineno) for n in ast.walk(tree)
                    if isinstance(n, (ast.stmt, ast.expr)) and hasattr(n, 'end_lineno')
                    and n.end_lineno and n.end_lineno > n.lineno}, key=lambda s:(s[1]-s[0],s[0]))
    # Bounded fixed point: adding one small node may intersect another. Monotonic
    # additions terminate; no more than max_added extra lines are ever admitted.
    changed = True
    while changed:
        changed = False
        for start, end in spans:
            if end-start+1 > max_span:
                continue
            node_lines = set(range(start,end+1))
            if selected & node_lines and not node_lines <= selected:
                extra = node_lines-selected
                if len(selected)-original+len(extra) <= max_added:
                    selected.update(extra); changed = True
    result = []
    for n in sorted(selected):
        if result and n == result[-1]['end_line']+1:
            result[-1]['end_line'] = n
        else:
            result.append({'start_line':n,'end_line':n,
                           'reason':'candidate evidence with bounded syntax context'})
    unresolved = sum(1 for a,b in spans if any(a<=t['end_line']<b or a<t['start_line']<=b for t in result))
    return result, {'syntax':'parsed', 'added_lines':len(selected)-original,
                    'crossing_nodes':unresolved, 'boundary_status':'partial' if unresolved else 'satisfied', 'semantic_sufficiency':'unknown'}


def required_pattern(term):
    import re
    if not term or any(c.isspace() for c in term):
        raise ValueError('required literals must be nonempty and contain no whitespace')
    return re.compile(r'(?<!\w)' + re.escape(term) + r'(?!\w)')


def assess_packet_evidence(terms, core_terms, source_terms, raw_slices, required, source_required):
    from query_matcher import compile_matcher
    from routing_policy import EvidenceChecks
    matcher = compile_matcher(terms)
    hits = set()
    present_required = set()
    patterns = [(term,required_pattern(term)) for term in required]
    # Each raw slice is separate: no synthetic match across omitted text.
    for raw in raw_slices:
        hits.update(matcher(raw))
        present_required.update(term for term,pattern in patterns if pattern.search(raw))
    return EvidenceChecks(tuple(source_terms),tuple(core_terms),
        tuple(t for i,t in enumerate(terms) if i in hits),
        tuple(t for t in required if not source_required.get(t,{}).get('count',0)),
        tuple(t for t in required if source_required.get(t,{}).get('count',0) and t not in present_required),
        'satisfied' if hits else ('missing' if terms else 'unknown'))
