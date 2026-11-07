from docx import Document
from collections import Counter
import sys
p=sys.argv[1]
d=Document(p)
print('PARAGRAPHS',len(d.paragraphs),'TABLES',len(d.tables),'IMAGES',len(d.inline_shapes),'SECTIONS',len(d.sections))
for i,s in enumerate(d.sections):
 print('SECTION',i,'page_cm',round(s.page_width.cm,2),round(s.page_height.cm,2),'margins_cm',round(s.top_margin.cm,2),round(s.bottom_margin.cm,2),round(s.left_margin.cm,2),round(s.right_margin.cm,2),'orientation',s.orientation)
print('STYLES')
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption','List Paragraph']:
 try:
  st=d.styles[name]; pf=st.paragraph_format; f=st.font
  print(name,'font',f.name,'size_pt',f.size.pt if f.size else None,'bold',f.bold,'align',pf.alignment,'before_pt',pf.space_before.pt if pf.space_before else None,'after_pt',pf.space_after.pt if pf.space_after else None,'line',pf.line_spacing)
 except KeyError: pass
print('PARA COUNTS',Counter((p.style.name) for p in d.paragraphs))
for i,p in enumerate(d.paragraphs):
 t=p.text.strip()
 if t:
  f=p.runs[0].font if p.runs else None
  size=f.size.pt if f and f.size else None
  print(f'P{i} [{p.style.name}] size={size} bold={f.bold if f else None}: {t[:350]}')
