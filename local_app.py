"""Local Gradio demo and test error browser for a completed notebook run."""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path

import gradio as gr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


ROOT = Path(__file__).resolve().parent
SOURCE_NOTEBOOK = ROOT / "Thangka_Pose_Training.ipynb"
RUNS = ROOT / "outputs" / "notebook_runs"
FUNCTIONS = {
    "get_code_cell", "_load_json", "_latest_completed_run", "load_saved_demo_globals",
    "format_prediction_vi", "prediction_reason_vi", "predict_posture", "draw_demo_pose",
}
DEMO_EDGES = [
    (0, 1), (0, 2), (1, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]


def completed_runs():
    results = []
    if not RUNS.exists():
        return results
    for folder in RUNS.iterdir():
        summary = folder / "SUMMARY.json"
        selection = folder / "deployment" / "selection.json"
        source = folder / "source_notebook.ipynb"
        if not (summary.is_file() and selection.is_file() and source.is_file()):
            continue
        try:
            metadata = json.loads(summary.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if metadata.get("run_mode") == "full" and metadata.get("run_id") == folder.name:
            results.append(folder.name)
    return sorted(results, reverse=True)


def load_runtime(run_id):
    """Load only inference definitions from the notebook, never training cells."""
    notebook = json.loads(SOURCE_NOTEBOOK.read_text(encoding="utf-8"))
    source = "".join(notebook["cells"][53]["source"])
    tree = ast.parse(source, filename=str(SOURCE_NOTEBOOK))
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS]
    missing = FUNCTIONS - {n.name for n in definitions}
    if missing:
        raise RuntimeError(f"Thiếu hàm demo trong notebook: {', '.join(sorted(missing))}")
    namespace = {
        "__builtins__": __builtins__, "ast": ast, "csv": csv, "json": json,
        "hashlib": __import__("hashlib"), "Path": Path, "np": np, "torch": torch,
        "plt": plt, "_saved_demo_root": ROOT, "CELL_KEY": "thangka_original_cell_index",
        "DEMO_SKELETON_EDGES": DEMO_EDGES,
    }
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(SOURCE_NOTEBOOK), "exec"), namespace)
    namespace.update(namespace["load_saved_demo_globals"](ROOT, run_id=run_id))
    # Use the pose checkpoint trained in this same run for the visual overlay.
    pose_checkpoint = RUNS / run_id / "pose_estimator" / "yolo11n_pose_formal" / "weights" / "best.pt"
    if pose_checkpoint.is_file():
        from ultralytics import YOLO

        namespace["pose_model"] = YOLO(str(pose_checkpoint))
    return namespace


def error_category(record):
    if not record["gold_l2"]:
        return "L2 trống, vẫn trả nhãn chi tiết" if record["decision_level"] == "l2" else "L2 trống, giữ nhãn tổng quát"
    if record["pred_l1"] != record["gold_l1"]:
        return "Sai L1"
    if record["l2_candidate"] != record["gold_l2"]:
        return "Sai ứng viên L2"
    if record["decision_level"] != "l2":
        return "Thiếu bằng chứng L2" if record["l2_evidence_ok"] == "False" else "Không qua ngưỡng L2"
    return "Đúng L2"


def read_test_records(run_id):
    path = RUNS / run_id / "deployment" / "test_predictions.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    for row in records:
        row["error_category"] = error_category(row)
    return records


def test_summary(records):
    labeled = [r for r in records if r["gold_l2"]]
    counts = Counter(r["error_category"] for r in labeled)
    blanks = [r for r in records if not r["gold_l2"]]
    l1_ok = sum(r["pred_l1"] == r["gold_l1"] for r in records)
    lines = [
        f"**Test đã lưu:** {len(records)} ảnh; L1 đúng **{l1_ok}/{len(records)}**. "
        f"Có **{len(labeled)}** ảnh có nhãn L2 và **{len(blanks)}** ảnh để trống L2.",
        f"**L2 đúng ở quyết định cuối:** {counts['Đúng L2']}/{len(labeled)}. "
        f"Sai L1: {counts['Sai L1']}; sai ứng viên L2: {counts['Sai ứng viên L2']}; "
        f"không qua ngưỡng: {counts['Không qua ngưỡng L2']}; "
        f"thiếu bằng chứng: {counts['Thiếu bằng chứng L2']}.",
        f"**L2 trống nhưng vẫn trả nhãn chi tiết:** "
        f"{sum(r['decision_level'] == 'l2' for r in blanks)}/{len(blanks)}.",
        "Các nhóm trên mô tả **đường quyết định của mô hình**, chưa chứng minh nguyên nhân thị giác "
        "như che khuất hoặc bệ đỡ. Hãy mở từng ảnh để kiểm tra các giả thuyết đó.",
    ]
    return "\n\n".join(lines)


