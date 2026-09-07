import os
import docx
import pandas as pd
import PyPDF2
import streamlit as st

st.set_page_config(
    page_title="Tra Cứu Bộ Câu Hỏi Excel", page_icon="📝", layout="wide"
)

st.title("📝 Hệ Thống Tra Cứu Câu Hỏi & Đáp Án")

UPLOAD_FOLDER = "./documents"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Thanh Sidebar Upload file
with st.sidebar:
    st.header("📁 Tải tệp lên hệ thống")
    uploaded_files = st.file_uploader(
        "Chọn tệp Excel (.xlsx, .xls) hoặc Word/PDF",
        type=["xlsx", "xls", "docx", "pdf", "txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"Đã lưu {len(uploaded_files)} tệp!")

# Danh sách tiêu đề chuẩn bắt buộc hiển thị
STANDARD_HEADERS = [
    "STT",
    "CÂU HỎI",
    "ĐÁP ÁN 1",
    "ĐÁP ÁN 2",
    "ĐÁP ÁN 3",
    "ĐÁP ÁN 4",
    "ĐÁP ÁN ĐÚNG",
    "TRÍCH DẪN NGUỒN CÂU HỎI",
]


def search_in_excel(filepath, query):
    results = []
    try:
        excel_data = pd.read_excel(filepath, sheet_name=None, header=None)

        for sheet_name, df in excel_data.items():
            df = df.fillna("")

            # Lặp qua từng dòng dữ liệu trong Excel
            for idx, row in df.iterrows():
                # Bỏ qua các dòng tiêu đề chung ở đầu trang (chứa chữ BỘ CÂU HỎI, ĐỘC LẬP - TỰ DO...)
                row_str = " ".join([str(val) for val in row.values])

                if query.lower() in row_str.lower():
                    # Tạo danh sách các giá trị không bị rỗng trong dòng
                    raw_values = [str(val).strip() for val in row.values]

                    # Áp tiêu đề chuẩn tương ứng với từng cột
                    clean_dict = {}
                    for i, val in enumerate(raw_values):
                        if val and val.lower() != "nan":
                            if i < len(STANDARD_HEADERS):
                                header_name = STANDARD_HEADERS[i]
                            else:
                                header_name = f"Thông tin thêm {i+1}"
                            clean_dict[header_name] = val

                    # Bỏ qua dòng nếu chỉ chứa tiêu đề file
                    if (
                        "STT" in clean_dict.values()
                        or "CÂU HỎI" in clean_dict.values()
                    ):
                        continue

                    if clean_dict:
                        # Tạo dataframe hiển thị đẹp
                        display_df = pd.DataFrame([clean_dict])
                        results.append(
                            {
                                "sheet": sheet_name,
                                "row_index": idx + 1,
                                "data_dict": clean_dict,
                                "raw_row_df": display_df,
                            }
                        )
    except Exception as e:
        st.error(f"Lỗi đọc file Excel {filepath}: {e}")
    return results


# Danh sách tệp
all_files = [
    f
    for f in os.listdir(UPLOAD_FOLDER)
    if f.endswith((".xlsx", ".xls", ".docx", ".pdf", ".txt"))
]
st.info(f"Số lượng file trong hệ thống: **{len(all_files)}** file")

# Ô tìm kiếm từ khóa
query = st.text_input(
    "Nhập câu hỏi hoặc từ khóa cần tra đáp án:",
    placeholder="Ví dụ: Ban Chính sách Tín dụng, Thanh toán quốc tế...",
)

if query:
    total_found = 0

    for file_name in all_files:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        if file_name.endswith((".xlsx", ".xls")):
            excel_results = search_in_excel(file_path, query)

            if excel_results:
                total_found += len(excel_results)
                st.subheader(
                    f"📄 File: `{file_name}` — Tìm thấy {len(excel_results)} kết quả"
                )

                for res in excel_results:
                    with st.expander(
                        f"📌 **Sheet [{res['sheet']}] - Dòng {res['row_index']}**"
                    ):
                        # 1. Bảng dữ liệu chuẩn tiêu đề
                        st.markdown("**Bảng thông tin chi tiết:**")
                        st.dataframe(
                            res["raw_row_df"], use_container_width=True
                        )

                        # 2. Danh sách tóm tắt từng mục
                        st.markdown("**Nội dung chi tiết:**")
                        for col_title, val in res["data_dict"].items():
                            st.write(f"- **{col_title}:** {val}")

    if total_found == 0:
        st.warning("Không tìm thấy câu hỏi/dòng nào chứa từ khóa trên.")