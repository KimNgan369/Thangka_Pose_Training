# Rà soát 35 trường hợp demo validation (29/10/2026)

Đã đọc 35 ảnh chụp `Screenshot (3437).png`–`Screenshot (3471).png` trong `..\demo chưa ổn`, đối chiếu với `data/classification_manifest.csv` và cả 35 ảnh gốc ở `data/images`. Các ảnh chụp hiển thị crop demo nhưng chỉ một phần hình trong viewport; sáu crop khó/đáng ngờ cũng được mở trực tiếp từ `data/crops`. Nhận xét về tư thế dựa trên ảnh gốc và crop khi cần, không dựa riêng vào phần trên của screenshot. Đây là 35 trường hợp do người dùng chọn là chưa ổn, **không phải mẫu ngẫu nhiên để tính tỉ lệ lỗi toàn validation**. Không thay nhãn đã duyệt chỉ từ dự đoán của mô hình.

| Screenshot | Ảnh gốc | Nhãn tham chiếu | Demo hiển thị | Nhận xét sau khi xem ảnh gốc |
|---:|---|---|---|---|
| 3437 | `199.png` | C2.4 — ngồi hai chân thả | Không xác định, L1 45% | Nhân vật chính ngồi, chân hướng xuống; từ chối L1 quá thận trọng ở ca này. |
| 3438 | `623.png` | C1.3 — chuyển động | Không xác định, L1 40% | Người cưỡi ngựa, chi dưới bị ngựa/trang phục che; cần thống nhất quy tắc L1 cho cưỡi thú. |
| 3439 | `HAR_318.jpg` | C2.7 — đứng lệch trọng tâm | Chuyển động 51% | Nhân vật chính bên dưới tranh có hai chân trụ không đối xứng; nhầm đứng/chuyển động. |
| 3440 | `HAR_36411.jpg` | C2.5 — quỳ/ngồi trên gót | Không xác định, L1 40% | Tư thế ngồi/quỳ trên thú tương đối rõ ở ảnh gốc; crop vẫn chứa chân. |
| 3441 | `HAR_65925.jpg` | C2.7 — đứng lệch trọng tâm | Chuyển động 51% | Nhân vật trung tâm trụ hai chân, dang rộng; nhầm đứng/chuyển động. |
| 3442 | `HAR_81655.jpg` | C2.5 — quỳ/ngồi trên gót | Không xác định, L1 50% | Nhân vật quỳ/ngồi gót trên đài; từ chối sát ngưỡng. |
| 3443 | `HAR_3314476_FULL.jpg` | C2.8 — một chân trụ, chân kia co/nâng | Đứng 55% | Đúng L1, thiếu chứng cứ để trả L2; chân trụ/chân nâng nhìn được trong ảnh gốc. |
| 3444 | `HAR_52548506.jpg` | C2.8 — một chân trụ, chân kia co/nâng | Đứng 68% | Đúng L1, thiếu L2; nhân vật nhảy, chân nâng rõ. |
| 3445 | `HAR_53552942.jpg` | C2.5 — quỳ/ngồi trên gót | Không xác định, L1 35% | Nhân vật ngồi/quỳ trên đài; keypoint chân dễ lẫn trang phục. |
| 3446 | `THK000011.png` | C1.3 — chuyển động | Ngồi 82% | Người cưỡi ngựa; L1 trong dữ liệu không nhất quán với `THK000025` (cùng cưỡi thú nhưng gán ngồi). |
| 3447 | `THK000025.png` | C1.1 — ngồi | Chuyển động 55% | Cưỡi linh thú, phần chân che; cần cùng quy tắc với các ảnh cưỡi ngựa. |
| 3448 | `THK000082.png` | C1.3 — chuyển động | Không xác định, L1 51% | Cưỡi ngựa, chân bị che; không đủ cơ sở chỉ bằng hình học chân để khẳng định nhãn chi tiết. |
| 3449 | `THK000087.jpg` | C1.3 — chuyển động | Ngồi 87% | Nhân vật chính cưỡi ngựa, dáng thân ngồi; cảnh chuyển động nhưng tư thế người là cưỡi/ngồi. Rà soát quy tắc. |
| 3450 | `THK000089.png` | C1.3 — chuyển động | Không xác định, L1 46% | Cưỡi ngựa phi; ghi chú manifest trước đây từng đề xuất C1.1, sau đổi thành C1.3 theo cảnh ngựa phi. Đây là ca quy tắc khó. |
| 3451 | `THK000104.jpg` | C1.3 — chuyển động | Không xác định, L1 47% | Nhân vật trên thú, chân khó tách khỏi thú; cần xác định nhãn theo **tư thế người**, không lấy chuyển động của thú làm chứng cứ duy nhất. |
| 3452 | `THK000129_55a45b8092_3.jpg` | C2.6 — đứng thẳng hai chân trụ | Không xác định, L1 45% | Nhân vật trung tâm đứng rõ; ảnh gốc có nhiều tiểu tượng, crop cần giữ đúng nhân vật đích. |
| 3453 | `THK000152.png` | C2.10 — động/múa | Đứng 75% | Sau khi xem toàn thân/crop, một chân trụ và một chân nâng ngang; nhãn động/múa có cơ sở, không nên tự sửa sang ngồi. |
| 3454 | `THK000163.png` | C2.10 — động/múa | C2.6 — đứng thẳng hai chân trụ, 75% | Cùng bố cục với `THK000152`; chân nâng ngang rõ nhưng mô hình trả L2 sai, bằng chứng L2 99% — lỗi nghiêm trọng. |
| 3455 | `THK000182.jpg` | C2.6 — đứng thẳng hai chân trụ | Ngồi 73% | Nhân vật trung tâm đứng đạp lên người khác; tay/trang phục dễ gây nhầm khớp hông-chân. |
| 3456 | `THK000191.jpg` | C2.9 — bước/chuyển hướng | Không xác định, L1 50% | Nhân vật chính đi/bước, chân dưới áo và mây bị che một phần. |
| 3457 | `THK000196.png` | C2.9 — bước/chuyển hướng | Không xác định, L1 44% | Dáng bước rõ hơn ở ảnh gốc; keypoint chân trên tranh phẫn nộ khó. |
| 3458 | `THK000284.jpg` | C2.9 — bước/chuyển hướng | Chuyển động 53% | Đúng L1, chưa trả L2; tư thế bước chân rộng. |
| 3459 | `THK000312.png` | C2.5 — quỳ/ngồi trên gót | Không xác định, L1 40% | Nhân vật quỳ cầu nguyện ở tiền cảnh; crop mục tiêu cần tách khỏi các tượng ngồi phía trên. |
| 3460 | `THK000316.jpg` | C2.7 — đứng lệch trọng tâm | Ngồi 99% | Nhân vật khuỵu/squat, hai bàn chân đặt trên người nằm; nhãn C2.7 đáng **tái duyệt** vì ảnh không giống đứng lệch trọng tâm điển hình. Không tự đổi nhãn. |
| 3461 | `THK000370_8af4c83812_2.jpg` | C2.2 — ngồi bắt chéo không khóa kín | Ngồi 75% | Đúng L1, C2.2 bị chặn bởi ngưỡng 1.0001; đây là lớp hiếm, fallback hợp lệ nhưng chưa đáp ứng mục tiêu nhãn chi tiết. |
| 3462 | `THK000581.jpg` | C1.1 — ngồi, L2 để trống | C2.3 — ngồi một chân co một chân thả, 71% | Sai do trả L2 quá cụ thể khi chân bị áo che; bộ phân loại “đủ bằng chứng L2” cho 94%, cần kiểm tra lại. |
| 3463 | `THK000623.jpg` | C1.1 — ngồi, L2 để trống | C2.3 — ngồi một chân co một chân thả, 71% | Sai quá cụ thể; hai chân bị áo che, bằng chứng L2 91% không tương xứng hình ảnh. |
| 3464 | `THK000877.jpg` | C2.7 — đứng lệch trọng tâm | Không xác định, L1 51% | Nhiều thân/đầu chồng nhau, thú bên dưới; pose estimator có thể trộn chi của các nhân vật. Rà soát crop và keypoint. |
| 3465 | `THK000967.jpg` | C2.3 — ngồi một chân co một chân thả | C2.1 — ngồi bắt chéo khóa kín, 90% | Chân thả nhìn được ở ảnh gốc/crop; dự đoán L2 sai nhưng rất tự tin. |
| 3466 | `THK001017.png` | C2.4 — ngồi hai chân thả | Không xác định, L1 49% | Ngồi trên ghế, ít nhất một bàn chân rõ; từ chối sát ngưỡng. |
| 3467 | `THK001049.png` | C2.10 — động/múa | Đứng 54% | Chân trụ/chân nâng và tay dang trong dáng múa; nhầm L1. |
| 3468 | `THK001069.png` | C2.5 — quỳ/ngồi trên gót | Chuyển động 75% | Nhân vật rõ ràng đang ngồi; chân dưới áo khó xác nhận quỳ trên gót, nên tái duyệt L2 nhưng L1 sai là chắc. |
| 3469 | `WC_15634388.jpg` | C2.2 — ngồi bắt chéo không khóa kín | Ngồi 61% | Đúng L1, C2.2 không thể phát ra vì ngưỡng riêng 1.0001. |
| 3470 | `WC_126127897.jpg` | C2.4 — ngồi hai chân thả | Đứng 58% | Nhân vật ngồi trên ghế, L1 sai; chi dưới bị áo che, nhãn L2 cần xem chứng cứ theo quy tắc đề tài. Ghi chú cũ trong manifest còn nói “chưa human review” dù trường trạng thái hiện là approved. |
| 3471 | `WKM_50795012.jpg` | C2.11 — nằm nghiêng | Không xác định dù L1 cao nhất 85% | Nhân vật nằm rất rõ, nhưng pose estimator không bắt được cơ thể nằm; mô hình ảnh cần là nguồn dự phòng khi pose thất bại. |

