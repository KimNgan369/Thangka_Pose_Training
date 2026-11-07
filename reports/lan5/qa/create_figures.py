from pathlib import Path
import csv,json
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
from openpyxl import load_workbook

ROOT=Path.cwd(); RUN=ROOT/'outputs/notebook_runs/20261031_174634_seed20261021'; QA=ROOT/'reports/lan5/qa'; FIG=QA/'figures'; FIG.mkdir(parents=True,exist_ok=True)
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def csvr(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def F(n,b=False): return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),n)
ink='#17212b'; muted='#586776'; grid='#d8e0e6'; teal='#287b74'; gold='#c28b45'; blue='#526e9e'; red='#b33a3a'; purple='#8b6fa8'
def cv(title,subtitle='',size=(1800,900)):
    im=Image.new('RGB',size,'white'); d=ImageDraw.Draw(im); d.text((size[0]/2,26),title,font=F(34,True),fill=ink,anchor='ma')
    if subtitle:d.text((size[0]/2,72),subtitle,font=F(21),fill=muted,anchor='ma')
    return im,d
def box(d,r,title):
    d.rounded_rectangle(r,15,fill='#fbfcfd',outline=grid,width=2);d.text((r[0]+18,r[1]+12),title,font=F(23,True),fill=ink)
def hbars(d,r,labs,vals,color,maxv,labelw):
    x0,y0,x1,y1=r;top=y0+48;bottom=y1-35;rh=(bottom-top)/len(labs);bx=x0+labelw;bw=x1-bx-50
    for j in range(5):
        xx=bx+bw*j/4;d.line((xx,top,xx,bottom),fill=grid,width=1);d.text((xx,bottom+4),str(round(maxv*j/4)),font=F(14),fill=muted,anchor='ma')
    for i,(lab,v) in enumerate(zip(labs,vals)):
        y=top+rh*(i+.5);d.text((x0+10,y),lab,font=F(max(14,min(18,int(rh*.46)))),fill=ink,anchor='lm');w=bw*v/maxv
        d.rounded_rectangle((bx,y-rh*.28,bx+w,y+rh*.28),5,fill=color);d.text((bx+w+6,y),str(v),font=F(16,True),fill=ink,anchor='lm')
def hm(d,r,m,labs,title):
    x0,y0,x1,y1=r;box(d,r,title);n=len(m); left=x0+76;top=y0+58;right=x1-15;bottom=y1-38;cw=(right-left)/n;ch=(bottom-top)/n;mx=max(max(row) for row in m) or 1
    for i in range(n):
        d.text((left-8,top+ch*(i+.5)),labs[i],font=F(15),fill=ink,anchor='rm')
        for j,v in enumerate(m[i]):
            t=v/mx;c=(int(239-137*t),int(246-109*t),int(251-63*t));x=left+j*cw;y=top+i*ch;d.rectangle((x,y,x+cw,y+ch),fill=c,outline='white',width=2)
            if v:d.text((x+cw/2,y+ch/2),str(v),font=F(16,True),fill='white' if t>.48 else ink,anchor='mm')
        d.text((left+cw*(i+.5),bottom+4),labs[i],font=F(15),fill=ink,anchor='ma')
def linechart(d,r,series,title):
    x0,y0,x1,y1=r;box(d,r,title);l=x0+64;t=y0+54;rr=x1-20;b=y1-58
    for i in range(6):
        q=i/5;y=b-(b-t)*q;xx=l+(rr-l)*q;d.line((l,y,rr,y),fill=grid);d.text((l-8,y),f'{q:.1f}',font=F(14),fill=muted,anchor='rm');d.text((xx,b+6),f'{q:.1f}',font=F(14),fill=muted,anchor='ma')
    for k,(pts,col,label) in enumerate(series):
        coords=[(l+x*(rr-l),b-y*(b-t)) for x,y in pts];d.line(coords,fill=col,width=4);yy=t+18+k*24;d.line((l+15,yy,l+48,yy),fill=col,width=4);d.text((l+55,yy),label,font=F(15),fill=ink,anchor='lm')