def per_class_table(records):
    codes = [f"C2.{i}" for i in range(1, 12)]
    result = []
    for code in codes:
        gold = [r for r in records if r["gold_l2"] == code]
        correct = sum(r["final_code"] == code for r in gold)
        result.append([code, len(gold), correct, len(gold) - correct, f"{100 * correct / len(gold):.1f}%" if gold else "—"])
    return result


def overlay_image(runtime, pose_result):
    fig, ax = plt.subplots(figsize=(10, 9), dpi=110)
    try:
        runtime["draw_demo_pose"](ax, pose_result)
        ax.axis("off")
        fig.tight_layout(pad=0)
        fig.canvas.draw()
        image = np.asarray(fig.canvas.buffer_rgba()).copy()[..., :3]
    finally:
        plt.close(fig)
    return image


def decision_details(runtime, result, reference=None):
    pred = result["prediction"]
    l1 = pred["l1_candidate"]
    child = pred["l2_candidate"]
    threshold = runtime["deployment_class_thresholds"].get(child, 1.0001)
    l1_name = runtime["l1_names_vi"].get(l1, l1)
    child_name = runtime["l2_names_vi"].get(child, child)
    lines = [
        f"### {result['display_text']}",
        f"**Quyết định:** {pred['decision_level'].upper()} · "
        f"**Ứng viên L1:** {l1_name} ({pred['l1_confidence']:.1%}) · "
        f"**Ứng viên L2:** {child_name} ({pred['l2_confidence']:.1%})",
        f"**Bằng chứng L2:** {pred['l2_evidence_confidence']:.1%} "
        f"(ngưỡng {runtime['deployment_evidence_threshold']:.1%}) · "
        f"**Ngưỡng riêng {child}:** {threshold:.1%}" if threshold <= 1 else
        f"**Bằng chứng L2:** {pred['l2_evidence_confidence']:.1%} · "
        f"**{child} chưa được phép trả ở cấu hình này** (ngưỡng {threshold:.4f}).",
        f"**Vì sao trả mức này:** {result['reason_text']}",
        f"**Pose:** {'phát hiện được nhân vật' if result['pose_detected'] else 'không phát hiện được nhân vật'}. "
        "Khung và điểm xương chỉ để minh họa; khi ảnh có nhiều nhân vật, hệ thống lấy một nhân vật có điểm phát hiện cao nhất.",
    ]
    if reference:
        category = error_category(reference)
        gold_l1 = runtime["l1_names_vi"].get(reference["gold_l1"], reference["gold_l1"])
        gold_l2 = runtime["l2_names_vi"].get(reference["gold_l2"], "Chưa gán L2")
        lines.append(f"**Nhãn tham chiếu:** {gold_l1} → {gold_l2} · **Nhóm lỗi trong test đã lưu:** {category}.")
        lines.append("Kết quả chạy lại có thể khác bảng đã lưu nếu dùng ảnh gốc thay vì crop, hoặc môi trường suy luận thay đổi.")
    return "\n\n".join(lines)


def probability_rows(runtime, result):
    pred = result["prediction"]
    parent = pred["l1_candidate"]
    rows = [["L1", code, runtime["l1_names_vi"].get(code, code), f"{value:.1%}"]
            for code, value in zip(runtime["indices"]["l1_codes"], result["l1_probabilities"])]
    child_codes = [c for c in runtime["indices"]["l2_codes"] if runtime["indices"]["l2_parent"][c] == parent]
    child_indices = [runtime["indices"]["l2_to_idx"][c] for c in child_codes]
    conditional = torch.softmax(torch.as_tensor(result["l2_logits"][child_indices]), dim=0).numpy()
    rows.extend(["L2 trong nhánh L1", code, runtime["l2_names_vi"].get(code, code),
                 f"{pred['l1_confidence'] * value:.1%}"] for code, value in zip(child_codes, conditional))
    return rows


