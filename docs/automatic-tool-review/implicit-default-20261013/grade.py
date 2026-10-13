import ast,re
from pathlib import Path
R=Path(__file__).parent

def norm(value,kind):
 v=value.strip().strip('`').strip()
 if kind=='expr':
  try:return ast.dump(ast.parse(v,mode='eval'),include_attributes=False)
  except (ValueError,SyntaxError):return v
 if kind=='expressions':return ';'.join(norm(x,'expr') for x in v.split(';'))
 if kind=='sequence':return ';'.join(x.strip().strip('`') for x in v.split(';'))
 return v

def observed(text,t):
 lines=(R/'sources'/t['file']).read_text().splitlines();seen=set()
 for line in text.splitlines():
  m=re.match(r'^(?:.*?'+re.escape(t['file'])+r'[:-])?\s*(\d+)(?:[:-]|\s+)(.*)$',line)
  if m:
   n=int(m[1])
   if 1<=n<=len(lines) and m[2].lstrip()==lines[n-1].lstrip():seen.add(n)
 return seen

def grade(d,t):
 seen=observed((R/(t['id']+'-seed.txt')).read_text(),t)
 for c in d['commands']:seen|=observed(c['aggregated_output'],t)
 scores=[]
 for f in t['facts']:
  found=[a for a in (d.get('answer') or {}).get('answers',[]) if a['id']==f['id']]
  a=found[0] if len(found)==1 else {};cit=a.get('evidence',[])
  factual=norm(a.get('answer',''),f['kind']) in [norm(x,f['kind']) for x in f['accepted_answers']]
  visible=bool(cit) and all(c['file']==t['file'] and type(c['start_line'])is int and type(c['end_line'])is int and 1<=c['start_line']<=c['end_line'] and set(range(c['start_line'],c['end_line']+1))<=seen for c in cit)
  cited={n for c in cit for n in range(c['start_line'],c['end_line']+1)}
  enough=all(set(g)<=cited for g in f['evidence_groups'])
  scores.append(dict(id=f['id'],factual=factual,citation_visible=visible,sufficient_groups=enough,grounded=bool(factual and visible and enough),citations=cit))
 return scores