rows=csvr(ROOT/'data/classification_manifest.csv'); ont=js(ROOT/'data/ontology.json'); l1=ont['level_1'];l2=ont['level_2']; c1=[x['code'] for x in l1];c2=[x['code'] for x in l2]
# 1: distribution panels
im,d=cv('Phân bố dữ liệu và quy mô các tập','Manifest đã khóa: 873 ảnh; L2 tính trên bản ghi có nhãn chi tiết',(1900,900));
for r,t in [((20,120,625,860),'Nhãn L1'),((645,120,1280,860),'Nhãn L2 có nhãn'),((1300,120,1880,860),'Split')]:box(d,r,t)
a=Counter(x['level_1_code'] for x in rows);b=Counter(x['level_2_code'] for x in rows if x['level_2_code']);s=Counter(x['split'] for x in rows)
hbars(d,(30,150,615,825),[f"{x['code']} · {x['vi']}" for x in l1],[a[x] for x in c1],teal,600,205)
hbars(d,(655,150,1270,825),[f"{x['code']} · {x['vi']}" for x in l2],[b[x] for x in c2],gold,300,380)
hbars(d,(1310,150,1870,825),['Train','Validation','Test'],[s['train'],s['val'],s['test']],blue,700,140);im.save(FIG/'01_data_distribution.png')
# 2: rater matrix from actual paired sheets
labs=c1+['C1.5']+c2; idx={x:i for i,x in enumerate(labs)}
def form(p):
    w=load_workbook(p,data_only=True,read_only=False)['Form'];out={}
    for n in range(5,w.max_row+1):
        k=w.cell(n,1).value;v=w.cell(n,3).value
        if k is not None and v is not None:out[str(k).strip()]=str(v).strip()
    return out
a=form(ROOT/'ratings/kappa_form_rater_ngan.xlsx');b=form(ROOT/'ratings/kappa_form_rater_my.xlsx');m=[[0]*len(labs) for _ in labs]
for k in set(a)&set(b):
    if a[k] in idx and b[k] in idx:m[idx[a[k]]][idx[b[k]]]+=1
im,d=cv('Đối chiếu nhãn độc lập giữa hai phiếu','Ghép theo image_id; n = 873 cặp',(1660,1120));hm(d,(30,120,1630,1080),m,labs,'Nhãn Ngan × nhãn My');im.save(FIG/'02_interrater_matrix.png')
# 3: confusion matrices from saved tests
mi=js(RUN/'image_classifier/test_metrics.json');mk=js(RUN/'keypoint_classifier/test_metrics.json')
spec=[(mi['l1_all_test']['confusion_matrix'],c1,'Ảnh · L1 end-to-end'),(mk['l1_all_test']['confusion_matrix'],c1,'Keypoint · L1 end-to-end'),(mi['l2_oracle_given_gold_l1']['confusion_matrix'],c2,'Ảnh · L2 oracle'),(mk['l2_oracle_given_gold_l1']['confusion_matrix'],c2,'Keypoint · L2 oracle')]
im,d=cv('Ma trận nhầm lẫn trên tập test','L2 oracle giả định L1 tham chiếu đã biết; không phải đầu ra triển khai',(1900,1400))
for (mat,labs,title),r in zip(spec,[(20,115,935,740),(965,115,1880,740),(20,765,935,1380),(965,765,1880,1380)]):hm(d,r,mat,labs,title)
im.save(FIG/'03_confusion_matrices.png')
# 4: test risk coverage plus confidence histograms; operating thresholds are chosen on validation
pp=[csvr(RUN/'image_classifier/test_predictions.csv'),csvr(RUN/'keypoint_classifier/test_predictions.csv')]; names=['Ảnh trực tiếp','Keypoint dự đoán']; colors=[teal,gold]
series=[]
for data,col,name in zip(pp,colors,names):
    arr=sorted(data,key=lambda z:float(z['l1_confidence']),reverse=True);ok=0;pts=[(0,0)]
    for i,z in enumerate(arr,1):ok+=z['gold_l1']==z['pred_l1'];pts.append((i/len(arr),ok/i))
    series.append((pts,col,name))