## Kết luận chẩn đoán

Trong 35 ca được chọn: 15 lần trả “Không xác định”, 12 lần sai L1 dù có kết quả, 3 lần trả L2 sai/quá cụ thể và 5 lần L1 đúng nhưng chưa trả được L2 tham chiếu. Những con số này **không** là tỉ lệ lỗi toàn bộ validation. Ảnh chụp là kết quả trên `val`, không phải `test`.

Checkpoint gần nhất ở `outputs/notebook_runs/20261029_223959_seed20261021` cho thấy trên **test 125 ảnh**: nhánh ảnh L1 accuracy 0,872 / macro-F1 0,815; nhánh keypoint L1 accuracy 0,864 / macro-F1 0,799. Nhánh keypoint trả L2 trên 55,3% số ảnh có gold L2, đạt selective accuracy 87,7%, nhưng exact L2 trên **toàn bộ** ảnh có gold L2 chỉ 48,5%. Nhánh ảnh hiện không phát ra L2 vì ngưỡng được chọn là 1,0001. Ngưỡng C2.2 cũng là 1,0001, nghĩa là **không có dự đoán C2.2 cuối cùng**. Evidence classifier keypoint chỉ nhận đúng 5/22 ảnh test để trống L2; vì thế các ca `THK000581` và `THK000623` bị trả nhãn chi tiết quá tự tin không phải cá biệt đơn thuần.

