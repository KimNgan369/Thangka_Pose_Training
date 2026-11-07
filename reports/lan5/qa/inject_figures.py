from pathlib import Path
f=Path('reports/lan5/qa/build_report.py')
s=f.read_text(encoding='utf-8')
def before(marker,addition):
    global s
    if s.count(marker)!=1: raise RuntimeError((marker,s.count(marker)))
    s=s.replace(marker,addition+marker,1)
before("h('4. GÁN NHÃN", """image(QA/'figures/01_data_distribution.png','Phân bố nhãn L1, L2 và quy mô các tập dữ liệu',
      'Biểu đồ cho thấy C1.1 chiếm tỷ trọng lớn nhất, trong khi nhiều nhãn L2 có rất ít mẫu. Train, validation và test lần lượt có 612, 136 và 125 ảnh. Vì vậy cần đọc điểm theo từng lớp cùng support; tổng số ảnh và kiểm toán trùng lặp không thay thế việc xem xét độ mất cân bằng.')
""")
before("h('5. QUY TRÌNH", """image(QA/'figures/02_interrater_matrix.png','Ma trận đối chiếu nhãn của hai người gán nhãn',
      'Các ô tập trung trên đường chéo, phù hợp với tỷ lệ trùng nhãn cụ thể 847/873 (97,02%) và Cohen’s κ = 0,9652. Sau khi quy L2 về lớp cha L1, hai phiếu thống nhất hoàn toàn. Kappa đo độ nhất quán giữa hai phiếu đã lưu, không tự xác nhận tính đúng tuyệt đối của nhãn.')
""")
before("h('6. NGUỒN GỐC", """image(QA/'figures/10_demo_pipeline.png','Luồng xử lý và thông tin được hiển thị trong demo',
      'Sơ đồ phản ánh các bước của hàm demo đã lưu. Cấu hình triển khai chọn image_weight = 1,0 nên nhãn cuối lấy từ nhánh ảnh; pose được tính để hỗ trợ phần trực quan và đối chiếu. Đây là sơ đồ quy trình, không phải kết quả suy luận mới trên một ảnh cụ thể.')
""")
before("sub('7.4. Định nghĩa", """image(QA/'figures/06_calibration_summary.png','So sánh ECE và Brier L1 trên test',
      'Nhánh ảnh có ECE 0,0350 và Brier 0,1548; nhánh keypoint lần lượt là 0,0502 và 0,2227. Các giá trị được tính từ kết quả test đã lưu. Temperature scaling và lựa chọn ngưỡng được thực hiện trên validation; test không được dùng để chọn các tham số này.')
""")
before("sub('8.3. Kết quả", """image(QA/'figures/03_confusion_matrices.png','Ma trận nhầm lẫn L1 end-to-end và L2 oracle của hai hướng',
      'Đường chéo thể hiện dự đoán đúng; các điểm ngoài đường chéo chỉ ra những lớp bị nhầm lẫn. L1 end-to-end phản ánh phân loại tổng quát trên test. Hai ma trận L2 là oracle: chúng giả định L1 chuẩn đã biết, nên dùng để phân tích riêng bộ phân biệt L2 chứ không diễn giải như hiệu năng L2 triển khai.')
image(QA/'figures/04_risk_confidence_test.png','Độ chính xác theo coverage và phân bố độ tin cậy L1',
      'Đường cong được dựng từ độ tin cậy và nhãn dự đoán đã lưu cho 125 ảnh test để mô tả quan hệ giữa tỷ lệ được nhận và độ chính xác có điều kiện. Đây là hình hậu kiểm mô tả, không dùng để chọn ngưỡng; ngưỡng vận hành đã được chọn trên validation. Các cột đỏ tập trung ở độ tin cậy thấp hơn sẽ là vùng cần tiếp tục rà soát.')
image(QA/'figures/08_test_comparison.png','So sánh các chỉ số L1 và L2 oracle trên cùng tập test',
      'Nhánh ảnh đạt accuracy L1 0,9040 và macro-F1 L1 0,8546, cao hơn nhánh keypoint tương ứng 0,8560 và 0,8091. Macro-F1 L2 oracle gần nhau (0,6749 và 0,6690); các giá trị này không biểu thị coverage L2 thực tế. Khác biệt cần được đọc cùng mẫu số và cơ chế từ chối ở các bảng kết quả.')
image_decisions=collections.Counter(r['decision_level'] for r in pred); keypoint_decisions=collections.Counter(r['decision_level'] for r in kp)
image_comment=(f"Nhánh ảnh trả {image_decisions['l2']} nhãn L2, {image_decisions['l1']} fallback L1 và {image_decisions['unknown']} trường hợp không xác định trên {len(pred)} ảnh. "
               f"Nhánh keypoint trả {keypoint_decisions['l2']} nhãn L2, {keypoint_decisions['l1']} fallback L1 và {keypoint_decisions['unknown']} trường hợp không xác định trên {len(kp)} ảnh. "
               'Tỷ lệ L2 thấp thể hiện chính sách chỉ trả nhãn chi tiết khi đạt điều kiện; không nên diễn giải coverage thấp như thiếu dữ liệu trong hình.')
image(QA/'figures/09_decision_distribution.png','Tỷ lệ các mức quyết định cuối trên test',image_comment)
""")
before("p('Chênh lệch accuracy L1", """image(QA/'figures/05_pose_metrics.png','Các chỉ số hình học của pose estimator trên tập test',
      'Trên 82 ảnh test đủ 17 keypoint, tỷ lệ phát hiện là 100%, IoU bbox trung bình 0,8539, PCK@0.05 là 0,7862 và OKS là 0,8853. Phạm vi này là đánh giá trên ảnh crop theo metric schema 2; không đại diện cho phát hiện nhân vật từ toàn bộ tranh và không so trực tiếp với số lần 4 dùng công thức khác.')
""")
before("sub('9.2. Ngưỡng", """image(QA/'figures/07_l2_class_diagnostics.png','Support theo split và F1 L2 oracle theo từng lớp',
      'Biểu đồ đặt số mẫu train/validation/test cạnh F1 test để tránh đọc điểm lớp hiếm tách rời mẫu số. Một số lớp có support test rất nhỏ nên F1 biến động mạnh; các thanh bằng 0 cũng không đồng nghĩa lớp đã được đánh giá trên quy mô đủ lớn. Kết quả L2 tiếp tục là oracle theo L1 chuẩn.')
""")
f.write_text(s,encoding='utf-8')
print('Injected figure placements into',f)
