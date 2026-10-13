from pathlib import Path
import json
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).parent;D=Path('/Users/han/Documents/Token/token-router/docs/automatic-tool-review');s=json.loads((R/'combined-summary.json').read_text())
font_manager.fontManager.addfont('/System/Library/Fonts/AppleSDGothicNeo.ttc');plt.rcParams.update({'font.family':'Apple SD Gothic Neo','axes.unicode_minus':False,'font.size':11})
fig,axs=plt.subplots(1,3,figsize=(15,5.8));fig.patch.set_facecolor('#f8fafc');colors=['#334155','#168e76'];keys=['admitted_logs','excluded','all'];labels=['자동 발동 로그','제외 과제','전체 20회']
for ax,metric,title in zip(axs[:2],['total_tokens','whole_wall'],['총토큰 · 입력 + 출력','전체 완료 시간 · 초']):
 maximum=max(s['groups'][k][a][metric]for k in keys for a in ('plain','implicit'))
 for i,k in enumerate(keys):
  p,g=[s['groups'][k][a][metric]for a in ('plain','implicit')]
  for off,val,color in [(-.19,p,colors[0]),(.19,g,colors[1])]:
   ax.barh(i+off,val,height=.31,color=color);ax.text(val+maximum*.014,i+off,f'{val:,.0f}'if metric=='total_tokens'else f'{val:.2f}',va='center',fontsize=10)
  ax.text(.99,.87-i/3,f'{(g/p-1)*100:+.2f}%',transform=ax.transAxes,ha='right',color='#b45309'if g>p else'#117360',fontsize=12)
 ax.set_title(title,pad=18);ax.set_yticks(range(3),labels if metric=='total_tokens'else['']*3);ax.invert_yaxis();ax.set_xlim(0,maximum*1.45);ax.spines[['top','right']].set_visible(False)
axs[2].axis('off');axs[2].set_title('정확도와 자동 선택',pad=18)
axs[2].text(.02,.84,'정답 + 실제 근거\n미사용 50/50  ·  설치·연결 50/50',fontsize=15,color='#0f172a')
axs[2].text(.02,.57,'로그: 도구 자동 호출 4/4\n제외군: 도구 호출 0/6\n안내 파일 읽기: 0회',fontsize=14,color='#117360')
axs[2].text(.02,.22,'예외 없이 절감되는 것은 아닙니다.\n제외군도 도구 설명 비용을 부담합니다.\n전체 시간 개선은 미확인입니다.',fontsize=12,color='#92400e')
fig.suptitle('기본으로 연결하고, 필요한 로그에서 선택적으로 호출',fontsize=20,y=.98)
fig.legend([plt.Rectangle((0,0),1,1,color=c)for c in colors],['스킬·도구 미사용 · 일반 검색','스킬 + 로컬 도구 설치·연결'],loc='lower center',ncol=2,bbox_to_anchor=(.5,.045),frameon=False)
fig.text(.015,.012,'고정 16회 비교 + 별도 코드 제외 4회. gpt-6.1-sol medium · 기존/개발 자료 · 반복은 독립 과제가 아님 · 보편적 절감 보장 없음',fontsize=10,color='#475569')
fig.tight_layout(rect=(0,.14,1,.91));fig.savefig(D/'comparison.png',dpi=170);plt.close(fig)