Độ tin cậy trên bbox “Pose 90%” là độ tin cậy phát hiện đối tượng, không phải độ đúng của từng keypoint hay xác suất nhãn tư thế. Trong notebook, pose estimator tạo 53 đặc trưng gốc (17 × x/y/confidence + box confidence + detected), rồi classifier bổ sung hình học; box có confidence cao nhất được chọn. Tư thế chân che khuất, nhân vật trên thú, nhiều người chồng nhau và nằm ngang là các nhóm dễ gây keypoint sai. Demo hiện chỉ dùng nhánh keypoint dù nhánh ảnh L1 đang tốt hơn trên test.

## Quy trình cải thiện đề xuất (theo thứ tự, không dùng test để chỉnh)

1. **Chốt quy tắc nhãn trước khi train.** Hai người gán nhãn Ngân/My cùng xem lại nhóm cưỡi thú (`THK000011`, `THK000025`, `THK000082`, `THK000087`, `THK000089`, `623`) và xác định L1 theo tư thế **của người** chứ không theo chuyển động của ngựa. Tái duyệt `THK000316`, `THK001069`, `WC_126127897`; nếu chân không đủ rõ, chỉ giữ L1, không ép L2. Ghi quyết định và lý do vào manifest; kiểm tra các mẫu train cùng kiểu để sửa nhất quán. Không biến 35 ca val này thành train một cách âm thầm.
2. **Kiểm toán hình học đầu vào.** Với từng ảnh lỗi, hiển thị crop, bbox người, confidence của hông/gối/cổ chân, so với keypoint do Ngân/My đã duyệt. Đo PCK/OKS riêng theo lớp, mức che khuất và orientation. Chỉ huấn luyện lại pose estimator nếu phép đo chứng minh nó là nút thắt; không lấy confidence bbox làm chỉ báo keypoint tốt. Kiểm tra chọn đúng nhân vật trong ảnh nhiều người. Trường hợp không phát hiện pose nên còn đường dự phòng từ ảnh RGB cho L1.
3. **Huấn luyện nhánh ảnh mạnh hơn bằng thí nghiệm có đối chứng.** Giữ baseline 224 px/ResNet18; so sánh 320–384 px, fine-tune thêm `layer3`/`layer4` sau giai đoạn head-only, 40–80 epoch với early stopping và learning-rate decay. Tăng cường train có giới hạn, không làm biến dạng ý nghĩa chân; tuyệt đối không augment val/test. Thử crop toàn thân và crop nhấn vùng hông–chân như hai view của **cùng nhân vật**, không dùng toàn ảnh nhiều người thay cho crop mục tiêu. Chọn theo macro-F1 L1, per-class recall, L2 exact-over-all và calibration, không chỉ accuracy hoặc selective accuracy.
4. **So sánh nhánh ảnh, keypoint và kết hợp muộn.** Trên validation, thử trộn xác suất L1 của hai nhánh; L2 vẫn theo nhánh có kết quả validation tốt hơn. Khi pose không phát hiện, chỉ nhánh ảnh được phép cứu L1; không tự trả L2 khi thiếu chứng cứ chân. Chọn trọng số và ngưỡng trên validation hoặc cross-validation theo nhóm, khóa cấu hình rồi mới xem test. Một phương án không vượt baseline trên các mục tiêu định trước thì không triển khai demo.
5. **Giảm L2 sai quá tự tin.** Huấn luyện/hiệu chuẩn lại bộ “đủ bằng chứng L2” và báo cáo riêng recall trên ảnh L2 trống; thêm tín hiệu chất lượng của hông–gối–cổ chân và mức che khuất. Với C2.2, kiểm tra nhầm C2.1/C2.3 bằng per-class confusion và dữ liệu thật; không giải quyết bằng oversampling quá mức hoặc hạ ngưỡng chỉ để có dự đoán C2.2. Nếu vẫn không đạt precision tối thiểu trên validation nhiều fold, fallback L1 là đúng với đề tài.
6. **Đánh giá chống tự đánh lừa.** Vì 35 ảnh này và cả test cũ đã được xem nhiều lần, dùng cross-validation phân tầng theo artifact trên tập phát triển để chọn phương án; test cũ chỉ là so sánh lịch sử. Muốn kết luận độc lập cuối cùng cần một bộ ảnh mới/chưa dùng để chỉnh mô hình. Báo cáo số mẫu từng lớp, khoảng tin cậy, coverage, unknown rate và lỗi điển hình. Một lớp 4 ảnh test không thể chứng minh chất lượng ổn định.

Đầu ra vẫn là **một nhãn tư thế cụ thể nhất đủ tin cậy kèm phần trăm**, fallback L1/“Không xác định” theo thứ bậc. BBox, keypoint, khung xương chỉ hỗ trợ; không thêm mục tiêu nhận diện nhân vật hay diễn giải nội dung tôn giáo.

**Trạng thái:** Đây là chẩn đoán và thiết kế thí nghiệm, **chưa phải mô hình đã được huấn luyện lại hoặc chứng minh cải thiện**. Môi trường dòng lệnh hiện không có Python 3.10 khả dụng (launcher trỏ tới file không tồn tại), nên chưa thể chạy thí nghiệm/kiểm chứng mới trực tiếp từ file. Không chỉnh nhãn hay checkpoint khi chưa có quyết định tái duyệt.