def build_app(run_id):
    runtime = load_runtime(run_id)
    records = read_test_records(run_id)
    by_id = {r["instance_id"]: r for r in records}
    manifest = {r["instance_id"]: r for r in runtime["rows"] if r["split"] == "test"}
    choices = [(f"{r['instance_id']} · {r['gold_l2'] or 'L2 trống'} · {r['error_category']}", r["instance_id"])
               for r in records]

    def infer(image_path, sample_id):
        if sample_id:
            row = manifest.get(sample_id)
            if row is None:
                raise gr.Error("Ảnh test không có trong manifest hiện tại.")
            image_path = str(runtime["DATA_DIR"] / row["crop_path"])
        elif not image_path:
            raise gr.Error("Hãy tải ảnh lên hoặc chọn một ảnh test.")
        try:
            with torch.inference_mode():
                result = runtime["predict_posture"](image_path)
            picture = overlay_image(runtime, result["pose_result"])
            return picture, decision_details(runtime, result, by_id.get(sample_id)), probability_rows(runtime, result)
        except Exception as exc:
            raise gr.Error(f"Không chạy được ảnh: {type(exc).__name__}: {exc}") from exc

    def filter_records(category, code):
        selected = [r for r in records if (category == "Tất cả" or r["error_category"] == category)
                    and (code == "Tất cả" or r["gold_l2"] == code)]
        return [[r["instance_id"], r["gold_l1"], r["gold_l2"] or "—", r["l2_candidate"] or "—",
                 r["final_code"], r["error_category"]] for r in selected]

    with gr.Blocks(title="Phân tích tư thế Thangka") as app:
        gr.Markdown("# Phân tích tư thế nhân vật Phật giáo")
        gr.Markdown(f"**Run:** `{run_id}` · Mô hình và ngưỡng đã khóa từ lần huấn luyện hoàn tất. "
                    "Giao diện chạy trên máy này; ảnh tải lên được xử lý tại local.")
        with gr.Tab("Thử ảnh"):
            gr.Markdown("Tải ảnh một nhân vật hoặc chọn ảnh trong tập test. Ảnh test được chạy trên **crop mục tiêu** đã dùng khi đánh giá.")
            with gr.Row():
                upload = gr.Image(type="filepath", label="Ảnh từ máy", sources=["upload"])
                sample = gr.Dropdown(choices=choices, label="Ảnh test đã gán nhãn", value=None, filterable=True)
            run_button = gr.Button("Phân tích ảnh", variant="primary")
            with gr.Row():
                overlay = gr.Image(label="Ảnh, bounding box và keypoint", interactive=False)
                details = gr.Markdown()
            probabilities = gr.Dataframe(headers=["Mức", "Mã", "Nhãn", "Độ tin cậy"],
                                         datatype=["str"] * 4, interactive=False, label="Xác suất dự đoán")
            run_button.click(infer, inputs=[upload, sample], outputs=[overlay, details, probabilities], concurrency_limit=1)
        with gr.Tab("Phân tích lỗi L2 trên test"):
            gr.Markdown(test_summary(records))
            gr.Dataframe(value=per_class_table(records), headers=["Lớp", "Số ảnh", "Đúng cuối", "Chưa đúng", "Tỷ lệ"],
                         datatype=["str", "number", "number", "number", "str"], interactive=False,
                         label="Kết quả L2 theo lớp")
            with gr.Row():
                category = gr.Dropdown(["Tất cả", "Đúng L2", "Sai L1", "Sai ứng viên L2", "Không qua ngưỡng L2",
                                        "Thiếu bằng chứng L2", "L2 trống, vẫn trả nhãn chi tiết", "L2 trống, giữ nhãn tổng quát"],
                                       value="Tất cả", label="Nhóm kết quả")
                code = gr.Dropdown(["Tất cả"] + [f"C2.{i}" for i in range(1, 12)] + [""],
                                   value="Tất cả", label="Nhãn L2 chuẩn (để trống = chưa gán)")
            table = gr.Dataframe(value=filter_records("Tất cả", "Tất cả"),
                                 headers=["Ảnh", "L1 chuẩn", "L2 chuẩn", "Ứng viên L2", "Kết quả cuối", "Nhóm lỗi"],
                                 datatype=["str"] * 6, interactive=False, label="Từng ảnh test")
            category.change(filter_records, inputs=[category, code], outputs=table)
            code.change(filter_records, inputs=[category, code], outputs=table)
            gr.Markdown("Để xem ảnh và dự đoán lại, chọn mã ảnh tương ứng ở tab **Thử ảnh**. "
                        "Khi phân tích nguyên nhân thị giác, kiểm tra chân bị che, bệ đỡ, nhiều tay/chân và độ rõ của khớp.")
    return app


def main():
    parser = argparse.ArgumentParser(description="Giao diện local phân tích tư thế Thangka")
    parser.add_argument("--run-id", help="Mã run hoàn tất; mặc định dùng run mới nhất")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    available = completed_runs()
    if not available:
        parser.error("Chưa có run hoàn tất trong outputs/notebook_runs")
    run_id = args.run_id or available[0]
    if run_id not in available:
        parser.error(f"Run chưa hoàn tất hoặc không tồn tại: {run_id}")
    app = build_app(run_id)
    app.launch(server_name="127.0.0.1", server_port=args.port, share=False, inbrowser=True)


if __name__ == "__main__":
    main()
