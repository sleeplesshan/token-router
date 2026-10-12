"""Observable retrieval checks; no semantic probabilities or completeness claims."""
import ast
import io


def assess_query_evidence(terms, matched):
    matched = set(matched)
    return {'query_anchor': 'satisfied' if matched else ('missing' if terms else 'unknown'),
            'matched_terms': [t for i, t in enumerate(terms) if i in matched],
            'unmatched_terms': [t for i, t in enumerate(terms) if i not in matched],
            'semantic_sufficiency': 'unknown'}


def complete_python_statements(text, targets, max_span=12, max_added=128, *, return_spans=None, return_definitions=None):
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
    if return_definitions is not None:
        pending=[(tree,())]
        while pending:
            node,scope=pending.pop()
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                qualified='.'.join((*scope,node.name));span=None
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and len(node.body)==2:
                    doc,returned=node.body
                    if (isinstance(doc,ast.Expr) and isinstance(doc.value,ast.Constant)
                            and isinstance(doc.value.value,str) and isinstance(returned,ast.Return)
                            and returned.end_lineno-returned.lineno+1<=max_span):
                        span=(returned.lineno,returned.end_lineno)
                return_definitions.append(dict(name=node.name,qualname=qualified,header=node.lineno,
                    span=span,eligible=span is not None and node.lineno in selected))
                scope=(*scope,node.name)
            pending.extend((child,scope) for child in reversed(list(ast.iter_child_nodes(node))))
    # Proposals use only the originally selected headers and this same parse.
    # They never compete with the released general AST completion budget.
    if return_spans is not None:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.lineno not in selected:
                continue
            if len(node.body) != 2 or not isinstance(node.body[1], ast.Return):
                continue
            doc, returned = node.body
            if (isinstance(doc, ast.Expr) and isinstance(doc.value, ast.Constant)
                    and isinstance(doc.value.value, str)
                    and returned.end_lineno-returned.lineno+1 <= max_span):
                return_spans.append((returned.lineno, returned.end_lineno))
        return_spans.sort()
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


def bounded_return_supplement(text, targets, base_packet, spans, render, accept, *,
                              max_lines=12, max_raw_chars=1024, max_rendered_chars=1024, accepted_spans=None):
    """Add whole short Returns without changing any released packet line.

    Separate experimental allowance, not a larger general AST budget. Rendering
    and admission are supplied by the existing router. No recursive expansion.
    """
    original = {n for t in targets for n in range(t['start_line'], t['end_line']+1)}
    selected = set(original)
    lines = list(io.StringIO(text, newline=''))
    raw_chars = 0
    admitted=[]
    for start, end in sorted(set(spans)):
        if not 1 <= start <= end <= len(lines) or end-start+1 > 12:
            continue
        extra = set(range(start, end+1))-selected
        chars = sum(len(lines[n-1]) for n in extra)
        if len(selected-original)+len(extra) <= max_lines and raw_chars+chars <= max_raw_chars:
            selected.update(extra)
            raw_chars += chars
            if extra:admitted.append((start,end))
    report = {'applied':False, 'new_lines':len(selected-original),
              'new_raw_chars':raw_chars, 'rendered_delta':0, 'reason':'no_addition'}
    if selected == original:
        return targets, base_packet, report
    proposed = []
    for n in sorted(selected):
        if proposed and n == proposed[-1]['end_line']+1:
            proposed[-1]['end_line'] = n
        else:
            proposed.append(dict(start_line=n,end_line=n,
                                 reason='candidate evidence with bounded syntax context'))
    trial = render(proposed)
    delta = len(trial.rendered)-len(base_packet.rendered)
    report['rendered_delta'] = delta
    def raw_map(packet):
        return {n:line for span,raw in zip(packet.ranges,packet.raw_slices)
                for n,line in enumerate(io.StringIO(raw, newline=''),span.start)}
    old, new = raw_map(base_packet), raw_map(trial)
    if not all(new.get(n) == line for n,line in old.items()):
        report['reason'] = 'preservation_failed'
    elif delta > max_rendered_chars:
        report['reason'] = 'rendered_addition_limit'
    elif not accept(trial):
        report['reason'] = 'existing_policy_or_output_limit'
    else:
        if accepted_spans is not None:accepted_spans.extend(admitted)
        report.update(applied=True,reason='bounded_return_added')
        return proposed, trial, report
    return targets, base_packet, report



def limit_return_target(name, definitions, base_targets, base_packet, m_targets, m_packet,
                        approved_spans, render, accept):
    """Only subtract approved M additions; never reallocate or infer query intent."""
    report=dict(applied=False,reason='unresolved',removed_lines=0,rendered_reduction=0)
    matches=[d for d in definitions if (d['qualname'] if '.' in name else d['name'])==name]
    if len(matches)!=1:
        report['reason']='ambiguous' if matches else 'unresolved'
        return m_targets,m_packet,report
    definition=matches[0]
    if not definition['eligible']:
        report['reason']='structure_or_header_ineligible'
        return m_targets,m_packet,report
    def raw_map(packet):
        return {n:line for span,raw in zip(packet.ranges,packet.raw_slices)
                for n,line in enumerate(io.StringIO(raw,newline=''),span.start)}
    b,m=raw_map(base_packet),raw_map(m_packet)
    span=tuple(definition['span']);goal=set(range(span[0],span[1]+1))
    if not goal<=m.keys() or (not goal<=b.keys() and span not in approved_spans):
        report['reason']='target_not_complete_or_approved'
        return m_targets,m_packet,report
    wanted=set(b)|goal
    if wanted==set(m):
        report['reason']='already_focused'
        return m_targets,m_packet,report
    proposed=[]
    for n in sorted(wanted):
        if proposed and n==proposed[-1]['end_line']+1:proposed[-1]['end_line']=n
        else:proposed.append(dict(start_line=n,end_line=n,reason='candidate evidence with bounded syntax context'))
    if wanted==set(b):proposed,trial=base_targets,base_packet
    else:trial=render(proposed)
    values=raw_map(trial)
    if not (b.keys()<=values.keys()<=m.keys() and goal<=values.keys()
            and all(m.get(n)==line for n,line in values.items())
            and all(values.get(n)==line for n,line in b.items())):
        report['reason']='preservation_failed'
    elif len(trial.rendered)>len(m_packet.rendered):report['reason']='rendered_growth'
    elif not accept(trial):report['reason']='existing_policy_or_output_limit'
    else:
        report.update(applied=True,reason='explicit_return_target',removed_lines=len(m)-len(values),
                      rendered_reduction=len(m_packet.rendered)-len(trial.rendered))
        return proposed,trial,report
    return m_targets,m_packet,report


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
