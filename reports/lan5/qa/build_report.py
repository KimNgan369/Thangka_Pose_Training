from pathlib import Path
from copy import deepcopy
import json,csv,hashlib,zipfile,collections,re
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from PIL import Image,ImageDraw,ImageFont
ROOT=Path.cwd(); OUT=ROOT/'reports/lan5'; QA=OUT/'qa'
REF=Path(r'I:\nam4\phan tich anh phat giao\report-GK-CK\52300129_52300131_report.docx')
RUN=ROOT/'outputs/notebook_runs/20261031_174634_seed20261021'
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def cr(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
S=js(RUN/'SUMMARY.json'); rows=cr(ROOT/'data/classification_manifest.csv'); pred=cr(RUN/'deployment/test_predictions.csv'); kp=cr(RUN/'keypoint_classifier/test_predictions.csv'); ont=js(ROOT/'data/ontology.json')
lookup={r['image_id']:r for r in rows}
fmt=lambda x:f'{float(x):.4f}'.replace('.',',')
TEXT_REPLACEMENTS=[
 (r'\bnested cross-validation\b','kiểm định chéo lồng nhau'),
 (r'\bcross-validation\b','kiểm định chéo'),
 (r'\bend-to-end\b','toàn quy trình'),
 (r'\bout-of-distribution\b','ngoài phạm vi dữ liệu'),
 (r'\bL2 oracle\b','L2 khi đã biết nhãn L1'),
 (r'\bmacro-F1\b','F1 trung bình theo lớp'),
 (r'\bkeypoint classifier\b','bộ phân loại dựa trên điểm mốc'),
 (r'\bimage classifier\b','bộ phân loại ảnh'),
 (r'\btrain set\b','tập huấn luyện'),
 (r'\btraining set\b','tập huấn luyện'),
 (r'\bvalidation set\b','tập xác thực'),
 (r'\btest set\b','tập kiểm thử'),
 (r'\bmetric schema 2\b','quy ước đo lường phiên bản 2'),
 (r'\bpose estimator\b','mô hình ước lượng tư thế'),
 (r'\braw accuracy\b','độ chính xác thô'),
 (r'\bkeypoints?\b','điểm mốc'),
 (r'\bcheckpoint\b','bản trọng số đã lưu'),
 (r'\bmanifest\b','bảng kê khai dữ liệu'),
 (r'\bcoverage\b','tỷ lệ có kết quả'),
 (r'\baccuracy\b','độ chính xác'),
 (r'\bprecision\b','độ chính xác dự đoán'),
 (r'\brecall\b','tỷ lệ nhận diện đúng'),
 (r'\bsplit\b','phân chia dữ liệu'),
 (r'\bvalidation\b','xác thực'),
 (r'\btrain\b','huấn luyện'),
 (r'\btest\b','kiểm thử'),
 (r'\bseed\b','lần khởi tạo'),
 (r'\bepochs?\b','vòng huấn luyện'),
 (r'\brun\b','lượt chạy'),
 (r'\bcrops?\b','ảnh cắt'),
 (r'\bschema\b','quy ước đánh giá'),
 (r'\bhash\b','mã kiểm tra'),
 (r'\bbootstrap\b','lấy mẫu lặp để ước lượng độ bất định'),
 (r'\blogistic\b','hồi quy logistic'),
 (r'\bnotebook\b','sổ thực nghiệm'),
 (r'\bfallback\b','lùi về nhãn tổng quát'),
 (r'\bensemble\b','tổ hợp mô hình'),
 (r'\bbbox\b','khung bao'),
 (r'\bOOD\b','ngoài phạm vi dữ liệu'),
 (r'\bdemo\b','bản minh họa'),
 (r'\bsupport\b','số mẫu'),
 (r'\bpipeline\b','quy trình'),
 (r'\bclassifier\b','bộ phân loại'),
 (r'\barchitecture\b','kiến trúc'),
 (r'\bprobability\b','xác suất'),
 (r'\bconfidence\b','mức tin cậy'),
 (r'\btemperature scaling\b','hiệu chỉnh xác suất'),
 (r'\btemperature\b','hệ số điều chỉnh'),
 (r'\bloss\b','hàm mất mát'),
 (r'\bmetrics?\b','chỉ số'),
 (r'\bthreshold\b','ngưỡng'),
 (r'\bfeature\b','đặc trưng'),
 (r'\bmodel\b','mô hình'),
 (r'\bimage\b','ảnh'),
 (r'(?<!YOLO11n-)\bpose\b','tư thế'),
 (r'\braw\b','thô'),
 (r'\bargmax\b','lớp có xác suất cao nhất'),
 (r'\bmetric\b','chỉ số'),
 (r'\bexact\b','đúng hoàn toàn'),
]
def readable(text):
 for pattern,replacement in TEXT_REPLACEMENTS:text=re.sub(pattern,replacement,text,flags=re.IGNORECASE)
 return text
d=Document(REF); paras=list(d.paragraphs); body_pr=deepcopy(paras[54]._p.pPr); h1_pr=deepcopy(paras[59]._p.pPr); h2_pr=deepcopy(paras[61]._p.pPr)
table_pr=deepcopy(d.tables[0]._tbl.tblPr)
def replace(p,text):
 props=deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
 p.clear(); r=p.add_run(readable(text))
 if props is not None:r._r.insert(0,props)
for cover_title in (paras[4],paras[18]):
 replace(cover_title,'BÁO CÁO TIẾN ĐỘ LẦN 5')
 cover_title.style=d.styles['Title']; cover_title.alignment=WD_ALIGN_PARAGRAPH.CENTER
 cover_title.paragraph_format.space_after=Pt(10)
for project_title in (paras[6],paras[20]):
 replace(project_title,'NHÂN VẬT\nTRONG ẢNH NGHỆ THUẬT PHẬT GIÁO\nTuần 8–9–10')
border=OxmlElement('w:pBdr')
for side in ['top','bottom','left','right','between']:
 e=OxmlElement('w:'+side);e.set(qn('w:val'),'nil');border.append(e)
for cover_title in (paras[4],paras[18]):cover_title._p.get_or_add_pPr().append(deepcopy(border))
for cover_title in (paras[4],paras[18]):
 for r in cover_title.runs:r.font.name='Times New Roman';r.font.size=Pt(14);r.bold=True;r.font.color.rgb=RGBColor(0,0,0)
# Retain cover components; replace all subsequent content in a working copy.
start=d._element.body.index(paras[28]._p)
for el in list(d._element.body)[start:]:
 if el.tag!=qn('w:sectPr'):d._element.body.remove(el)
tblno=0; figno=0
caption_registry={'Hình':[],'Bảng':[]};pending_caption_lists=[]
def p(text='',kind='body'):
 after_table=len(d._element.body)>1 and d._element.body[-2].tag==qn('w:tbl')
 x=d.add_paragraph(); pr=deepcopy(h1_pr if kind=='h1' else h2_pr if kind=='h2' else body_pr)
 if x._p.pPr is not None:x._p.remove(x._p.pPr)
 x._p.insert(0,pr)
 x.style='Heading 1' if kind=='h1' else 'Heading 2' if kind=='h2' else 'Normal'
 x.paragraph_format.keep_with_next=kind!='body';x.paragraph_format.widow_control=True
 x.paragraph_format.space_after=Pt(6 if kind=='body' else 5)
 x.paragraph_format.space_before=Pt(10 if kind=='h1' else 5 if kind=='h2' else 6 if after_table else 0)
 x.paragraph_format.line_spacing=1.08
 r=x.add_run(readable(text));r.font.name='Times New Roman';r.font.size=Pt(14 if kind!='body' else 13);r.font.color.rgb=RGBColor(0,0,0);r.bold=kind!='body'
 if kind=='body':x.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
 return x
def h(t):return p(t,'h1')
def sub(t):return p(t,'h2')
def field_code(paragraph,instruction,result=''):
 run=paragraph.add_run();el=OxmlElement('w:fldChar');el.set(qn('w:fldCharType'),'begin');el.set(qn('w:dirty'),'true');run._r.append(el)
 run=paragraph.add_run();el=OxmlElement('w:instrText');el.set(qn('xml:space'),'preserve');el.text=' '+instruction+' ';run._r.append(el)
 run=paragraph.add_run();el=OxmlElement('w:fldChar');el.set(qn('w:fldCharType'),'separate');run._r.append(el)
 if result:paragraph.add_run(str(result))
 run=paragraph.add_run();el=OxmlElement('w:fldChar');el.set(qn('w:fldCharType'),'end');run._r.append(el)
def caption(paragraph,label,number,title):
 title=readable(title)
 caption_registry[label].append(f'{label} {number}. {title}')
 paragraph.style=d.styles['Caption'] if 'Caption' in d.styles else d.styles['Normal']
 paragraph.add_run(label+' ')
 field_code(paragraph,f'SEQ {label} \\* ARABIC',number)
 paragraph.add_run('. '+title)
 paragraph.paragraph_format.keep_with_next=True
 for r in paragraph.runs:r.font.name='Times New Roman';r.font.size=Pt(11);r.italic=True;r.font.color.rgb=RGBColor(0,0,0)
def table(title,headers,data,widths=None):
 global tblno
 tblno+=1
 cap=p();cap.alignment=WD_ALIGN_PARAGRAPH.CENTER;caption(cap,'Bảng',tblno,title)
 t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 t._tbl.remove(t._tbl.tblPr);t._tbl.insert(0,deepcopy(table_pr))
 widths=widths or [17.5/len(headers)]*len(headers)
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'5');b.set(qn('w:color'),'777777');borders.append(b)
 old=t._tbl.tblPr.find(qn('w:tblBorders'))
 if old is not None:t._tbl.tblPr.remove(old)
 t._tbl.tblPr.append(borders)
 margins=OxmlElement('w:tblCellMar')
 for side in ['top','bottom','left','right']:
  e=OxmlElement('w:'+side);e.set(qn('w:w'),'75');e.set(qn('w:type'),'dxa');margins.append(e)
 t._tbl.tblPr.append(margins)
 for j,w in enumerate(widths):t.columns[j].width=Cm(w)
 for i,vals in enumerate([headers]+data):
  rr=t.rows[0] if i==0 else t.add_row()
  pr=rr._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
  if i==0:pr.append(OxmlElement('w:tblHeader'))
  for j,v in enumerate(vals):
   c=rr.cells[j];c.width=Cm(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   x=c.paragraphs[0];x.paragraph_format.space_after=Pt(2);x.paragraph_format.space_before=Pt(2);x.paragraph_format.line_spacing=1.0
   x.paragraph_format.keep_with_next=i<2
   x.alignment=WD_ALIGN_PARAGRAPH.CENTER if j>0 and len(str(v))<22 else WD_ALIGN_PARAGRAPH.LEFT
   r=x.add_run(readable(str(v)));r.font.name='Times New Roman';r.font.size=Pt(11);r.bold=i==0;r.font.color.rgb=RGBColor(0,0,0)
 return t
def image(path,caption_text,comment=None,width=16.7):
 global figno
 figno+=1
 x=d.add_paragraph();x.alignment=WD_ALIGN_PARAGRAPH.CENTER;x.paragraph_format.keep_with_next=True;x.add_run().add_picture(str(path),width=Cm(width))
 x=d.add_paragraph();x.alignment=WD_ALIGN_PARAGRAPH.CENTER;caption(x,'Hình',figno,caption_text);x.paragraph_format.keep_with_next=bool(comment)
 if comment:p(comment)
def demo_case_page(cases,offset,kind):
 for i,(image_id,comment_text) in enumerate(cases):
  row=next(r for r in pred if r['image_id']==image_id)
  detail=(f"đầu ra {row['final_code']} khớp nhãn tham chiếu" if kind=='good' else f"đầu ra {row['final_code'] or 'Không xác định'} chưa khớp đầy đủ nhãn tham chiếu")
  image(QA/f'case_{kind}_{image_id}.png',f'Ca {offset+i+1} — {image_id}: {detail}',comment_text)
  page()
def page():d.add_page_break()
LEVEL1={v['code']:v['vi'] for v in ont['level_1']};LEVEL2={v['code']:v['vi'] for v in ont['level_2']}
GOOD_CASES=[
 ('THK000431','Kết quả chi tiết phù hợp nhãn tham chiếu; ảnh thể hiện tư thế ngồi bắt chéo.'),
 ('THK000701','Mô hình trả đúng nhãn chi tiết C2.3 theo hồ sơ tham chiếu; trường hợp này minh họa khả năng phân biệt một dạng ngồi cụ thể.'),
 ('HAR_3314415','Kết quả C2.6 khớp nhãn tham chiếu ở cả mức tổng quát và chi tiết.'),
 ('CHINA777_P01_28','Mô hình nhận đúng lớp nằm nghiêng ở mức chi tiết; đây là một trường hợp khớp nhãn trong nhóm có ít ảnh.'),
 ('THK001031','Nhãn tổng quát C1.3 được trả đúng; nhãn chi tiết được để trống theo hồ sơ tham chiếu, nên đây là kết quả đúng ở mức tổng quát.'),
 ('THK000419','Đầu ra C1.1 phù hợp nhãn tham chiếu tổng quát. Không có nhãn L2 tham chiếu để xác nhận mức chi tiết.'),
]
NEEDS_REVIEW=[
 ('THK000705','Nhãn tổng quát C1.1 đúng, nhưng mô hình chọn C2.3 thay cho C2.2. Sai lệch nằm ở phân biệt hai dạng tư thế cùng nhóm ngồi.'),
 ('THK000914','Nhãn tổng quát C1.1 đúng; nhãn tham chiếu không có L2. Vì vậy, đầu ra C2.1 vượt mức chi tiết có thể xác nhận từ hồ sơ đánh giá.'),
 ('THK000279','Mô hình trả C1.2 trong khi nhãn tham chiếu là C1.3. Sai lệch đã xuất hiện ở mức tư thế tổng quát; độ tin cậy L1 lưu trong hồ sơ là 43,1%.'),
 ('THK000177_3ef4f0fe8c_3','Nhãn tổng quát C1.2 đúng, nhưng C2.6 được trả thay cho C2.7. Trường hợp này cho thấy mức tin cậy L1 cao không bảo đảm nhãn chi tiết đúng.'),
 ('THK000748','Mô hình giữ đúng nhóm ngồi C1.1 nhưng trả C2.3 thay cho C2.5. Cần xem riêng sai lệch ở lớp tư thế chi tiết.'),
 ('HAR_98818','Nhãn tham chiếu là đứng C1.2/C2.6, còn đầu ra cuối là C1.1. Đây là nhầm lẫn ở mức tổng quát; hồ sơ cho thấy độ tin cậy L1 48,0%.'),
]
def wrap_text(draw,text,font,max_width):
 words=text.split();lines=[];line=''
 for word in words:
  trial=(line+' '+word).strip()
  if draw.textbbox((0,0),trial,font=font)[2] <= max_width:line=trial
  else:
   if line:lines.append(line)
   line=word
 if line:lines.append(line)
 return lines
def create_case_cards():
 cards={r['image_id']:r for r in pred};font_path='C:/Windows/Fonts/arial.ttf'
 title=ImageFont.truetype(font_path,36);label=ImageFont.truetype(font_path,27);small=ImageFont.truetype(font_path,24)
 for group,cases,color in [('good',GOOD_CASES,'#2d6f5e'),('review',NEEDS_REVIEW,'#a14f4f')]:
  for image_id,_ in cases:
   row=cards[image_id];m=lookup[image_id];source=ROOT/'data'/m['crop_path']
   if not source.exists():source=ROOT/'data'/m['image_path']
   src=Image.open(source).convert('RGB');src.thumbnail((820,740))
   card=Image.new('RGB',(1600,1000),'#fbfaf7');dr=ImageDraw.Draw(card)
   dr.rounded_rectangle((24,24,1576,112),radius=20,fill=color)
   dr.text((55,45),('CA KHỚP NHÃN THAM CHIẾU' if group=='good' else 'CA CẦN RÀ SOÁT'),font=title,fill='white')
   dr.rounded_rectangle((35,145,925,965),radius=18,fill='white',outline='#d7d4cc',width=2)
   dr.rectangle((55,165,905,925),fill='#efeee9')
   card.paste(src,(55+(850-src.width)//2,165+(760-src.height)//2))
   x=970;y=160;dr.text((x,y),image_id,font=title,fill='#222222');y+=70
   gold_l1=row['gold_l1'];gold_l2=row['gold_l2'];final=row['final_code']
   def show(code):
    if not code:return 'Không xác định'
    return f'{code} — {LEVEL2.get(code,LEVEL1.get(code,""))}'
   fields=[('Nhãn tham chiếu',show(gold_l1)+((' / '+show(gold_l2)) if gold_l2 else ' / L2 để trống')),
           ('Đầu ra cuối',show(final) if final else 'Không xác định'),
           ('Nhãn chi tiết được cân nhắc',show(row['l2_candidate']) if row['l2_candidate'] else 'Không có'),
           ('Mức tin cậy L1',f"{float(row['l1_confidence'])*100:.1f}%"),
           ('Mức tin cậy nhãn chi tiết',f"{float(row['l2_confidence'])*100:.1f}%")]
   for head,val in fields:
    dr.text((x,y),head,font=label,fill=color);y+=39
    for line in wrap_text(dr,val,small,570):dr.text((x,y),line,font=small,fill='#222222');y+=34
    y+=18
   dr.line((x,900,1530,900),fill='#d7d4cc',width=2)
   dr.text((x,916),'Nguồn: dự đoán đã lưu của lượt đánh giá chính',font=small,fill='#555555')
   card.save(QA/f'case_{group}_{image_id}.png')
def create_pose_batch_composites():
 base=RUN/'pose_estimator/geometry_test';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
 for n in range(3):
  pair=[]
  for suffix,label in [('labels','Nhãn tham chiếu'),('pred','Kết quả mô hình')]:
   im=Image.open(base/f'val_batch{n}_{suffix}.jpg').convert('RGB')
   pair.append((im.copy(),label))
  gap=34;width=sum(im.width for im,_ in pair)+gap;height=max(im.height for im,_ in pair)+62
  canvas=Image.new('RGB',(width,height),'white');dr=ImageDraw.Draw(canvas);y=0
  x=0
  for im,label in pair:
   dr.text((x+8,8),label,font=font,fill='#222222')
   canvas.paste(im,(x,52));x+=im.width+gap
  canvas.save(QA/f'pose_val_batch{n}_comparison.png')
create_case_cards();create_pose_batch_composites()
def chart_curves():
 im=Image.new('RGB',(1600,760),'white');dr=ImageDraw.Draw(im)
 font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/times.ttf',22)
 colors=['#24527a','#287b74','#a96926','#873c53','#6b60a0','#777777']
 dr.text((110,20),'Điểm lựa chọn checkpoint trên validation qua các epoch',fill='black',font=font)
 for val in [0,.2,.4,.6,.8,1]:
  y=620-val*500;dr.line((110,y,1520,y),fill='#dddddd',width=2);dr.text((30,y-15),str(val),fill='black',font=small)
 dr.line((110,120,110,620),fill='black',width=2)
 for tick in range(0,81,10):
  xx=110+tick/80*1410;dr.text((xx-10,625),str(tick),fill='black',font=small)
 for i,fp in enumerate(sorted((RUN/'image_classifier').glob('*/history.json'))):
  hh=js(fp); hh=hh if isinstance(hh,list) else hh['history']
  points=[(110+v['epoch']/80*1410,620-v['selection_score']*500) for v in hh]
  dr.line(points,fill=colors[i],width=4)
  x=110+(i%3)*475;y=675+(i//3)*35
  dr.line((x,y+12,x+35,y+12),fill=colors[i],width=4);dr.text((x+42,y),fp.parent.name.replace('_seed',' / '),fill='black',font=small)
 im.save(QA/'curves.png')
chart_curves()
p('MỤC LỤC').alignment=WD_ALIGN_PARAGRAPH.CENTER
toc=d.add_paragraph();r=toc.add_run();e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'begin');r._r.append(e)
r=toc.add_run();e=OxmlElement('w:instrText');e.set(qn('xml:space'),'preserve');e.text=' TOC \\o "1-2" \\h \\z \\u ';r._r.append(e)
r=toc.add_run();e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'end');r._r.append(e)
page()
def add_caption_list(label):
 x=d.add_paragraph();x.paragraph_format.space_before=Pt(4);x.paragraph_format.space_after=Pt(8)
 field_code(x,f'TOC \\h \\z \\c "{label}"','')
 pending_caption_lists.append((x,label))
for list_title,list_label in [('DANH MỤC HÌNH','Hình'),('DANH MỤC BẢNG BIỂU','Bảng')]:
 x=p(list_title);x.alignment=WD_ALIGN_PARAGRAPH.CENTER
 for r in x.runs:r.bold=True;r.font.size=Pt(14)
 add_caption_list(list_label);page()
p('DANH MỤC TỪ VIẾT TẮT').alignment=WD_ALIGN_PARAGRAPH.CENTER
table('Các thuật ngữ sử dụng trong báo cáo',['Thuật ngữ','Giải thích'],[
 ['L1 / L2','Nhãn tư thế ở mức tổng quát / nhãn mô tả tư thế cụ thể hơn'],['Khung bao / IoU','Vùng bao quanh nhân vật / mức chồng lấp giữa vùng dự đoán và vùng tham chiếu'],['PCK / OKS','Hai chỉ số đánh giá độ gần giữa điểm mốc dự đoán và điểm đã gán'],['Độ chính xác dự đoán / tỷ lệ nhận diện đúng','Tỷ lệ dự đoán được xác nhận là đúng / tỷ lệ ảnh tham chiếu được nhận diện'],['F1 trung bình theo lớp','Điểm trung bình giữa các lớp, trong đó lớp ít mẫu vẫn có trọng số ngang nhau'],['Tỷ lệ có kết quả','Tỷ lệ ảnh mà hệ thống đưa ra câu trả lời ở mức đang xét'],['L2 khi đã biết nhãn L1','Phép đo nhãn chi tiết trong điều kiện đã biết trước nhãn tổng quát tham chiếu'],['ECE / Brier','Hai phép đo mức phù hợp giữa độ tin cậy mô hình thể hiện và kết quả thực tế'],['mAP','Điểm tổng hợp về độ chính xác khi thay đổi ngưỡng nhận diện'],['Khoảng tin cậy / ảnh ngoài phạm vi','Khoảng ước lượng độ bất định / ảnh khác đáng kể với nhóm dùng để xây dựng mô hình'],['Lần khởi tạo / bản trọng số đã lưu','Giá trị khởi tạo ngẫu nhiên / tệp mô hình được lưu để nạp lại']],[3,14.5])
h('QUYẾT ĐỊNH TRIỂN KHAI')
p('Đến ngày 01/11/2026, nhóm đã hoàn thành quy trình thực nghiệm phân loại tư thế phân cấp theo hai hướng: học trực tiếp từ ảnh và học từ điểm mốc do mô hình pose dự đoán. Phương án được chọn trên validation là tổ hợp ba mô hình ResNet-18; trọng số nhánh ảnh trong cấu hình triển khai bằng 1,0. Nhánh keypoint tiếp tục được giữ làm đối chứng và công cụ phân tích hình học, chưa đóng góp vào xác suất phân loại của cấu hình đang chọn. [2], [3]')
p('Phạm vi sử dụng hiện tại là demo và báo cáo nội bộ. Mô hình chưa đạt độ phủ đồng đều ở 11 lớp L2, và tập test đã được xem trong các vòng phát triển. Vì vậy, kết quả được xem là mốc thực nghiệm hiện hành; việc đánh giá khả năng tổng quát hóa cần một tập kiểm thử mới được khóa trước khi điều chỉnh mô hình. [2], [7]')
h('TÓM TẮT')
p('Báo cáo lần 5 tổng hợp tiến độ tuần 8–9–10, chốt số liệu đến ngày 01/11/2026. Theo báo cáo giữa kỳ, đến 20/10 nhóm đã cố định 873 ảnh được duyệt và phương án chia 612/136/125, nhưng chưa thực hiện huấn luyện chính thức. Trong kỳ này, sáu mô hình phân loại ảnh đã hoàn tất huấn luyện với hai kiến trúc và ba lần khởi tạo; nhóm cũng đánh giá mô hình ước lượng điểm mốc và bộ phân loại dựa trên các điểm này. Nhánh ảnh đạt độ chính xác L1 là 90,40% và Macro-F1 là 0,8546; nhánh điểm mốc lần lượt đạt 85,60% và 0,8091. Ở mức L2, hệ thống trả nhãn cho 37/103 ảnh có tham chiếu và 33 nhãn khớp; độ đúng trong số ảnh đã được trả lời là 89,19%. Trên 82 ảnh đủ 17 điểm mốc, PCK@0.05 là 0,7862 và OKS là 0,8853. Các giới hạn chính gồm số mẫu ít ở một số lớp, độ phủ nhãn chi tiết còn thấp và việc cần có một đợt đánh giá độc lập mới. [1]–[4]')
h('1. TÓM TẮT TIẾN ĐỘ VÀ PHẠM VI')
sub('1.1. Mục tiêu và kết quả chính')
p('Mục tiêu của giai đoạn này là chuyển từ dữ liệu đã gán nhãn và mô hình gợi ý hình học sang hệ thống dự đoán một nhãn tư thế cụ thể nhất có đủ bằng chứng. Đầu ra có ba mức: nhãn chi tiết L2, nhãn tổng quát L1 khi chưa đủ căn cứ cho L2, hoặc “Không xác định” khi xác suất L1 không đạt ngưỡng. Việc nhận diện danh tính nhân vật, diễn giải tôn giáo và tái dựng hình thể 3D nằm ngoài phạm vi thực nghiệm. [3], [6]')
table('Tiến độ đạt được đến thời điểm chốt',['Hạng mục','Kết quả có bằng chứng','Giới hạn còn lại'],[
 ['Dữ liệu','873 ảnh; split 612/136/125; 729 nhãn L2','144 ảnh L2 trống; mất cân bằng lớp'],['Huấn luyện ảnh','ResNet-18 và MobileNetV2, mỗi kiến trúc 3 seed','Chưa có nested cross-validation'],['Nhánh keypoint','Đặc trưng hình học 100 chiều; chọn logistic C=0,1','Chất lượng chân còn thấp ở các lớp khó'],['Đồng thuận','873 cặp nhãn; κ mã tư thế = 0,9652','Chỉ phản ánh hai phiếu nhãn đã lưu'],['Demo','Nạp lại checkpoint và ngưỡng đã lưu, kiểm tra manifest','Chưa đo độ trễ và chưa đánh giá OOD'],['Đánh giá','Có dự đoán từng ảnh, kết quả từng lớp và bootstrap','Test lịch sử đã tham gia vòng phản hồi phát triển']],[3,7.2,7.3])
sub('1.2. Phạm vi số liệu và nguyên tắc diễn giải')
p('Số liệu chính được lấy từ hồ sơ huấn luyện và đánh giá hoàn tất lúc 00:53 ngày 01/11/2026 theo giờ Việt Nam. Một hồ sơ hoàn tất khác lúc 00:55 cùng ngày cho các nhóm kết quả phân loại ảnh, điểm mốc, cấu hình triển khai và ước lượng độ bất định trùng với hồ sơ chính. Hai hồ sơ này không được tính thành hai thí nghiệm độc lập. Mô hình minh họa được nạp lại từ trọng số đã lưu; quá trình huấn luyện không được chạy lại để tạo các ca minh họa. [2], [8]')
p('Ba giá trị 20261021, 20261031 và 20261107 là các cách khởi tạo khác nhau để xem độ ổn định của kết quả, không phải ngày huấn luyện. Toàn bộ mô hình trong kỳ đã hoàn tất trước thời điểm chốt báo cáo. Các lượt kiểm tra kỹ thuật chỉ xác nhận quy trình vận hành, không được dùng làm số liệu chất lượng mô hình. [2], [6]')
h('2. TIẾN TRÌNH DỮ LIỆU VÀ CÁC MỐC HUẤN LUYỆN')
sub('2.1. Công việc trong tuần 8–9–10')
p('Tiến độ được tổng hợp theo ba nhóm công việc của kỳ báo cáo. Các mốc ngày dưới đây dựa trên gói dữ liệu, hồ sơ sửa nhãn và nhật ký chạy; chúng không thay thế nhật ký chấm công hay xác nhận lịch học của từng thành viên.')
table('Các mốc có hồ sơ đối chiếu trong kỳ',['Mốc','Công việc','Sản phẩm kiểm chứng'],[
 ['Tuần 8\nMốc 20/10','Chuẩn hóa dữ liệu, hệ thống nhãn và phương án chia theo nhóm tác phẩm','Bản mô tả dữ liệu, bảng kê khai và hồ sơ phân chia'],['Tuần 9\n26–29/10','Xây dựng hai hướng phân loại từ ảnh và điểm mốc; rà 35 trường hợp minh họa chưa ổn','Nhật ký huấn luyện và biên bản rà soát 35 trường hợp'],['Tuần 10\n30/10','Thống nhất một số trường hợp cưỡi ngựa và cưỡi nai/hươu; cập nhật nhãn','Biên bản thống nhất nhãn ngày 30/10'],['Tuần 10\n31/10–01/11','Điều chỉnh cách xử lý ảnh, việc phân loại theo hai cấp và đánh giá bằng chứng; huấn luyện sáu mô hình; lưu bản để trình diễn','Hồ sơ cải tiến, kết quả tổng hợp, quyết định lựa chọn và trọng số đã lưu']],[3.2,8,6.3])
sub('2.2. Đối chiếu tiến độ với báo cáo giữa kỳ')
p('Báo cáo giữa kỳ chốt ngày 20/10/2026 cho biết bộ hồ sơ có 1.165 bản ghi, trong đó 873 ảnh được duyệt; 729 ảnh có nhãn L2 và 144 ảnh dừng ở L1. Phương án chia theo nhóm hiện vật đã được cố định ở mức 612 ảnh huấn luyện, 136 ảnh xác thực và 125 ảnh kiểm thử. Tuy nhiên, tại thời điểm đó nhóm chưa hoàn tất huấn luyện chính thức, đánh giá phân loại, so sánh mô hình và trình diễn toàn quy trình. Đây là mốc xuất phát phù hợp để xem xét tiến độ kỳ này.')
p('Ba chỉ số precision 0,9495, recall 0,9400 và PCK@0.05 bằng 0,7265 trong báo cáo giữa kỳ thuộc một mốc thử nghiệm kỹ thuật trước đó trên 100 ảnh. Báo cáo giữa kỳ nêu rõ tập này chỉ dùng để xác minh quy trình, không phải tập kiểm thử chính thức của phương án chia mới. Kết quả hiện tại được tính trên hồ sơ thực nghiệm và mẫu số riêng; PCK 0,7862 không được diễn giải là mức tăng trực tiếp so với 0,7265 vì giao thức, tập ảnh và cách tính khác nhau.')
table('Tiến độ từ mốc giữa kỳ đến ngày 01/11/2026',['Hạng mục','Tại báo cáo giữa kỳ (20/10)','Tại báo cáo lần 5'],[
 ['Dữ liệu và phân chia','873 ảnh được duyệt; split 612/136/125 đã cố định','Tiếp tục dùng split 612/136/125 cho huấn luyện và đánh giá'],['Huấn luyện phân loại','Chưa thực hiện chính thức','Hoàn tất 6 mô hình ảnh với 2 kiến trúc × 3 seed; có thêm nhánh keypoint'],['Đánh giá phân loại','Chưa có kết quả chính thức','Nhánh ảnh: L1 accuracy 0,9040, Macro-F1 0,8546; nhánh keypoint: 0,8560 và 0,8091'],['Ước lượng điểm mốc','Mốc pilot 100 ảnh: PCK@0.05 = 0,7265','82 ảnh đủ điểm mốc: PCK@0.05 = 0,7862; OKS = 0,8853, theo schema hiện hành'],['Demo mô hình','Chưa xây dựng bản trình diễn đầu-cuối','Đã nạp lại mô hình đã lưu và đối chiếu 12 ca minh họa; chưa phải kiểm thử vận hành đầy đủ'],['Phạm vi kết luận','Chưa kết luận hiệu năng cuối cùng','Có kết quả thực nghiệm nội bộ; cần đánh giá độc lập mới trước khi khẳng định khả năng tổng quát hóa']],[3.2,6.7,6.3])
p('Số lượng ảnh và cách chia ở báo cáo giữa kỳ khớp với cấu hình đang dùng; tiến độ tăng chủ yếu nằm ở việc hoàn thành huấn luyện, đánh giá và nạp lại mô hình. Các ca demo được chọn có chủ đích để minh họa tình huống phù hợp và tình huống cần xem xét, không đại diện cho tỷ lệ đúng chung. Hồ sơ hiện có cũng chưa đủ để so sánh trực tiếp từng ảnh của pilot 100 mẫu với các mẫu trong đánh giá hiện tại; vì vậy các chỉ số giữa hai mốc được trình bày như hai phép đo riêng.')
h('3. PHÂN CHIA DỮ LIỆU VÀ PHÂN BỐ LỚP')
sub('3.1. Phân chia cố định và tập đủ điều kiện')
p('Phương án phân chia phiên bản 2 giữ các ảnh của cùng hiện vật hoặc nhóm ảnh gần trùng trong cùng một phần dữ liệu; các lớp tư thế được phân tầng để hạn chế chênh lệch lớn giữa các phần. Tỷ lệ mục tiêu là 70/15/15, còn số lượng thực tế là 612/136/125 do phải giữ nguyên nhóm tác phẩm. Giá trị khởi tạo mô hình khác với giá trị dùng để lập phương án chia. Hồ sơ kiểm tra không ghi nhận nhóm hiện vật hoặc ảnh trùng mã ở nhiều phần dữ liệu. [2], [4]')
table('Số mẫu theo nhiệm vụ và phân chia',['Tập con','Train','Validation','Test','Tổng'],[
 ['Toàn bộ ảnh L1',612,136,125,873],['Có L2',520,106,103,729],['L2 trống',92,30,22,144],['Đủ 17 keypoint',442,88,82,612],['Có ít nhất một keypoint',578,128,117,823],['Không có keypoint',34,8,8,50]],[6.3,2.8,2.8,2.8,2.8])
p('Tập “có ít nhất một keypoint” bao gồm cả ảnh đủ 17 keypoint; hai dòng này không được cộng với nhau. Có 211 ảnh có keypoint nhưng chưa đầy đủ và 50 ảnh không có điểm mốc. Nhánh ảnh sử dụng toàn bộ 612 ảnh train để học L1; loss L2 chỉ tính trên 520 ảnh train có nhãn L2. Mô hình pose đầy đủ được xây dựng từ 442 ảnh train đủ điểm mốc. [2]–[4]')
sub('3.2. Phân bố nhãn tổng quát và chi tiết')
table('Phân bố bốn lớp L1',['Lớp','Tên tư thế','Train','Val','Test','Tổng'],[[c['code'],c['vi']]+[sum(r['level_1_code']==c['code'] and r['split']==sp for r in rows) for sp in ['train','val','test']]+[sum(r['level_1_code']==c['code'] for r in rows)] for c in ont['level_1']],[2,6.3,2.3,2.3,2.3,2.3])
table('Phân bố 11 lớp L2',['Lớp','Tên tư thế','Train','Val','Test'],[[c['code'],c['vi']]+[sum(r['level_2_code']==c['code'] and r['split']==sp for r in rows) for sp in ['train','val','test']] for c in ont['level_2']],[2,8,2.5,2.5,2.5])
p('C1.1 có 544/873 ảnh, tương đương 62,31%; riêng C2.1 có 273/729 ảnh mang L2. Một số lớp chỉ có 3–4 ảnh trong validation hoặc test. Do đó, accuracy tổng thể dễ chịu ảnh hưởng của lớp ngồi phổ biến; macro-F1, kết quả từng lớp và support được báo đồng thời. Trọng số nghịch căn tần suất chỉ tính từ train để không đưa phân bố test vào quá trình học.')
image(QA/'figures/01_data_distribution.png','Phân bố nhãn L1, L2 và quy mô các tập dữ liệu',
      'Biểu đồ cho thấy C1.1 chiếm tỷ trọng lớn nhất, trong khi nhiều nhãn L2 có rất ít mẫu. Train, validation và test lần lượt có 612, 136 và 125 ảnh. Vì vậy cần đọc điểm theo từng lớp cùng support; tổng số ảnh và kiểm toán trùng lặp không thay thế việc xem xét độ mất cân bằng.')
h('4. GÁN NHÃN VÀ KIỂM TRA CHÉO')
sub('4.1. Quy tắc nhãn và đính chính ngày 30/10')
p('Hệ thống nhãn hiện hành gồm bốn nhóm tư thế tổng quát L1 và 11 nhãn chi tiết L2. C1.5 chỉ dùng để từ chối khi ảnh chưa đủ căn cứ, không phải lớp huấn luyện thứ năm. Khi hình ảnh không cho thấy rõ biến thể, nhãn dừng ở L1 thay vì suy đoán L2. Bộ điểm mốc theo quy ước COCO-17 đánh dấu mỗi khớp là chưa xác định, bị che nhưng còn ước lượng được, hoặc nhìn thấy; trái/phải tính theo cơ thể nhân vật. [4]')
p('Biên bản ngày 30/10 thống nhất một số ảnh được gán tư thế ngồi hoặc cưỡi ngựa. Các ảnh THK000025, THK000010, THK000016, THK000078 và THK000787 được đổi sang nhóm chuyển động theo quyết định đã ghi. Quy tắc này không tự động áp dụng cho ảnh cưỡi la, sư tử, hổ hoặc rồng chưa được xem xét. Các bản xuất ngày 20/10 được giữ làm lịch sử; phần đánh giá hiện tại dùng hồ sơ nhãn đã cập nhật. [5]')
sub('4.2. Đồng thuận giữa hai người gán nhãn')
p('Hai phiếu gán nhãn được ghép theo mã ảnh, sau đó kiểm tra trường hợp trùng mã, thiếu nhãn hoặc dùng mã ngoài hệ thống nhãn. Trên 873 cặp, tỷ lệ trùng hoàn toàn ở nhãn tư thế chi tiết là 97,02%, tương ứng 847 cặp; 26 cặp có khác biệt. Kappa trên mã nhãn cụ thể là 0,9652. Khi quy nhãn chi tiết về nhóm tư thế tổng quát, tỷ lệ đồng thuận và kappa đều bằng 1,0000. [2], [3]')
p('Kappa ở đây là phép đo không trọng số trên nhãn cụ thể; nó không tính khoảng cách giữa các nhãn trong cấu trúc phân cấp. Kết quả phản ánh mức thống nhất giữa hai phiếu được lưu, không đo sai số vị trí điểm mốc và cũng không chứng minh nhãn đúng tuyệt đối. Hồ sơ cần bảo toàn phiếu gốc, thời điểm gán và bước phân xử để xác nhận hai lượt gán nhãn thực sự độc lập.')
image(QA/'figures/02_interrater_matrix.png','Ma trận đối chiếu nhãn của hai người gán nhãn',
      'Các ô tập trung trên đường chéo, phù hợp với tỷ lệ trùng nhãn cụ thể 847/873 (97,02%) và Cohen’s κ = 0,9652. Sau khi quy L2 về lớp cha L1, hai phiếu thống nhất hoàn toàn. Kappa đo độ nhất quán giữa hai phiếu đã lưu, không tự xác nhận tính đúng tuyệt đối của nhãn.')
h('5. QUY TRÌNH CỦA CÔNG CỤ')
p('Quy trình thực nghiệm gồm các bước có thể đối chiếu: kiểm tra dữ liệu và nhãn; cố định phương án chia; huấn luyện mô hình từ ảnh và mô hình ước lượng tư thế; chọn cấu hình trên tập xác thực; hiệu chỉnh xác suất và ngưỡng; đánh giá trên tập kiểm thử; lưu kết quả và nạp lại mô hình để minh họa. Người duyệt vẫn quyết định nhãn tham chiếu; đầu ra mô hình không tự thay thế nhãn đã được duyệt. [3], [8]')
table('Vai trò của các thành phần vận hành',['Thành phần','Đầu vào và đầu ra','Kiểm soát chính'],[
 ['Kiểm tra dữ liệu','Bảng kê khai, hệ thống nhãn và phương án chia → thống kê và rà trùng','Giữ nguyên cách chia giữa các kiến trúc'],['Nhánh ảnh','Ảnh cắt nhân vật → xác suất L1, L2 và mức đủ căn cứ','Giữ tỷ lệ ảnh; kích thước đầu vào 384 × 384'],['Nhánh điểm mốc','Vị trí khớp ước lượng → đặc trưng hình học → xác suất tư thế','Dùng cùng quy tắc hình học khi huấn luyện và minh họa'],['Chọn cấu hình','Tập xác thực → kiến trúc, mức hiệu chỉnh xác suất và ngưỡng','Không dùng tập kiểm thử trực tiếp để điều chỉnh ngưỡng'],['Mô hình đã lưu','Trọng số mô hình, dữ liệu và quyết định đã chốt → nhãn và xác suất','Kiểm tra đúng phiên bản; không huấn luyện lại khi minh họa']],[3.7,7.1,6.7])
p('Các chỉ số phân loại trong báo cáo được tính từ ảnh nhân vật đã cắt sẵn. Vì vậy, chúng không đo khả năng tự tìm nhân vật chính trong một bức tranh toàn cảnh. Nếu sử dụng ảnh có nhiều hình tượng, cần đánh giá riêng bước chọn và định vị nhân vật trước khi kết luận về chất lượng nhãn cuối.')
image(QA/'figures/10_demo_pipeline.png','Các bước xử lý và thông tin được trình bày trong bản minh họa',
      'Sơ đồ cho thấy ảnh được chuyển thành nhãn tư thế, đồng thời hiển thị điểm mốc để người xem đối chiếu. Cấu hình hiện hành lấy kết quả phân loại từ nhánh ảnh; điểm mốc chỉ hỗ trợ phần quan sát, không làm thay đổi nhãn cuối. Đây là minh họa quy trình, không phải một lần dự đoán mới.')
h('6. NGUỒN GỐC VÀ VAI TRÒ CÁC MÔ HÌNH')
sub('6.1. Nhánh phân loại trực tiếp từ ảnh')
p('Hai lựa chọn phân loại ảnh là ResNet-18 và MobileNetV2, đều được khởi tạo từ trọng số đã học trước trên dữ liệu ảnh quy mô lớn. Mỗi mô hình dự đoán tư thế tổng quát, tư thế chi tiết và mức độ đủ căn cứ để đưa ra nhãn chi tiết. Hai kiến trúc được so sánh trên cùng bộ dữ liệu và cùng cách đánh giá. [3], [10], [11]')
p('Mỗi kiến trúc được huấn luyện với ba cách khởi tạo. Nhóm so sánh kết quả của từng cách khởi tạo, sau đó đánh giá tổ hợp nhiều mô hình trên tập xác thực. Cách làm này giảm lệ thuộc vào một lần chạy thuận lợi; tuy nhiên, ba lần khởi tạo trên cùng một phương án chia dữ liệu chưa thay thế việc kiểm tra trên nhiều cách chia khác nhau.')
sub('6.2. Nhánh pose và bộ phân loại hình học')
p('Khâu ước lượng điểm mốc sử dụng mô hình YOLO11n-pose đã có, với cấu hình trước đó gồm 50 vòng huấn luyện, ảnh đầu vào 416 và hai ảnh mỗi lượt cập nhật. Hồ sơ hiện tại nạp lại mô hình này; nhóm không huấn luyện lại bộ ước lượng điểm mốc trong đợt nâng cấp cuối tháng 10. Vì vậy, thay đổi ở kết quả phân loại không được quy cho một lần huấn luyện mới của mô hình này. [3], [6]')
p('Bộ phân loại hình học dùng tọa độ và mức quan sát của 17 khớp, cùng các khoảng cách, tỷ lệ và góc giữa những khớp chính; tổng cộng 100 đặc trưng. Nhóm so sánh hồi quy logistic, rừng ngẫu nhiên và Extra Trees. Phương án hồi quy logistic với C=0,1 đạt kết quả xác thực tốt nhất trong số các phương án đã thử. [3]')
h('7. HUẤN LUYỆN, PHÂN CHIA DỮ LIỆU VÀ CHỈ SỐ')
sub('7.1. Cấu hình thực nghiệm có thể tái lập')
table('Cấu hình huấn luyện nhánh ảnh',['Nội dung','Giá trị thực hiện'],[
 ['Phần cứng và môi trường','GPU RTX 3050 Laptop; phiên bản môi trường phần mềm được lưu trong hồ sơ thực nghiệm'],['Kích thước ảnh','384 × 384; giữ tỷ lệ toàn thân và xoay ảnh trước khi chuẩn hóa kích thước'],['Số mô hình','2 kiến trúc × 3 lần khởi tạo = 6 mô hình'],['Số ảnh mỗi lượt cập nhật','4 ảnh mỗi nhóm; tích lũy 4 nhóm trước khi cập nhật đầy đủ'],['Trình tự tinh chỉnh','5 vòng đầu học lớp dự đoán; mở rộng dần các phần còn lại của mô hình'],['Dừng huấn luyện','Tối đa 100 vòng; cho phép dừng sớm khi kết quả xác thực không còn cải thiện'],['Tốc độ học','0,00002 cho phần trích đặc trưng; 0,0002 cho lớp dự đoán'],['Điều chỉnh độ phức tạp','Hệ số 0,0005 để hạn chế mô hình khớp quá mức với mẫu huấn luyện'],['Ổn định quá trình học','Tính toán độ chính xác hỗn hợp, giới hạn độ lớn cập nhật và giữ thống kê chuẩn hóa'],['Chênh lệch số lượng lớp','Tăng trọng số cho lớp ít ảnh; không tạo bản sao riêng cho C2.2']],[5.1,12.4])
p('Hàm mục tiêu kết hợp việc nhận diện tư thế tổng quát, tư thế chi tiết và quyết định xem bằng chứng có đủ hay không. Ảnh thiếu nhãn L2 vẫn được dùng để học L1 và mức đủ căn cứ, nhưng không bị ép thành một nhãn chi tiết. Một phần trọng số cũng khuyến khích hai cấp nhãn nhất quán, để sai lệch ở nhãn chi tiết ảnh hưởng đến đánh giá nhãn tổng quát. [3], [6]')
p('Điểm chọn bản trọng số dùng cho đánh giá được tổng hợp theo bốn thành phần: 35% cho F1 trung bình ở L1, 40% cho F1 L2 trong toàn quy trình, 15% cho F1 L2 khi đã biết trước nhãn L1 chuẩn và 10% cho mức phù hợp của bằng chứng. Điểm này được tính trên tập xác thực và khác với điểm so sánh cấu hình triển khai sau khi chọn ngưỡng; vì vậy không nên đặt hai giá trị cạnh nhau như cùng một chỉ số. [3]')
sub('7.2. Lịch huấn luyện thực tế')
table('Số epoch và checkpoint tốt nhất của sáu mô hình',['Kiến trúc','Seed','Epoch tốt nhất','Epoch đã chạy','Điểm chọn checkpoint'],[[v['architecture'],v['seed'],v['best_epoch'],v['epochs_completed'],fmt(v['best_validation_selection_score'])] for v in [js(fp) for fp in sorted((RUN/'image_classifier').glob('*/training_summary.json'))]],[3.9,3,3.1,3,4.5])
image(QA/'curves.png','Diễn biến điểm chọn mô hình tốt nhất; mỗi đường là một kiến trúc và cách khởi tạo, nguồn: nhật ký huấn luyện [2]',
       'Các đường thể hiện điểm tổng hợp trên validation qua từng epoch của sáu lượt huấn luyện. Đỉnh được dùng để lưu trạng thái tốt nhất; độ dao động giữa các đường cho thấy kết quả còn phụ thuộc vào kiến trúc và lần khởi tạo. Hình này mô tả quá trình chọn mô hình, không phải kết quả trên test.')
p('Không mô hình nào phải chạy đủ 100 epoch. Checkpoint tốt nhất có thể xuất hiện trước mốc min_epochs, như MobileNetV2 seed 20261107 ở epoch 13; min_epochs ràng buộc thời điểm được phép dừng, không cấm giữ một checkpoint tốt ở giai đoạn sớm. Các run lưu best_model.pt để suy luận và last_training_state.pt để tiếp tục huấn luyện với optimizer, scheduler và trạng thái ngẫu nhiên. [2], [6]')
sub('7.3. Hiệu chỉnh xác suất và lựa chọn ngưỡng')
p('Temperature scaling được áp dụng trên validation cho đầu ra L1, L2 và bằng chứng. Đây là bước hiệu chỉnh xác suất sau huấn luyện; nó không chứng minh rằng mọi giá trị phần trăm trên demo đều tương đương xác suất đúng trong bối cảnh ngoài dữ liệu nghiên cứu. ECE và Brier được dùng để mô tả chất lượng xác suất của run hiện hành. [3], [12]')
p('Ngưỡng L1 của nhánh ảnh là 0,4267, được chọn để đạt coverage validation lớn nhất với accuracy trên mẫu được nhận ít nhất 90%. Mỗi lớp L2 có ngưỡng riêng: tối thiểu ba dự đoán validation được chấp nhận, precision thực nghiệm ít nhất 90% và không nhận L2 trên ảnh có L2 tham chiếu trống. Ngưỡng bằng chứng chung được chọn theo macro recall. Giá trị 1,0001 có nghĩa lớp bị khóa ở cấp L2 và chỉ có thể trả về L1 hoặc từ chối. [2], [3]')
image(QA/'figures/06_calibration_summary.png','So sánh ECE và Brier L1 trên test',
      'Nhánh ảnh có ECE 0,0350 và Brier 0,1548; nhánh keypoint lần lượt là 0,0502 và 0,2227. Các giá trị được tính từ kết quả test đã lưu. Temperature scaling và lựa chọn ngưỡng được thực hiện trên validation; test không được dùng để chọn các tham số này.')
sub('7.4. Định nghĩa chỉ số và mẫu số')
table('Quy ước đọc các chỉ số trong báo cáo',['Chỉ số','Định nghĩa áp dụng'],[
 ['Accuracy L1 thô','Argmax L1 đúng trên toàn bộ 125 ảnh, trước cơ chế từ chối'],['Selective accuracy L1','Số L1 đúng chia số ảnh được chấp nhận trả lời L1/L2'],['Coverage L2','Số ảnh có gold L2 được trả L2 chia 103 ảnh có gold L2'],['Selective accuracy L2','Số dự đoán L2 đúng trên số được trả L2 trong tập 103 ảnh'],['L2 exact trên toàn tập có L2','Số L2 đúng chia 103; fallback và từ chối đều chưa hoàn thành L2'],['L2 oracle','Đánh giá nhánh L2 khi biết trước L1 đúng; không phải kết quả triển khai'],['PCK@0.05','Tỷ lệ điểm có sai số pixel ≤ 5% đường chéo bbox; tính với v>0'],['OKS','Dùng hệ số COCO (2σ)², tọa độ pixel và diện tích bbox đại diện đối tượng']],[5.2,12.3])
p('PCK và OKS tự tính đã chuyển sang metric schema 2. Công thức cũ dùng không gian chuẩn hóa riêng theo chiều rộng và chiều cao, có thể làm lệch khoảng cách trên ảnh ngang. Việc thay công thức đo, trong khi giữ nguyên checkpoint, có thể làm thay đổi số báo cáo mà không phản ánh thay đổi năng lực mô hình. [3], [6]')
h('8. KẾT QUẢ ĐỊNH LƯỢNG')
sub('8.1. Lựa chọn kiến trúc và kết hợp hai nhánh')
table('So sánh các tổ hợp trên validation',['Tổ hợp','Macro-F1 L1','Macro-F1 L2 end-to-end','Điểm chọn triển khai'],[[name,fmt(v['l1_macro_f1']),fmt(v['l2_end_to_end_macro_f1']),fmt(v['score'])] for name,v in S['image_selection']['group_comparison'].items()],[5,4,4.5,4])
p('Tổ hợp ba ResNet-18 đạt điểm lựa chọn 0,6158, cao hơn MobileNetV2 và tổ hợp cả sáu mô hình trong giao thức này. Bước triển khai tiếp tục so sánh nhánh ảnh, nhánh keypoint và các tỷ lệ trộn trung gian trên validation; cấu hình được chọn có image_weight=1,0. Vì vậy, không có cơ sở mô tả đầu ra hiện hành là mô hình kết hợp ảnh–keypoint mang lại cải thiện. [2], [3]')
sub('8.2. Kết quả phân loại trên 125 ảnh test')
metrics=[('l1_accuracy','Độ chính xác L1 trước ngưỡng'),('l1_macro_f1','F1 trung bình L1'),('l1_selective_coverage','Tỷ lệ có kết quả L1'),('l1_selective_accuracy','Độ chính xác L1 trong số ảnh có câu trả lời'),('unknown_rate','Tỷ lệ không xác định'),('l1_ece','ECE L1'),('l1_brier','Brier L1'),('l2_oracle_macro_f1','F1 L2 khi đã biết nhãn L1'),('l2_coverage','Tỷ lệ có kết quả L2 trên 103 ảnh'),('l2_selective_accuracy','Độ chính xác L2 trong số ảnh có câu trả lời'),('l2_exact_over_all','L2 đúng trên 103 ảnh'),('l2_blank_abstention','Không trả L2 trên 22 ảnh không có nhãn L2')]
table('Đối sánh hai hướng trên cùng phân chia dữ liệu',['Chỉ số','Nhánh ảnh','Nhánh điểm mốc'],[[label,fmt(S['image_test'][key]),fmt(S['keypoint_test'][key])] for key,label in metrics],[9.5,4,4])
p('Nhánh ảnh đúng L1 thô 113/125 ảnh. Sau ngưỡng từ chối, 123 ảnh được nhận và 112 ảnh đúng L1, tương ứng 91,06%; hai ảnh bị từ chối. Nhánh keypoint đúng L1 thô 107/125; sau ngưỡng, nhận 108 ảnh và đúng 98 ảnh, tương ứng 90,74%. Việc giảm coverage giúp selective accuracy cao hơn nhưng không làm biến mất các trường hợp hệ thống không trả lời. [2]')
p('Trên 103 ảnh có L2 tham chiếu, nhánh ảnh nhận 37 và đúng 33; nhánh keypoint nhận 10 và đúng cả 10. Accuracy 100% của keypoint phải được đọc cùng coverage 9,71%, không thể xem là vượt nhánh ảnh về khả năng nhận dạng chi tiết trên toàn bộ dữ liệu. Ngoài ra, nhánh ảnh còn trả L2 cho hai ảnh thuộc nhóm 22 ảnh L2 trống. [2]')
p('Tổng đầu ra triển khai là 39 nhãn L2, 84 nhãn L1 và 2 trường hợp Không xác định. Trong 39 nhãn L2, có 33 nhãn đúng theo tham chiếu; bốn nhãn sai thuộc nhóm đã có L2 và hai nhãn được đưa ra trên ảnh L2 trống. Nếu tính độ đúng nghiêm ngặt trên toàn bộ 39 đầu ra L2, tỷ lệ là 84,62%, thấp hơn 89,19% được tính riêng trên nhóm có gold L2. Sự khác biệt mẫu số này cần được giữ khi trình bày demo.')
image(QA/'figures/03_confusion_matrices.png','Ma trận nhầm lẫn L1 toàn quy trình và L2 khi đã biết nhãn L1 của hai hướng',
      'Các ô trên đường chéo thể hiện dự đoán đúng; các ô ngoài đường chéo cho biết những tư thế bị nhầm lẫn. Ma trận L1 phản ánh kết quả phân loại tổng quát. Ma trận L2 giả định nhãn L1 chuẩn đã biết trước, nên chỉ dùng để xem riêng khả năng phân biệt tư thế chi tiết, không đại diện cho kết quả hệ thống trả ra từ ảnh đầu vào.')
image(QA/'figures/04_risk_confidence_test.png','Độ chính xác theo coverage và phân bố độ tin cậy L1',
      'Đường cong được dựng từ độ tin cậy và nhãn dự đoán đã lưu cho 125 ảnh test để mô tả quan hệ giữa tỷ lệ được nhận và độ chính xác có điều kiện. Đây là hình hậu kiểm mô tả, không dùng để chọn ngưỡng; ngưỡng vận hành đã được chọn trên validation. Các cột đỏ tập trung ở độ tin cậy thấp hơn sẽ là vùng cần tiếp tục rà soát.')
image(QA/'figures/08_test_comparison.png','So sánh kết quả L1 và L2 khi đã biết nhãn L1 trên cùng tập kiểm thử',
      'Nhánh ảnh đạt độ chính xác L1 0,9040 và F1 trung bình theo lớp 0,8546, cao hơn nhánh dựa trên điểm mốc tương ứng 0,8560 và 0,8091. F1 L2 trong điều kiện đã biết nhãn L1 gần nhau (0,6749 và 0,6690); các giá trị này không biểu thị tỷ lệ ảnh thực tế được trả nhãn chi tiết. Cần đọc cùng số ảnh và tỷ lệ hệ thống đưa ra kết quả ở các bảng liên quan.')
image_decisions=collections.Counter(r['decision_level'] for r in pred); keypoint_decisions=collections.Counter(r['decision_level'] for r in kp)
image_comment=(f"Nhánh ảnh trả {image_decisions['l2']} nhãn L2, {image_decisions['l1']} fallback L1 và {image_decisions['unknown']} trường hợp không xác định trên {len(pred)} ảnh. "
               f"Nhánh keypoint trả {keypoint_decisions['l2']} nhãn L2, {keypoint_decisions['l1']} fallback L1 và {keypoint_decisions['unknown']} trường hợp không xác định trên {len(kp)} ảnh. "
               'Tỷ lệ L2 thấp thể hiện chính sách chỉ trả nhãn chi tiết khi đạt điều kiện; không nên diễn giải coverage thấp như thiếu dữ liệu trong hình.')
image(QA/'figures/09_decision_distribution.png','Tỷ lệ các mức quyết định cuối trên test',image_comment)
sub('8.3. Kết quả hình học pose và mức bất định')
table('Kết quả ước lượng tư thế trên tập kiểm thử đủ điểm mốc',['Chỉ số','Giá trị','Phạm vi'],[
 ['Số ảnh đánh giá',82,'Ảnh kiểm thử đủ 17 điểm mốc'],['Điểm mốc tham chiếu',1394,'17 × 82; chỉ tính điểm có vị trí'],['Tỷ lệ phát hiện','1,0000','Theo quy trình xử lý ảnh cắt hiện hành'],['IoU khung bao trung bình','0,8539','Đo mức chồng lấp giữa khung dự đoán và khung tham chiếu'],['PCK@0.05','0,7862','Sai số vị trí so với đường chéo khung bao'],['OKS trung bình','0,8853','Theo quy ước đánh giá hiện hành; có điều chỉnh theo kích thước nhân vật'],['mAP tư thế 50–95','0,7898','Chỉ số tổng hợp từ bước ước lượng tư thế'],['mAP tư thế 50 / 75','0,9842 / 0,8567','Cùng tập 82 ảnh'],['mAP khung bao 50–95','0,9579','Cùng tập 82 ảnh']],[6.5,4,7])
image(QA/'figures/05_pose_metrics.png','Các chỉ số hình học của pose estimator trên tập test',
      'Trên 82 ảnh test đủ 17 điểm mốc, tỷ lệ phát hiện là 100%, IoU khung bao trung bình 0,8539, PCK@0.05 là 0,7862 và OKS là 0,8853. Phạm vi này là đánh giá trên ảnh cắt theo quy ước đo hiện hành; không đại diện cho việc tìm nhân vật từ toàn bộ tranh và không so trực tiếp với mốc pilot 100 ảnh (PCK 0,7265) nêu trong báo cáo giữa kỳ, do khác tập ảnh và giao thức đo.')
p('Chênh lệch độ chính xác L1 thô giữa nhánh ảnh và nhánh điểm mốc là 0,0480, tương ứng sáu ảnh trên tổng số 125. Khi lấy mẫu lặp theo từng ảnh để ước lượng độ bất định, khoảng 95% của chênh lệch nằm trong khoảng −0,0080 đến 0,1120 và có chứa 0. Vì vậy, số liệu hiện tại chưa đủ để khẳng định ưu thế ổn định của nhánh ảnh. Phép ước lượng chưa lấy mẫu theo nhóm tác phẩm, nên vẫn cần thận trọng khi suy rộng kết luận. [2], [3]')
image(QA/'figures/11_pose_overlay_example.png','Đối chiếu điểm mốc tham chiếu và kết quả ước lượng tư thế đã lưu',
      'Hai phần của hình cho thấy điểm mốc đã gán và điểm mốc do YOLO11n-pose ước lượng trên cùng ảnh. Đây là ví dụ minh họa, không phải mẫu chọn ngẫu nhiên; các chỉ số được tính trên toàn bộ 82 ảnh kiểm thử đủ điểm mốc. Sai khác vị trí cần được xem cùng kết quả tổng hợp, nhất là ở tranh có nhiều nhân vật hoặc hình thể cách điệu.')
h('9. ĐÁNH GIÁ TRỰC QUAN VÀ PHÂN TÍCH LỖI')
sub('9.1. Kết quả L2 theo từng lớp')
pc=cr(RUN/'deployment/per_class_end_to_end.csv')
table('Hiệu năng L2 end-to-end của cấu hình triển khai',['Lớp','Support','Dự đoán','Đúng','Precision','Recall','F1'],[[v['code'],v['support'],v['predicted'],v['correct'],fmt(v['precision']),fmt(v['recall']),fmt(v['f1'])] for v in pc],[2.1,2.3,2.3,2,3,2.9,2.9])
p('Cột dự đoán trong bảng bao gồm mọi đầu ra L2, kể cả trường hợp hồ sơ tham chiếu để trống nhãn chi tiết. Vì vậy, mô hình đã đưa ra 39 nhãn L2, trong khi 103 ảnh có nhãn L2 để đối chiếu. Sáu lớp C2.2, C2.4, C2.5, C2.7, C2.9 và C2.10 chưa có đầu ra được chấp nhận; C2.8 có một dự đoán nhưng sai. F1 trung bình trên 11 lớp ở điều kiện sử dụng thực tế là 0,2268, thấp hơn nhiều phép đo chỉ xét khả năng phân biệt chi tiết khi đã biết trước nhóm L1.')
p('C2.1 có độ chính xác dự đoán 0,9474 nhưng chỉ nhận diện đúng 0,4865 số ảnh tham chiếu. C2.3 dự đoán 10 ảnh và đúng 7; C2.6 đúng 1/2; C2.11 dự đoán đúng 7 ảnh và bỏ sót 1 trong 8 ảnh tham chiếu. Với các lớp ít mẫu, đây là kết quả của một nhóm ảnh nhỏ, chưa phải đặc tính ổn định của toàn lớp.')
image(QA/'figures/07_l2_class_diagnostics.png','Số ảnh theo từng phần dữ liệu và F1 L2 theo lớp',
      'Biểu đồ đặt số mẫu ở các phần huấn luyện, xác thực và kiểm thử cạnh điểm F1 của từng lớp. Một số lớp có rất ít ảnh trong phần kiểm thử nên điểm số có thể thay đổi mạnh chỉ vì một trường hợp. Cột bằng 0 cũng không có nghĩa lớp đã được kiểm tra trên quy mô đủ lớn. Phần so sánh L2 khi đã biết nhãn L1 chỉ phân tích riêng khả năng nhận diện tư thế chi tiết.')
sub('9.2. Ngưỡng validation và sai lệch khi sang test')
table('Các lớp được mở ngưỡng L2 ở nhánh ảnh',['Lớp','Ngưỡng','Xác thực đúng/nhận','Khoảng tin cậy Wilson 95%','Kiểm thử đúng/nhận'],[
 ['C2.1','0,8424','17/17','0,8157–1,0000','18/19'],['C2.3','0,6730','11/12','0,6461–0,9851','7/10'],['C2.6','0,6059','3/3','0,4385–1,0000','1/2'],['C2.8','0,2293','3/3','0,4385–1,0000','0/1'],['C2.11','0,0000','6/6','0,6097–1,0000','7/7']],[2,2.8,3.5,5.7,3.5])
p('Mục tiêu độ chính xác dự đoán 90% chỉ áp dụng khi lựa chọn ngưỡng trên tập xác thực. C2.8 đạt 3/3 trường hợp ở bước này nhưng dự đoán duy nhất trên tập kiểm thử lại sai, cho thấy kết quả từ số mẫu nhỏ có thể thiếu ổn định. C2.11 có một nhãn chi tiết trong nhóm nằm; hệ thống vẫn phải xác nhận L1 và mức đủ căn cứ trước khi trả nhãn này, không tự động gán cho mọi ảnh nằm. [2], [3]')
sub('9.3. Phạm vi của rà soát trực quan')
p('Hồ sơ ngày 29/10 đã đối chiếu 35 trường hợp demo do người dùng chọn với ảnh gốc và crop khi cần. Những ca này giúp phát hiện nhầm ngồi/đứng/chuyển động, bất nhất ở cảnh cưỡi thú và thiếu bằng chứng vùng chân. Đây là tập được chọn vì có vấn đề, không phải mẫu ngẫu nhiên để ước lượng tỷ lệ lỗi chung. Các sửa đổi ngày 30–31/10 được đặt trong bối cảnh phản hồi đó; kết quả trên test cũ tiếp tục có giá trị chẩn đoán, nhưng không còn là bằng chứng độc lập mới. [5]–[7]')
h('10. MỨC ĐỘ ĐẦY ĐỦ CỦA SỔ TAY ĐÁNH GIÁ')
table('Bằng chứng đã lưu và khoảng trống kiểm chứng',['Nội dung','Trạng thái','Ý nghĩa'],[
 ['Dự đoán theo từng ảnh','125 kết quả ở mỗi hướng và cấu hình triển khai','Đối chiếu được mã ảnh, nhãn tham chiếu và quyết định cuối'],['Kết quả theo lớp','11 lớp L2; có phân tích điểm mốc theo lớp','Nhận diện lớp ít ảnh hoặc chưa có đầu ra chi tiết'],['Lịch sử huấn luyện','Có hồ sơ cho cả sáu mô hình','Phân biệt kết quả tốt nhất với trạng thái cuối'],['Lựa chọn mô hình','Có bảng tổng hợp và quyết định đã lưu','Truy lại kiến trúc, cách khởi tạo và ngưỡng'],['Dữ liệu và mã nguồn','Có phiên bản nhãn, mã kiểm tra và bản lưu chương trình','Đối chiếu được dữ liệu và quy trình đã sử dụng'],['Kiểm tra phần mềm','Chín kiểm tra hồi quy đạt; kiểm tra toàn quy trình hoàn tất','Xác nhận vận hành, không thay thế đánh giá chất lượng mô hình'],['Đánh giá trên ảnh mới','Chưa có trong kết quả hiện hành','Chưa kết luận khả năng áp dụng rộng'],['Thời gian và chi phí xử lý','Chưa được đo định lượng','Chưa khẳng định khả năng đáp ứng thời gian thực']],[4.3,6.6,6.6])
p('Hồ sơ nâng cấp ghi nhận mô hình có thể được mở lại từ trọng số đã lưu và hệ thống từ chối cấu hình không khớp. Kết quả ở phiên làm việc mới trùng với bản ghi đánh giá; thao tác này chỉ xác nhận khả năng sử dụng lại kết quả đã có, không tạo thêm một lần huấn luyện hay một phép đo chất lượng mới. [6], [8]')
h('11. HIỆU NĂNG THEO NHÓM TƯ THẾ L1')
p('Để phản ánh đầu ra người dùng thực sự nhận được, bảng dưới được tính lại từ kết quả đã lưu sau khi áp dụng ngưỡng từ chối. “Đúng/tổng” là số ảnh có nhãn L1 đúng trên tổng số ảnh thuộc lớp đó; trường hợp bị từ chối được tính là chưa có câu trả lời đúng. Vì vậy, số đúng là 112 thay vì 113 của độ chính xác L1 trước ngưỡng ở mục 8. [2]')
table('Kết quả L1 sau ngưỡng theo lớp',['Gold L1','Số ảnh','Ảnh đúng L1','Keypoint đúng L1','Ảnh bị từ chối'],[[c,len([r for r in pred if r['gold_l1']==c]),sum(r['gold_l1']==c and r['pred_l1']==c for r in pred),sum(r['gold_l1']==c and r['pred_l1']==c for r in kp),sum(r['gold_l1']==c and not r['pred_l1'] for r in pred)] for c in ['C1.1','C1.2','C1.3','C1.4']],[3.2,3,3.8,4.2,3.3])
table('Ma trận nhầm lẫn L1 sau ngưỡng của nhánh ảnh',['Gold → Dự đoán','Ngồi','Đứng','Chuyển động','Nằm','Từ chối'],[[c]+[sum(r['gold_l1']==c and r['pred_l1']==cc for r in pred) for cc in ['C1.1','C1.2','C1.3','C1.4','']] for c in ['C1.1','C1.2','C1.3','C1.4']],[4.3,2.4,2.4,3.6,2.4,2.4])
p('Nhóm đứng chỉ đúng 8/13 sau ngưỡng, trong khi ngồi đúng 76/79. Ba ảnh đứng bị gán chuyển động và ba ảnh chuyển động bị gán đứng, cho thấy ranh giới giữa tư thế trụ và động tác là điểm cần ưu tiên. Nhóm nằm đúng 9/9 ở L1 nhưng chỉ có chín ảnh; kết quả này không được dùng để kết luận lớp nằm đã giải quyết hoàn toàn, nhất là khi hình học chi dưới ở nhóm này còn yếu.')
h('12. ẢNH HƯỞNG CỦA KHẢ KIẾN VÀ CHE KHUẤT')
p('Các bảng phân nhóm sau đây nối kết dự đoán test với metadata của manifest bằng image_id. Chỉ số là tỷ lệ L1 đúng sau ngưỡng trên toàn bộ ảnh trong nhóm; đây là phép tổng hợp bổ sung cho báo cáo, không phải chỉ số thô trong SUMMARY. Các nhóm cùng một thuộc tính không chồng lấn; nhóm giữa hai thuộc tính có thể chứa cùng ảnh.')
data=[]
for field,label in [('visibility','Khả kiến'),('occlusion_type','Che khuất')]:
 names={'full':'Đầy đủ','partial':'Một phần','heavily_occluded':'Che khuất nặng','garment':'Y phục','none':'Không che','figure':'Nhân vật','object':'Vật thể'}
 for val in sorted(set(lookup[r['image_id']][field] for r in pred)):
  a=[r for r in pred if lookup[r['image_id']][field]==val];correct=sum(r['gold_l1']==r['pred_l1'] for r in a)
  data.append([label,names.get(val,val),len(a),correct,fmt(correct/len(a))])
table('L1 sau ngưỡng theo khả kiến và che khuất',['Thuộc tính','Nhóm','Số ảnh','Đúng','Tỷ lệ'],data,[4,4.8,2.9,2.9,2.9])
p('Nhóm đầy đủ đạt 86/94, còn nhóm một phần đạt 23/28. Ba ảnh che khuất nặng đều đúng L1, nhưng số mẫu quá nhỏ để suy ra che khuất nặng dễ hơn. Tương tự, nhóm không che chỉ đúng 18/25 trong khi nhóm y phục đúng 85/91; chênh lệch có thể liên quan phân bố lớp và đặc trưng của từng nhóm, không xác lập quan hệ nhân quả giữa che khuất và hiệu năng.')
p('Chẩn đoán hình học chi dưới sử dụng sáu khớp hông–gối–cổ chân. Trên các ảnh test đủ điểm mốc, lower-body PCK của C2.1 là 0,9429 nhưng chỉ 0,3750 ở C2.5, 0,4524 ở C2.7 và 0,2222 ở C2.9. Hình học vùng chân là một nút thắt có bằng chứng; cần xác minh bằng đối chiếu ảnh–nhãn–dự đoán trước khi quyết định sửa nhãn hoặc huấn luyện pose mới. [2]')
h('13. PHÂN BỐ LỖI THEO KÍCH THƯỚC VÀ TỪNG ẢNH')
sub('13.1. Kích thước nhân vật trong ảnh nguồn')
table('L1 sau ngưỡng theo tỷ lệ diện tích bbox',['Nhóm','Quy tắc','Số ảnh','Đúng','Tỷ lệ'],[
 ['Nhỏ','Dưới 10%',9,9,'1,0000'],['Trung bình','Từ 10% đến dưới 30%',53,48,'0,9057'],['Lớn','Từ 30% trở lên',63,55,'0,8730']],[3,6,2.8,2.8,2.9])
p('Tỷ lệ kích thước được tính bằng diện tích khung bao nhân vật chia cho diện tích toàn ảnh. Tuy nhiên, bộ phân loại nhận ảnh nhân vật đã cắt sẵn, nên kết quả 9/9 ở nhóm nhỏ không chứng minh mô hình có thể tự tìm nhân vật nhỏ trong tranh toàn cảnh. Kết quả này chỉ phản ánh phân loại trên chín ảnh cắt đã chuẩn bị.')
sub('13.2. Hình học theo lớp tư thế khó')
geo=[r for r in cr(RUN/'pose_estimator/geometry_by_class.csv') if r['split']=='test']
table('PCK toàn thân và chi dưới trên test đủ điểm mốc',['Lớp','Số ảnh','PCK toàn thân','PCK chi dưới'],[[r['l2_code'],r['images'],fmt(r['pck']),fmt(r['lower_body_pck'])] for r in sorted(geo,key=lambda r:int(r['l2_code'].split('.')[1]))],[4,3.5,5,5])
p('Support trong bảng hình học khác support phân loại L2 vì chỉ ảnh đủ điểm mốc được đưa vào phép đo này. C2.11 có tám ảnh test mang L2 nhưng chỉ hai ảnh thuộc đánh giá hình học đầy đủ; PCK toàn thân 0,4706 và chi dưới 0,2500 của hai ảnh đó không mâu thuẫn với việc bộ phân loại ảnh nhận đúng bảy nhãn C2.11. Hai nhiệm vụ và mẫu số khác nhau.')
h('14. CA ĐIỂN HÌNH TỐT VÀ CẦN ƯU TIÊN')
table('Các ca đối chiếu từ dự đoán triển khai đã lưu',['Mã ảnh','Nhãn tham chiếu','Đầu ra','Ý nghĩa chẩn đoán'],[
 ['THK000514','C1.1 / C2.1','C2.1','Nhận đúng nhãn chi tiết'],['THK000506','C1.1 / C2.1','C1.1','Đúng tổng quát; chưa đạt ngưỡng chi tiết'],['THK000705','C1.1 / C2.2','C2.3','Đúng L1 nhưng sai cấu hình chân ở L2'],['THK000748','C1.1 / C2.5','C2.3','Nhầm quỳ/ngồi gót với một chân thả'],['THK000914','C1.1; L2 trống','C2.1','Đưa ra chi tiết vượt nhãn tham chiếu'],['HAR_69346','C1.2 / C2.8','Không xác định','Từ chối L1; cần phân tích mức tin cậy'],['Machig_Labdron_\nGoogle_Art_Project','C1.3 / C2.10','C2.8','Sai cả nhánh L1 và nhãn chi tiết']],[5.6,4.1,2.8,5])
p('Các trường hợp trong bảng là ví dụ truy vết theo kết quả đã lưu; chúng không được chọn để ước lượng tỷ lệ lỗi. Với ca có L2 trống, việc mô hình đưa ra L2 được xem là không tuân theo tham chiếu đánh giá, chưa đủ căn cứ kết luận nhãn mô hình sai về mặt ngữ nghĩa nếu chưa được người duyệt đối chiếu. Cần giữ nguyên nhãn đã duyệt cho đến khi có quyết định phân xử có hồ sơ.')
sub('14.1. Sáu trường hợp mô hình trả kết quả phù hợp')
p('Sáu ảnh dưới đây được chọn từ hồ sơ dự đoán đã lưu của lượt đánh giá chính. “Phù hợp” nghĩa là đầu ra khớp nhãn tham chiếu ở mức chi tiết khi có L2, hoặc khớp L1 khi hồ sơ không có L2. Các ca này minh họa cách hệ thống hoạt động, không phải mẫu ngẫu nhiên và không dùng để ước lượng hiệu năng chung. Nhãn tham chiếu là nhãn đã duyệt trong bộ dữ liệu; sự trùng khớp không xác nhận nhãn đúng tuyệt đối.')
demo_case_page(GOOD_CASES,0,'good')
sub('14.2. Sáu trường hợp cần cải thiện hoặc người duyệt xem lại')
p('Các ví dụ sau được chọn vì có sai lệch giữa đầu ra đã lưu và nhãn tham chiếu. Phần nhận xét nêu rõ sai lệch ở mức tổng quát, mức chi tiết hoặc việc đưa ra nhãn chi tiết khi không có tham chiếu. Đây là các ca chẩn đoán có chủ đích, không đại diện cho tỷ lệ lỗi của toàn bộ tập test.')
demo_case_page(NEEDS_REVIEW,0,'review')
table('Thay đổi mô tả trên năm lớp ưu tiên so với cấu hình trước',['Lớp','Số test','Recall L2 cũ','Recall L2 mới','Sai/từ chối L1 cũ → mới'],[[r['code'],r['support'],fmt(r['old_l2_exact_recall']),fmt(r['new_l2_exact_recall']),r['old_wrong_or_rejected_l1']+' → '+r['new_wrong_or_rejected_l1']] for r in cr(RUN/'deployment/target_labels_vs_previous.csv')],[2.3,2.3,3.4,3.4,6.1])
p('Tệp đối sánh cho thấy recall L2 của C2.3 tăng từ 1/17 lên 7/17 và C2.11 từ 2/8 lên 7/8. C2.5, C2.7 và C2.10 vẫn chưa có nhãn L2 đúng được trả ra. Đây là so sánh hồi cứu giữa các cấu hình trên test đã xem, không phải thí nghiệm ablation kiểm soát từng thay đổi; không thể tách riêng đóng góp của độ phân giải, loss, seed hay hiệu chỉnh ngưỡng. [2], [6]')
h('15. CẤU TRÚC GÓI DỮ LIỆU VÀ KHẢ NĂNG TÁI LẬP')
sub('15.1. Định danh phiên bản dữ liệu và mô hình')
p('Hồ sơ dữ liệu mang phiên bản thangka_pose_v1.1.0_dacntt_2026-10-20; nhãn làm việc đã được cập nhật ngày 30/10. Tên phiên bản được đối chiếu cùng bảng kê khai dữ liệu và cấu hình huấn luyện để xác định đúng nguồn ảnh, nhãn và phần chia dùng trong báo cáo. Mã kiểm tra SHA-256 của bảng kê khai khớp với thông tin lưu trong hồ sơ huấn luyện và đánh giá điểm mốc:')
q=p('527fd2f85fd60af921e696272ff7ca3bb39dbf7ee41ac1763501330603b71637')
for r in q.runs:r.font.size=Pt(10)
p('Một mã kiểm tra trong biên bản thống nhất nhãn ngày 30/10 khác với giá trị tính từ bảng kê khai hiện hành. Báo cáo dùng giá trị được tính trực tiếp và đối chiếu với hồ sơ mô hình đã lưu; biên bản cần được hiệu chỉnh để tránh nhầm phiên bản. Các bản xuất ngày 20/10 được giữ làm tài liệu lịch sử, không dùng thay cho nhãn hiện hành nếu chưa kiểm tra. [4], [5]')
table('Các nhóm hồ sơ phục vụ đối chiếu và tái lập',['Hồ sơ','Thông tin được lưu'],[
 ['Dữ liệu và hệ thống nhãn','Mã ảnh, nhãn đã duyệt, nguồn, quyền sử dụng, điểm mốc và phương án chia'],['Kiểm tra chất lượng','Số lượng ảnh, ảnh trùng và điều kiện môi trường khi thực nghiệm'],['Huấn luyện phân loại ảnh','Sáu lịch huấn luyện, kết quả tốt nhất và trạng thái có thể tiếp tục'],['Phân loại theo điểm mốc','Cấu hình đã chọn và dự đoán theo từng ảnh'],['Đánh giá hình học','Chỉ số khung bao và điểm mốc theo ảnh, theo lớp'],['Cấu hình triển khai','Ngưỡng quyết định, nhãn đầu ra và các trường hợp cần rà soát'],['Tổng hợp và độ bất định','Kết quả chung và ước lượng độ dao động khi so sánh hai nhánh']],[5.2,12.3])
p('Để nạp lại kết quả, cần giữ thống nhất phiên bản ảnh, nhãn, mô hình đã lưu và các ngưỡng đã lựa chọn. Để lặp lại quá trình huấn luyện, cần bổ sung môi trường phần mềm, cách khởi tạo, cấu hình tối ưu và dữ liệu đầu vào tương ứng. Việc mở lại được mô hình đã lưu xác nhận khả năng tái sử dụng trong môi trường hiện có, nhưng không bảo đảm mọi máy tính sẽ tạo kết quả hoàn toàn giống nhau.')
sub('15.2. Mở lại demo và kiểm soát sai cấu hình')
p('Nhóm đã mở lại mô hình trong một phiên làm việc mới và kiểm tra sự phù hợp giữa phiên bản dữ liệu, kích thước ảnh đầu vào và cấu hình đã lưu. Kết quả dự đoán khớp với hồ sơ đánh giá tương ứng; quá trình này không huấn luyện lại mô hình và không chọn lại ngưỡng. [8]')
p('Hồ sơ bàn giao cần bổ sung mã kiểm tra riêng cho trọng số và phương án phân chia. Mã kiểm tra của dữ liệu xác nhận đúng phiên bản bảng kê khai, nhưng không thay thế việc nhận diện từng tệp mô hình. Tài liệu hướng dẫn gán nhãn cũng cần được rà soát để thống nhất với các quyết định đã áp dụng ở giai đoạn pilot và phiên bản hiện hành.')
h('16. CHẤT LƯỢNG, NGUỒN GỐC DỮ LIỆU VÀ GIỚI HẠN')
sub('16.1. Phạm vi sử dụng và chất lượng nguồn')
p('Hồ sơ quyền sử dụng ghi nhận 832 ảnh chỉ dành cho nghiên cứu nội bộ và 41 ảnh đã được xác minh điều kiện sử dụng. Bộ dữ liệu hiện đáp ứng yêu cầu kỹ thuật cho nghiên cứu nội bộ, chưa sẵn sàng phát hành công khai. Việc có ảnh trong kho không đồng nghĩa với quyền phân phối ảnh hoặc trọng số mô hình; mọi hình thức công bố ngoài phạm vi môn học cần được rà soát theo nguồn và quyền của từng ảnh. [4]')
p('Báo cáo giữa kỳ xác định bộ dữ liệu là hồ sơ nội bộ phục vụ huấn luyện, với phạm vi ảnh được sàng lọc theo khả năng sử dụng và bằng chứng thị giác. Vì vậy, phân bố hiện tại không đại diện thống kê cho toàn bộ nghệ thuật Thangka. Kết quả trên dữ liệu nội bộ không cho phép suy ra tần suất tư thế hoặc hiệu năng trên các bộ sưu tập chưa khảo sát. [1], [4]')
sub('16.2. Các giới hạn ảnh hưởng trực tiếp đến kết luận')
p('Thứ nhất, tập kiểm thử đã được xem qua nhiều vòng chẩn đoán và cải tiến. Việc chọn ngưỡng trên tập xác thực giúp tránh điều chỉnh trực tiếp theo kết quả kiểm thử trong một lượt huấn luyện, nhưng không xóa được ảnh hưởng của phản hồi kiểm thử qua nhiều vòng phát triển. Một tập độc lập mới là điều kiện cần để kết luận về khả năng áp dụng cho ảnh chưa gặp.')
p('Thứ hai, một số tư thế hiếm chỉ có vài ảnh trong tập xác thực và kiểm thử. Tập xác thực đã được dùng để chọn kiến trúc, hiệu chỉnh xác suất và chọn ngưỡng, nên kết quả có thể phù hợp với chính tập này hơn mức đạt được trên ảnh mới. Cần kiểm tra thêm bằng nhiều phương án chia theo nhóm hoặc một nhóm ảnh riêng để hiệu chỉnh trước khi chốt cấu hình cuối.')
p('Thứ ba, kết quả phân loại dùng ảnh nhân vật đã cắt sẵn; nhóm chưa đo toàn bộ quy trình từ tranh nguyên bản qua chọn nhân vật đến nhãn cuối. PCK và OKS chỉ được tính trên ảnh có đủ điểm mốc, trong khi độ chính xác L1 tính trên toàn bộ tập kiểm thử. Mọi bảng cần nêu rõ điều kiện đầu vào và số ảnh được dùng để tránh so sánh sai.')
p('Thứ tư, “Không xác định” hiện là quyết định từ chối theo ngưỡng trong phân phối. Chưa có tập âm hoặc OOD để đánh giá khả năng từ chối tranh không thuộc phạm vi, nhân vật nhiều chi hoặc ảnh không chứa người. Không được xem cờ từ chối là bộ phát hiện ngoài phân phối đã được kiểm chứng.')
p('Thứ năm, việc lùi về nhãn tổng quát hạn chế các kết luận chi tiết thiếu căn cứ nhưng làm giảm số ảnh được gán L2. Sáu lớp hiện chưa được mở ở đầu ra chi tiết. Nhóm chưa kiểm tra riêng từng thay đổi để xác định yếu tố nào tạo ra mức cải thiện ở các lớp còn lại. Tỷ lệ người duyệt phải sửa khung bao hoặc điểm mốc cũng chưa được đo trên một tập đánh giá thống nhất.')
h('17. CÔNG VIỆC ĐÃ HOÀN THÀNH VÀ KẾ HOẠCH')
sub('17.1. Đối chiếu với yêu cầu kỳ trước')
table('Mức hoàn thành các hạng mục đặt ra tại giữa kỳ',['Hạng mục','Trạng thái đến 01/11','Điều kiện để hoàn tất chắc chắn'],[
 ['Dữ liệu và split','Đã sử dụng phương án 612/136/125 đã chốt giữa kỳ','Lưu rõ ánh xạ pilot 100 ảnh và tập đánh giá hiện tại nếu cần so sánh'],['Đồng thuận nhãn','Có 873 cặp phiếu; κ mã tư thế 0,9652','Bảo toàn phiếu gốc, dấu thời gian độc lập và hồ sơ phân xử'],['Huấn luyện phân loại','Đã hoàn tất hai kiến trúc, ba lần khởi tạo và nhánh keypoint','Đánh giá trên một tập độc lập mới trước kết luận cuối'],['Phân tích lớp khó','C2.3 và C2.11 có cải thiện trong đối chiếu cấu hình','C2.5, C2.7, C2.10 vẫn chưa trả L2 đúng; cần tăng bằng chứng'],['Truy xuất nguồn gốc','Có manifest, môi trường và bản chụp lượt chạy','Bổ sung mã kiểm tra trọng số và phân chia; hoàn thiện hồ sơ bàn giao'],['Demo mô hình đã lưu','Đã nạp lại checkpoint và tạo 12 ca minh họa','Đo thời gian đáp ứng, thử ảnh toàn cảnh và trường hợp ngoài phạm vi'],['Hiệu chỉnh bởi người duyệt','Chưa có phép đo riêng cho tỷ lệ phải sửa đầu ra','Lưu dự đoán ban đầu, bản sửa cuối và thời gian xử lý']],[4.1,6.7,6.7])
sub('17.2. Kế hoạch thực hiện giai đoạn tiếp theo')
table('Kế hoạch ưu tiên và tiêu chí nghiệm thu đề xuất',['Ưu tiên','Công việc','Sản phẩm và tiêu chí nghiệm thu'],[
 ['1','Đối chiếu các tập đánh giá','Lập danh sách ảnh pilot 100 mẫu và ảnh trong phương án hiện tại; nêu số trường hợp trùng và giữ rõ mục đích từng tập'],['2','Khóa phép đánh giá mới','Chốt danh sách ảnh mới, tiêu chí chọn và mã kiểm tra trước khi điều chỉnh mô hình'],['3','Kiểm tra độ ổn định lớp hiếm','Đánh giá trên nhiều phương án chia theo nhóm; báo số ảnh và mức dao động; giữ riêng tập kiểm thử'],['4','Đối chứng cải tiến ước lượng tư thế','Dùng cùng quy ước đo; so độ chính xác điểm mốc chi dưới, nhãn chi tiết và chi phí xử lý'],['5','Đánh giá từng thay đổi ở nhánh ảnh','Kiểm tra riêng ảnh đầu vào, cách kết hợp hai cấp nhãn và ngưỡng đủ căn cứ trong điều kiện còn lại như nhau'],['6','Đánh giá bản minh họa khi sử dụng','Thử tranh toàn cảnh, ảnh cắt sẵn, ảnh không có nhân vật và ảnh ngoài phạm vi; đo thời gian trung vị và nhóm 5% chậm nhất'],['7','Hoàn thiện hồ sơ bàn giao','Bổ sung mã kiểm tra trọng số, hướng dẫn nhãn thống nhất, hồ sơ quyền và nhật ký sửa đầu ra']],[1.6,6.3,9.6])
p('Các mục trên là kế hoạch đề xuất, chưa được tính vào kết quả đã hoàn thành. Nguyên tắc nghiệm thu là tăng chất lượng ở lớp yếu mà vẫn báo đầy đủ coverage và lỗi; không hạ mục tiêu precision chỉ để ép mô hình hiển thị nhãn L2. Nếu một lớp chưa có đủ bằng chứng, đầu ra L1 hoặc từ chối vẫn phải được ghi nhận minh bạch.')
h('18. KẾT LUẬN')
p('Trong kỳ báo cáo lần 5, nhóm đã chuyển từ giai đoạn chuẩn bị dữ liệu của báo cáo giữa kỳ sang huấn luyện và đánh giá các hướng phân loại tư thế. Hồ sơ hiện hành gồm 873 ảnh được duyệt, phương án chia 612/136/125 và 729 ảnh có nhãn chi tiết. Nhóm hoàn tất sáu mô hình ảnh, đánh giá thêm nhánh điểm mốc và nạp lại mô hình đã lưu để tạo các trường hợp minh họa. Cấu hình được chọn là tổ hợp ba ResNet-18; nhánh điểm mốc được giữ để so sánh và phân tích hình học. [1]–[4]')
p('Trên tập kiểm thử hiện hành, nhánh ảnh đạt độ chính xác L1 90,40% và F1 trung bình theo lớp 0,8546. Hệ thống trả đúng nhãn L2 cho 33/103 ảnh có tham chiếu; sáu lớp L2 chưa được mở ở đầu ra cuối. Khả năng phân loại tổng quát đã được đo, nhưng tỷ lệ ảnh nhận nhãn chi tiết còn hạn chế. Mô hình điểm mốc đạt PCK 0,7862 trên 82 ảnh đủ điểm; đây là phép đo riêng theo quy ước hiện hành, không so trực tiếp với mốc pilot 0,7265 trên 100 ảnh của báo cáo giữa kỳ.')
p('Giai đoạn tiếp theo cần đối chiếu rõ các tập đánh giá, xây dựng một phép kiểm tra độc lập mới, nâng độ ổn định ở các lớp ít ảnh và đánh giá toàn quy trình từ tranh nguyên bản đến nhãn tư thế. Khi chưa hoàn thành các bước này, kết quả chỉ nên được xem là mốc thực nghiệm nội bộ, chưa đủ để kết luận về khả năng áp dụng rộng.')
h('PHỤ LỤC A. HÌNH ẢNH ĐÁNH GIÁ ĐẦY ĐỦ')
p('Phụ lục này đưa vào báo cáo toàn bộ 16 tệp hình kết quả trong thư mục đánh giá pose của lượt chạy chính ngày 01/11/2026. Mười biểu đồ được trình bày nguyên bản; sáu ảnh theo lô được ghép theo cặp nhãn tham chiếu và dự đoán để tiện đối chiếu, không thay đổi nội dung ảnh. Các biểu đồ phát hiện nhân vật và điểm mốc không phải là kết quả phân loại tư thế L1/L2. [2]')
sub('A.1. Kết quả đánh giá khung bao nhân vật')
box_figures=[
 ('BoxF1_curve.png','Mức cân bằng giữa nhận diện đúng và khả năng tìm đủ đối tượng theo ngưỡng','Đường biểu diễn cho biết điểm cân bằng thay đổi ra sao khi thay ngưỡng tiếp nhận. Giá trị cao trên tập ảnh này cho thấy kết quả thuận lợi trong điều kiện đánh giá hiện tại; nó chưa chứng minh mô hình hoạt động tương tự trên ảnh mới.'),
 ('BoxP_curve.png','Tỷ lệ khung bao dự đoán khớp với tham chiếu theo ngưỡng','Biểu đồ cho thấy mức độ chính xác của các khung bao được chấp nhận. Tăng ngưỡng có thể hạn chế khung báo nhầm nhưng cũng làm tăng nguy cơ bỏ sót; vì vậy cần đọc cùng biểu đồ khả năng tìm đủ đối tượng.'),
 ('BoxPR_curve.png','Quan hệ giữa khung bao đúng và khả năng tìm đủ đối tượng','Đường cong mô tả sự đánh đổi giữa việc hạn chế báo nhầm và việc tìm đủ đối tượng. Kết quả này chỉ phản ánh bước định vị nhân vật trong tập đánh giá, không đo nhãn tư thế.'),
 ('BoxR_curve.png','Tỷ lệ tìm thấy đối tượng theo ngưỡng tin cậy','Khi ngưỡng tiếp nhận tăng, một số khung ít chắc chắn bị loại bỏ và tỷ lệ tìm thấy có thể giảm. Hình này giúp đọc ảnh hưởng của ngưỡng đến số đối tượng còn được giữ lại; không thể dùng riêng lẻ để kết luận chất lượng toàn hệ thống.')]
for i,(name,title_text,comment_text) in enumerate(box_figures):
 image(RUN/'pose_estimator/geometry_test'/name,title_text,comment_text);page()
sub('A.2. Kết quả tổng hợp phát hiện đối tượng')
image(RUN/'pose_estimator/geometry_test/confusion_matrix.png','Ma trận số lượng đối tượng tham chiếu và đối tượng được mô hình phát hiện',
      'Các ô trên đường chéo thể hiện trường hợp dự đoán trùng với nhãn; các ô còn lại cho thấy trường hợp bỏ sót hoặc phát hiện dư. Bộ đánh giá pose chỉ có một nhóm đối tượng “figure”, nên ma trận này không phân biệt các lớp tư thế. Hãy đọc số đếm cùng các chỉ số tổng hợp ở mục 8.3.');page()
image(RUN/'pose_estimator/geometry_test/confusion_matrix_normalized.png','Ma trận chuẩn hóa kết quả phát hiện đối tượng',
      'Chuẩn hóa giúp so sánh tỷ lệ giữa các ô dù số lượng mẫu khác nhau. Do biểu đồ vẫn thuộc bài toán phát hiện một nhóm đối tượng, nó không cho biết mô hình phân biệt đúng giữa ngồi, đứng, chuyển động hay nằm.');page()
sub('A.3. Kết quả đánh giá điểm mốc cơ thể')
pose_figures=[
 ('PoseF1_curve.png','Mức cân bằng giữa điểm mốc đúng và khả năng tìm đủ điểm mốc','Đường cong cho thấy mức cân bằng giữa độ chính xác và độ bao phủ của các điểm mốc khi thay ngưỡng. Điểm cao trên tập đánh giá không loại trừ sai lệch ở từng khớp, nhất là các vị trí bị che hoặc được thể hiện cách điệu.'),
 ('PoseP_curve.png','Tỷ lệ điểm mốc dự đoán khớp theo ngưỡng tin cậy','Biểu đồ phản ánh tỷ lệ các điểm mốc được dự đoán đúng trong số điểm được chấp nhận. Ngưỡng cao thường giữ lại các điểm chắc chắn hơn nhưng có thể làm giảm số khớp được phát hiện; cần xem kèm PCK và OKS.'),
 ('PosePR_curve.png','Quan hệ giữa độ chính xác và khả năng tìm đủ điểm mốc','Đường cong mô tả sự đánh đổi giữa việc giữ các điểm có vị trí đáng tin cậy và việc tìm đủ các khớp. Đây là đánh giá tọa độ điểm mốc, không đồng nghĩa với độ đúng của nhãn tư thế chi tiết.'),
 ('PoseR_curve.png','Tỷ lệ tìm thấy điểm mốc theo ngưỡng tin cậy','Hình cho thấy số điểm mốc còn được chấp nhận thay đổi theo ngưỡng. Điểm mốc bị che, nhỏ hoặc khó phân biệt có thể ảnh hưởng đến kết quả; các trường hợp ấy cần được xem cùng ảnh và nhãn tham chiếu.')]
for name,title_text,comment_text in pose_figures:
 image(RUN/'pose_estimator/geometry_test'/name,title_text,comment_text);page()
sub('A.4. Đối chiếu nhãn điểm mốc và dự đoán theo từng lô')
batch_comments=[
 'Hai phần của hình lần lượt thể hiện điểm mốc tham chiếu và kết quả ước lượng trên cùng ảnh. Ở cảnh có nhiều chi tiết hoặc nhân vật phụ, cần xác nhận khung và điểm mốc thuộc đúng nhân vật được đánh giá. Đây là minh họa trực quan, không thay cho phép đo trên toàn bộ tập.',
 'Đối chiếu cho thấy bộ dữ liệu có cảnh nhiều nhân vật và nền trang trí dày. Người đọc cần xem cả vị trí khung bao lẫn các điểm mốc, thay vì chỉ dựa vào nhãn độ tin cậy phát hiện. Kết quả định lượng vẫn được tổng hợp riêng trên 82 ảnh đủ điểm mốc.',
 'Ảnh có nhiều nhân vật và tư thế chồng lấp làm việc chọn đúng đối tượng trở nên quan trọng. Hình này giúp rà soát trực quan cách mô hình đặt khung và điểm mốc; nó không được chọn ngẫu nhiên và không đại diện riêng cho toàn bộ dữ liệu test.'
]
for n,comment_text in enumerate(batch_comments):
 image(QA/f'pose_val_batch{n}_comparison.png',f'Đối chiếu nhãn tham chiếu và dự đoán điểm mốc trong lô {n}',comment_text);page()
h('TÀI LIỆU THAM KHẢO')
refs=[
 '[1] Trần Thảo My và Trần Thị Kim Ngân, Báo cáo dự án CNTT: Phân tích tư thế phân cấp của nhân vật trong ảnh nghệ thuật Phật giáo, báo cáo giữa kỳ, chốt số liệu ngày 20/10/2026. Tài liệu nội bộ.',
 '[2] Nhóm thực hiện, Hồ sơ thực nghiệm 20261031_174634_seed20261021, outputs/notebook_runs/: SUMMARY.json; dataset_audit.json; environment.json; inter_rater_agreement.json; paired_bootstrap.json; các tệp metrics, predictions, selection và history. Hoàn tất 01/11/2026. Đối chiếu thêm run 20261031_174817_seed20261021.',
 '[3] Nhóm thực hiện, source_notebook.ipynb trong run 20261031_174634_seed20261021, bản chụp mã nguồn thực nghiệm; Thangka_Pose_Training.ipynb trong thư mục dự án. Kiểm tra ngày 01/11/2026.',
 '[4] Nhóm thực hiện, Gói dữ liệu thangka_pose_v1.1.0_dacntt_2026-10-20: data/DATASET_CARD.md; classification_manifest.csv; ontology.json; split_registry.json; keypoints_coco.json; keypoints_partial_coco.json; quality_report.json. CSV có đính chính nhãn ngày 30/10/2026.',
 '[5] Nhóm thực hiện, Thống nhất nhãn ngày 30/10/2026, data/LABEL_CONSENSUS_20261030.md. Các quyết định gán nhãn Ngân–My; hash trong văn bản được đối chiếu lại với manifest thực tế trong báo cáo này.',
 '[6] Nhóm thực hiện, Cải thiện các nhãn tư thế khó, QUALITY_UPGRADE_20261031.md; outputs/quality_training_status.json và quality_smoke_status.json. Trạng thái cập nhật 01/11/2026.',
 '[7] Nhóm thực hiện, Hồ sơ rà soát demo, DEMO_AUDIT_20261029.md. Phân tích 35 trường hợp do người dùng chọn và giới hạn của kiểm thử lịch sử, 29/10/2026.',
 '[8] Nhóm thực hiện, saved_demo.py; notebook_cells.py; tests/test_quality_pipeline.py; tests/test_saved_demo.py. Mã nạp lại demo và kiểm thử hồi quy, kiểm tra 01/11/2026.',
 '[9] Nhóm thực hiện, outputs/pose_baseline/config.json và best.pt; hồ sơ pose_estimator/test_pose_metrics.json của run hiện hành. Cấu hình baseline pose và chỉ số metric schema 2.',
 '[10] K. He, X. Zhang, S. Ren và J. Sun, “Deep Residual Learning for Image Recognition,” CVPR, 2016, tr. 770–778. https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf. Truy cập 01/11/2026.',
 '[11] M. Sandler, A. Howard, M. Zhu, A. Zhmoginov và L.-C. Chen, “MobileNetV2: Inverted Residuals and Linear Bottlenecks,” CVPR, 2018. https://openaccess.thecvf.com/content_cvpr_2018/html/Sandler_MobileNetV2_Inverted_Residuals_CVPR_2018_paper.html. Truy cập 01/11/2026.',
 '[12] C. Guo, G. Pleiss, Y. Sun và K. Q. Weinberger, “On Calibration of Modern Neural Networks,” Proceedings of the 34th International Conference on Machine Learning, PMLR 70, tr. 1321–1330, 2017. https://proceedings.mlr.press/v70/guo17a.html. Truy cập 01/11/2026.'
]
for t in refs:
 x=p(t)
 x.alignment=WD_ALIGN_PARAGRAPH.LEFT
 for r in x.runs:r.font.size=Pt(11)
for list_paragraph,list_label in pending_caption_lists:
 runs=list_paragraph.runs
 end_run=next((r for r in runs if any(el.tag==qn('w:fldChar') and el.get(qn('w:fldCharType'))=='end' for el in r._r)),None)
 if end_run is not None:
  cached=list_paragraph.add_run('\n'.join(caption_registry[list_label]))
  cached.font.name='Times New Roman';cached.font.size=Pt(10);cached.font.color.rgb=RGBColor(0,0,0)
  end_run._r.addprevious(cached._r)
 list_paragraph.paragraph_format.line_spacing=1.0
 list_paragraph.paragraph_format.widow_control=True
settings=d.settings.element
uf=settings.find(qn('w:updateFields'))
if uf is None:uf=OxmlElement('w:updateFields');settings.append(uf)
uf.set(qn('w:val'),'true')
d.core_properties.title='Báo cáo tiến độ lần 5 tuần 8 9 10 Phân tích tư thế Thangka'
d.core_properties.subject='Tiến độ huấn luyện đến ngày 01/11/2026'
FINAL=OUT/'52300129_52300131_BaoCaoTienDo_Lan5_Tuan8_9_10_Thangka_20261101_TheoBaoCaoGiuaKy.docx'
tmp=QA/'authored.docx';d.save(tmp)
# Preserve opaque original package members; only edited/new parts come from the authoring copy.
changed={'word/document.xml','word/settings.xml','word/_rels/document.xml.rels','[Content_Types].xml','docProps/core.xml'}
with zipfile.ZipFile(REF) as a,zipfile.ZipFile(tmp) as b,zipfile.ZipFile(FINAL,'w',zipfile.ZIP_DEFLATED) as z:
 inventory={name:{'size':len(a.read(name)),'sha256':hashlib.sha256(a.read(name)).hexdigest()} for name in a.namelist()}
 for name in a.namelist():z.writestr(name,b.read(name) if name in changed else a.read(name))
 for name in b.namelist():
  if name not in a.namelist():z.writestr(name,b.read(name))
 (QA/'package_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
print(FINAL)
print('tables',tblno,'figures',figno,'paragraphs',len(d.paragraphs),'words',sum(len(p.text.split()) for p in d.paragraphs))