im,d=cv('Đường cong chấp nhận và độ tin cậy L1','Hậu kiểm trên test; ngưỡng vận hành được chọn riêng trên validation',(1900,930));linechart(d,(30,125,930,890),series,'Accuracy trên mẫu được nhận · test');box(d,(960,125,1870,890),'Phân bố độ tin cậy test: đúng / sai')
for branch,(data,col) in enumerate(zip(pp,colors)):
    x0=1030;ybase=470+branch*270;bins=16;bw=780/bins;ok=[0]*bins;bad=[0]*bins
    for z in data:
        k=min(bins-1,int(float(z['l1_confidence'])*bins));(ok if z['gold_l1']==z['pred_l1'] else bad)[k]+=1
    mx=max(ok+bad+[1]);
    for i in range(bins):
        x=x0+i*bw;w=bw-3;d.rectangle((x,ybase-ok[i]/mx*170,x+w,ybase),fill=col);d.rectangle((x,ybase-170-bad[i]/mx*170,x+w,ybase-170),fill=red)
    d.text((x0,ybase-365),names[branch],font=F(18,True),fill=ink);d.text((x0,ybase+5),'0',font=F(14),fill=muted);d.text((x0+780,ybase+5),'1',font=F(14),fill=muted,anchor='ra')
d.text((1330,875),'Độ tin cậy cao nhất',font=F(16),fill=muted,anchor='ma');im.save(FIG/'04_risk_confidence_test.png')
# 5: pose geometry metrics
pose=js(RUN/'pose_estimator/test_pose_metrics.json'); vals=[pose['test_detection_rate'],pose['mean_bbox_iou'],pose['pck_at_0_05_bbox_diagonal'],pose['mean_oks']]; labs=['Tỷ lệ phát hiện','BBox IoU','PCK@0.05','OKS']
im,d=cv('Chất lượng hình học của bộ ước lượng pose',f"Test: {pose['test_full_keypoint_images']} ảnh đủ 17 điểm; {pose['pck_visible_keypoints']} keypoint có v>0",(1700,780));box(d,(60,125,1640,730),'Chỉ số cùng tập test');left,top,right,bottom=145,240,1555,615
for j in range(6):
    y=bottom-(bottom-top)*j/5;d.line((left,y,right,y),fill=grid);d.text((left-10,y),f'{j/5:.1f}',font=F(15),fill=muted,anchor='rm')
for i,(lab,v) in enumerate(zip(labs,vals)):
    x=left+180+i*340;h=(bottom-top)*v;d.rectangle((x-58,bottom-h,x+58,bottom),fill=[blue,teal,gold,purple][i]);d.text((x,bottom-h-18),f'{v:.1%}',font=F(20,True),fill=ink,anchor='ms');d.text((x,bottom+20),lab,font=F(18),fill=ink,anchor='ma')
im.save(FIG/'05_pose_metrics.png')
# 6: stored ECE/Brier test metrics; validation reliability bins are not serialized in the run.
sumry=js(RUN/'SUMMARY.json'); tests=[sumry['image_test'],sumry['keypoint_test']]
im,d=cv('Hiệu chỉnh xác suất L1 trên test','ECE 10 bins và Brier đa lớp; giá trị nhỏ hơn là tốt hơn',(1800,850))
for ix,(metric,title,maxv) in enumerate([('l1_ece','ECE · 10 bins',.08),('l1_brier','Brier đa lớp',.30)]):
    x0=35+ix*875;box(d,(x0,130,x0+835,800),title);left=x0+110;right=x0+780;top=225;bottom=710
    for j in range(5):
        q=j/4;y=bottom-(bottom-top)*q;d.line((left,y,right,y),fill=grid);d.text((left-8,y),f'{maxv*q:.2f}',font=F(14),fill=muted,anchor='rm')
    for k,(v,c,nm) in enumerate(zip([z[metric] for z in tests],colors,names)):
        x=left+175+k*300;h=(bottom-top)*v/maxv;d.rectangle((x-55,bottom-h,x+55,bottom),fill=c);d.text((x,bottom-h-17),f'{v:.4f}',font=F(17,True),fill=ink,anchor='ms');d.text((x,bottom+15),nm,font=F(16),fill=ink,anchor='ma')
