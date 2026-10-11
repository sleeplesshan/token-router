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
