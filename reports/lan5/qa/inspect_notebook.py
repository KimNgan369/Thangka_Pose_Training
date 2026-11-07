import json
from pathlib import Path
p=Path('outputs/notebook_runs/20261031_174634_seed20261021/source_notebook.ipynb')
n=json.loads(p.read_text(encoding='utf-8'))
print('cells',len(n['cells']))
for i,c in enumerate(n['cells']):
 s=''.join(c.get('source',[])); outs=c.get('outputs',[])
 pics=[o for o in outs if 'data' in o and any(k.startswith('image/') for k in o['data'])]
 if c['cell_type']=='code' and (pics or any(k in s for k in ['plt.show()','display(','imshow(','plot(','confusion_matrix','heatmap','Figure('])):
  print(i,'images',len(pics),'out',len(outs),s[:260].replace('\n',' '))