im.save(FIG/'06_calibration_summary.png')
# 7: class supports and F1s
ip=mi['l2_oracle_given_gold_l1']['per_class'];kp=mk['l2_oracle_given_gold_l1']['per_class']; sp={z:Counter(r['level_2_code'] for r in rows if r['split']==z and r['level_2_code']) for z in ['train','val','test']}
im,d=cv('Quy mô mẫu và F1 oracle theo từng lớp L2','F1 tính trên test khi biết trước L1 chuẩn; số mẫu test được ghi cạnh support',(1900,1150));box(d,(20,120,930,1110),'Support theo split');box(d,(965,120,1880,1110),'F1 theo lớp trên test')
d.rectangle((245,162,265,179),fill=blue);d.text((272,171),'Train',font=F(14),fill=ink,anchor='lm');d.rectangle((355,162,375,179),fill='#8aa5c8');d.text((382,171),'Validation',font=F(14),fill=ink,anchor='lm');d.rectangle((500,162,520,179),fill=gold);d.text((527,171),'Test',font=F(14),fill=ink,anchor='lm')
for i,(code,item) in enumerate(zip(c2,l2)):
    y=205+i*78;d.text((40,y+16),code,font=F(16,True),fill=ink,anchor='lm');x=130
    for val,col in zip([sp['train'][code],sp['val'][code],sp['test'][code]],[blue,'#8aa5c8',gold]):
        w=300*val/300;d.rectangle((x,y,x+w,y+27),fill=col);x+=w+8
    d.text((130,y+39),f"train {sp['train'][code]} / val {sp['val'][code]} / test {sp['test'][code]}",font=F(14),fill=muted)
    d.text((995,y+16),code,font=F(16,True),fill=ink,anchor='lm')
    for j,(v,col) in enumerate([(ip[i]['f1'],teal),(kp[i]['f1'],gold)]):
        xx=1080;yy=y+j*25;w=570*float(v);d.rectangle((xx,yy,xx+w,yy+17),fill=col);d.text((xx+w+5,yy+8),f'{float(v):.2f}',font=F(14),fill=ink,anchor='lm')
d.text((1100,1080),'Ảnh trực tiếp',font=F(15),fill=teal);d.text((1280,1080),'Keypoint',font=F(15),fill=gold);im.save(FIG/'07_l2_class_diagnostics.png')
# 8: grouped comparison
keys=[('Accuracy\nL1','l1_accuracy'),('Macro-F1\nL1','l1_macro_f1'),('Macro-F1\nL2 oracle','l2_oracle_macro_f1'),('L2 exact /\ngold L2','l2_exact_over_all')]
im,d=cv('So sánh hai hướng phân loại trên cùng test','Cùng mẫu số; L2 oracle không đồng nhất với dự đoán triển khai',(1800,850));box(d,(50,130,1750,790),'Giá trị các chỉ số');l,r=160,1660;t,b=240,690
for j in range(6):
    q=j/5;y=b-(b-t)*q;d.line((l,y,r,y),fill=grid);d.text((l-10,y),f'{q:.1f}',font=F(15),fill=muted,anchor='rm')
for i,(lab,key) in enumerate(keys):
    cx=l+(r-l)*(i+.5)/len(keys)
    for k,(vals,c) in enumerate(zip(tests,colors)):
        v=vals[key];x=cx-55+k*110;h=(b-t)*v;d.rectangle((x,b-h,x+75,b),fill=c);d.text((x+37,b-h-15),f'{v:.2f}',font=F(15,True),fill=ink,anchor='ms')
    d.multiline_text((cx,b+22),lab,font=F(16),fill=ink,anchor='ma',align='center',spacing=3)
