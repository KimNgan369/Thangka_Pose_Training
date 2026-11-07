from pathlib import Path
import json,csv,collections,zipfile,hashlib
from docx import Document
ROOT=Path.cwd(); QA=ROOT/'reports/lan5/qa'
REF=Path(r'I:\nam4\phan tich anh phat giao\report-chốt\tuần 5-6-7-lần 4\52300129_52300131_BaoCaoTienDo_Lan4_PhanTichTuTheThangka_CapNhat_20261010_rev6.docx')
RUN=ROOT/'outputs/notebook_runs/20261031_174634_seed20261021'
def j(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def csvr(p): return list(csv.DictReader(p.open(encoding='utf-8-sig')))
d=Document(REF)
with (QA/'reference.txt').open('w',encoding='utf-8') as f:
 for i,p in enumerate(d.paragraphs):
  f.write(f'P{i} [{p.style.name}] {p.text}\n')
 for i,t in enumerate(d.tables):
  f.write(f'TABLE {i}\n'+ '\n'.join(' | '.join(c.text for c in r.cells) for r in t.rows)+'\n')
print('SECTIONS',[(s.page_width.cm,s.page_height.cm,s.top_margin.cm,s.bottom_margin.cm,s.left_margin.cm,s.right_margin.cm) for s in d.sections])
for i in [0,2,3,4,5,6,16,50,60,80]:
 p=d.paragraphs[i]; print('STYLE',i,p.text[:80],p._p.xml[:2000])
rows=csvr(ROOT/'data/classification_manifest.csv')
print('L1',collections.Counter((r['level_1_code'],r['split']) for r in rows))
print('L2',collections.Counter((r['level_2_code'],r['split']) for r in rows))
print('RIGHTS',collections.Counter(r['rights_status'] for r in rows))
print('HASH',hashlib.sha256((ROOT/'data/classification_manifest.csv').read_bytes()).hexdigest())
for p in sorted((RUN/'image_classifier').glob('*/training_summary.json')):
 v=j(p);print('TRAIN',p.parent.name,{k:v[k] for k in ['best_epoch','epochs_completed','best_validation_selection_score']})
for folder in ['image_classifier','keypoint_classifier','pose_estimator']:
 print('FILES',folder,[p.name for p in (RUN/folder).iterdir() if p.is_file()])
print('ONTOLOGY',j(ROOT/'data/ontology.json'))
