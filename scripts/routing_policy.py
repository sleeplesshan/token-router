"""Pure routing contracts. Checks are observations, never probabilities."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Span:
    start: int
    end: int
    def __post_init__(self):
        if type(self.start) is not int or type(self.end) is not int or not 1 <= self.start <= self.end:
            raise ValueError('invalid span')

@dataclass(frozen=True)
class ScanFacts:
    total_lines: int
    source_chars: int
    selected_raw_chars: int
    source_terms: tuple[str, ...]
    source_stamp: tuple[int, ...]
    scan_complete: bool = True

@dataclass(frozen=True)
class Packet:
    ranges: tuple[Span, ...]
    raw_slices: tuple[str, ...]
    rendered: str
    def __post_init__(self):
        if len(self.ranges) != len(self.raw_slices):
            raise ValueError('packet range/content mismatch')
        for span,raw in zip(self.ranges,self.raw_slices):
            lines=raw.count('\n') + (1 if raw and not raw.endswith('\n') else 0)
            if lines != span.end-span.start+1:
                raise ValueError('packet source line count does not match coordinates')
        if any(a.end >= b.start for a,b in zip(self.ranges,self.ranges[1:])):
            raise ValueError('packet ranges must be sorted and disjoint')

@dataclass(frozen=True)
class EvidenceChecks:
    source_terms: tuple[str, ...]
    core_terms: tuple[str, ...]
    packet_terms: tuple[str, ...]
    absent_required: tuple[str, ...]
    lost_required: tuple[str, ...]
    packet_query_anchor: str
    semantic_sufficiency: str = 'unknown'

@dataclass(frozen=True)
class RouteDecision:
    action: str
    reason_codes: tuple[str, ...] = ()
    next_action: str | None = None


def decide_packet(*, checks, required, source_chars, full_chars, packet_chars,
                  has_candidates, small_limit, full_limit, candidate_limit,
                  output_limit, whole=False):
    full_fits = full_chars <= output_limit and (whole or source_chars <= full_limit)
    def otherwise(reason, next_action):
        return RouteDecision('auto_full' if full_fits else 'needs_targeted_read',
                             (reason,), None if full_fits else next_action)
    if whole:
        return otherwise('whole_scope', 'narrow_query')
    if source_chars <= small_limit:
        return otherwise('small_source', 'narrow_query')
    if checks.absent_required:
        return otherwise('required_literal_absent_in_this_source','change_search_scope')
    if checks.lost_required:
        return otherwise('required_literal_dropped_from_packet','read_missing_witnesses')
    if checks.packet_query_anchor == 'missing' and not required:
        return otherwise('no_packet_query_anchor','search_query_terms')
    if has_candidates and packet_chars <= min(candidate_limit,output_limit) and packet_chars <= full_chars*.85:
        return RouteDecision('auto_candidates')
    return otherwise('insufficient_bounded_reduction','narrow_query')