d.rectangle((630,170,654,192),fill=teal);d.text((663,181),'Ảnh trực tiếp',font=F(17),fill=ink,anchor='lm');d.rectangle((850,170,874,192),fill=gold);d.text((883,181),'Keypoint dự đoán',font=F(17),fill=ink,anchor='lm');im.save(FIG/'08_test_comparison.png')
# 9: final decision mix
im,d=cv('Phân bố mức quyết định cuối trên test','Tỷ lệ tính riêng trên 125 ảnh của mỗi nhánh',(1600,730));box(d,(55,135,1545,660),'Đầu ra sau ngưỡng');
for i,(data,nm) in enumerate(zip(pp,names)):
    counts=Counter(x['decision_level'] for x in data);y=280+i*150;x=375;width=1040;d.text((100,y+25),nm,font=F(22,True),fill=ink,anchor='lm')
    for key,col,label in [('l2',teal,'L2'),('l1',gold,'Fallback L1'),('unknown','#b8b8b8','Không xác định')]:
        f=counts[key]/len(data);w=width*f;d.rectangle((x,y,x+w,y+52),fill=col)
        if f>.06:d.text((x+w/2,y+26),f'{f:.1%}',font=F(16,True),fill='white' if key!='unknown' else ink,anchor='mm')
        x+=w
x=400
for col,label in [(teal,'L2 chi tiết'),(gold,'Fallback L1'),('#b8b8b8','Không xác định')]:d.rectangle((x,600,x+20,620),fill=col);d.text((x+27,610),label,font=F(15),fill=ink,anchor='lm');x+=250
im.save(FIG/'09_decision_distribution.png')
# 10: explanatory view of saved demo logic (not a newly executed prediction)
im,d=cv('Các bước hiển thị của demo suy luận','Tái dựng luồng từ predict_posture() và show_prediction(); không phải suy luận mới',(1900,740))
boxes=[(25,'Ảnh crop','Thangka / crop'),(395,'YOLO11n-pose','BBox + 17 keypoint'),(765,'Nhánh ảnh','ResNet-18 × 3\nL1 / L2'),(1135,'Cổng quyết định','Ngưỡng L1, bằng chứng\nvà ngưỡng riêng L2'),(1505,'Kết quả demo','Nhãn, fallback hoặc từ chối\n+ biểu đồ confidence')]
for i,(x,title,sub) in enumerate(boxes):
    color=['#eaf2f8','#e9f3f0','#eef2f8','#fbf1e4','#f2edf6'][i];d.rounded_rectangle((x,200,x+330,445),16,fill=color,outline=[blue,teal,blue,gold,purple][i],width=3);d.text((x+165,255),title,font=F(23,True),fill=ink,anchor='mm');d.multiline_text((x+165,340),sub,font=F(19),fill=ink,anchor='mm',align='center',spacing=8)
    if i<4:d.line((x+340,322,x+362,322),fill=muted,width=4);d.polygon([(x+362,322),(x+349,313),(x+349,331)],fill=muted)
d.rounded_rectangle((300,535,1600,690),12,fill='#fff9f0',outline='#ead7b9',width=2);d.multiline_text((950,610),'Cấu hình triển khai đã chọn image_weight = 1,0. Pose hỗ trợ phần trực quan và được giữ làm nhánh đối chứng; kết quả phân loại triển khai hiện hành do nhánh ảnh quyết định.',font=F(20),fill=ink,anchor='mm',align='center',spacing=8);im.save(FIG/'10_demo_pipeline.png')
# 11: actual pose-evaluation label/prediction output saved by the notebook run.
src=RUN/'pose_estimator/geometry_test'; panelw=880; panelh=440
im=Image.new('RGB',(1850,560),'white'); d=ImageDraw.Draw(im); d.text((925,24),'Ví dụ trực quan từ đầu ra đánh giá pose đã lưu',font=F(30,True),fill=ink,anchor='ma')
for x,name,label in [(25,'val_batch2_labels.jpg','Nhãn keypoint tham chiếu'),(945,'val_batch2_pred.jpg','Dự đoán YOLO11n-pose')]:
    d.rounded_rectangle((x,75,x+880,535),12,fill='#fbfcfd',outline=grid,width=2);d.text((x+440,93),label,font=F(21,True),fill=ink,anchor='ma')
    pic=Image.open(src/name).convert('RGB').resize((panelw,panelh),Image.Resampling.LANCZOS);im.paste(pic,(x,130))
im.save(FIG/'11_pose_overlay_example.png')
print('Created',len(list(FIG.glob('*.png'))),'illustration files')
