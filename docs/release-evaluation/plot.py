"""Render observed comparisons; matplotlib is a report-only dependency."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).parent;s=json.loads((P/'summary.json').read_text());m=s['model_comparison'];a=m['arms'];colors=['#7b8a9e','#25806d']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(12,8.2),layout='constrained');fig.suptitle('Token Router: installed skill vs ordinary search\n4 fixed paired tasks · gpt-6.1-sol / medium',fontsize=18,fontweight='bold')
for ax,key,title,fmt in [(axs[0,0],'total_tokens','Total input + output tokens',',.0f'),(axs[0,1],'total_cli_wall','Total episode time (seconds)', '.1f'),(axs[1,0],'correct_with_visible_evidence','Correct + visible evidence / 4 tasks','.0f')]:
 vals=[a[x][key] for x in ['plain','skill']];ax.bar(['No skill','Skill enabled'],vals,color=colors,width=.55);ax.set_title(title);ax.set_ylim(0,max(vals)*1.22)
 for i,v in enumerate(vals):ax.text(i,v+max(vals)*.025,format(v,fmt),ha='center',fontweight='bold')
axs[0,0].text(.5,.85,'+10.7% with skill',transform=axs[0,0].transAxes,ha='center',color='#a14432')
axs[0,1].text(.5,.85,'+10.2% observed; timing is noisy',transform=axs[0,1].transAxes,ha='center',color='#a14432',fontsize=10)
ax=axs[1,1];ax.axis('off');ax.text(0,1,'What actually happened',fontsize=14,fontweight='bold',va='top');ax.text(0,.87,'• Both arms used ordinary search on every task.\n• Router execution: 0; follow-up reads: 0.\n• No forced whole-file baseline.\n• Skills are optional guidance, not middleware.\n\nThis sample did NOT show token savings.\nNo claim of universal quality or speed.\n\nAll-run budget (includes first harness failure):\n133,723 tokens · 10 CLI calls · 137.5 s',va='top',linespacing=1.65)
fig.savefig(P/'comparison.png',dpi=180);fig.savefig(P/'comparison.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained');vals=[s['full_chars'],s['router_chars']];ax.barh(['Whole allowed files','Default initial packets'],vals,color=colors);ax.set_xlabel('Numbered source characters — NOT tokens');ax.set_title('Offline packet size only: 24 tasks / 8 projects\nInitial evidence complete: whole files 24/24; router packets 20/24')
for i,v in enumerate(vals):ax.text(v*.98,i,f'{v:,}',va='center',ha='right',color='white',fontweight='bold')
fig.savefig(P/'offline-context.png',dpi=180);plt.close(fig)
