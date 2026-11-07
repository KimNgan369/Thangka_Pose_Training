exec(open('reports/lan5/qa/inspect_data.py',encoding='utf-8').read().split("d=Document(REF)")[0])
from PIL import Image,ImageDraw
from lxml import etree
ps=sorted(QA.glob('ref-*.png'))
for k in range(0,len(ps),6):
 out=Image.new('RGB',(1275,1740),'#ccc')
 for i,p in enumerate(ps[k:k+6]):
  im=Image.open(p); im.thumbnail((425,840)); out.paste(im,((i%3)*425,(i//3)*870)); ImageDraw.Draw(out).text(((i%3)*425+10,(i//3)*870+842),p.stem,fill='black')
 out.save(QA/f'ref_contact_{k//6}.png')
d=Document(REF)
inv={}
with zipfile.ZipFile(REF) as z:
 for name in z.namelist(): inv[name]={'size':len(z.read(name)),'sha256':hashlib.sha256(z.read(name)).hexdigest()}
(QA/'package_inventory.json').write_text(json.dumps(inv,indent=2),encoding='utf-8')
roles={}
for i in [0,2,3,4,5,6,7,14,16,54,59,61]:
 p=d.paragraphs[i]; roles[str(i)]={'text':p.text,'xml':etree.tostring(p._p,encoding='unicode')}
(QA/'template_roles.json').write_text(json.dumps(roles,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text(f'''# Báo cáo lần 5 theo mẫu lần 4
Reference: {REF}
SHA256: {hashlib.sha256(REF.read_bytes()).hexdigest()}
Reference render: reference.pdf and ref-01 through ref-{len(ps):02}.png; {len(ps)} pages; one section.
Page system: Letter 21.59 x 27.94 cm; margins top 1.905, bottom 1.82915, left 2.08315, right 1.98085 cm. Preserve sectPr including footer/header distances and first-page configuration.
Typography: Normal Times New Roman 13 pt. Source direct body pPr at paragraph 54; Heading 1 pattern p59 (14 pt), Heading 2 p61 (14 pt); cover p0–15. Exact XML captured in template_roles.json. Preserve style definitions, numbering, theme, media and relationships. Preserve cover logo and existing frame.
Slots: word/document.xml body p0–15 cover; replace p3 report number and p5 period with weeks 8–9–10 and cutoff 01/11/2026, preserve names, adviser and title. Rest of body rewritten with cloned source paragraph/table patterns. Old figures are removed from body; new quantitative tables and figures describe current training. Reuse headings 1–18 with updated subheadings. TOC regenerated for current content. Long content may repeat source patterns and paginate naturally.
Tables: clone source table properties, use full text width and explicit grids for new schema; repeat header, auto row height, no split rows. Header/body typography follows reference 10–11 pt when needed; source palette preserved.
Header/footer: source empty paragraphs and any existing page fields retained. Package parts preserve-only except document.xml, settings updateFields, new media relationships/content types needed for figures, and document property title. Field refresh performed with Word on copied output; final PNG render via Word PDF + packaged Poppler because Windows runtime manifest has libreOfficeVersion=null.
Inventory: package_inventory.json stores every reference package member size/hash. Reference stays unchanged. Cover, page geometry and styles are fidelity gates. No historical numeric claims or stale charts are retained in updated body.
Content flow: cover; TOC; abbreviations; decisions and abstract; 18 scientific progress sections; internal evidence references. Detailed interpretation must distinguish validation/test, pose/classification denominators, old/new protocol, performed/proposed work.
''',encoding='utf-8')
rows=csvr(ROOT/'data/classification_manifest.csv'); lookup={r['image_id']:r for r in rows}
pr=csvr(RUN/'deployment/test_predictions.csv'); kp=csvr(RUN/'keypoint_classifier/test_predictions.csv')
print('GROUP_COMPARISON',j(RUN/'SUMMARY.json')['image_selection']['group_comparison'])
print('L1 confusion')
for code in ['C1.1','C1.2','C1.3','C1.4']:
 sub=[r for r in pr if r['gold_l1']==code]; ks=[r for r in kp if r['gold_l1']==code]
 print(code,len(sub),collections.Counter(r['pred_l1'] for r in sub),'KP',collections.Counter(r['pred_l1'] for r in ks))
print('decisions',collections.Counter(r['decision_level'] for r in pr))
for field in ['visibility','occlusion_type']:
 for value in sorted(set(lookup[r['image_id']][field] for r in pr)):
  sub=[r for r in pr if lookup[r['image_id']][field]==value]
  print(field,value,len(sub),sum(r['gold_l1']==r['pred_l1'] for r in sub))
for name,lo,hi in [('small',0,.1),('medium',.1,.3),('large',.3,2)]:
 sub=[r for r in pr if lo<=float(lookup[r['image_id']]['bbox_w'])*float(lookup[r['image_id']]['bbox_h'])/(float(lookup[r['image_id']]['width'])*float(lookup[r['image_id']]['height']))<hi]
 print('size',name,len(sub),sum(r['gold_l1']==r['pred_l1'] for r in sub))
print('ERRORS',[(r['image_id'],r['gold_l1'],r['gold_l2'],r['pred_l1'],r['final_code']) for r in pr if r['gold_l1']!=r['pred_l1'] or (r['pred_l2'] and r['pred_l2']!=r['gold_l2'])])
