import os
import re
import unicodedata
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Tra Cứu Bộ Câu Hỏi - Tác giả Eira",
    page_icon="📝",
    layout="wide",
)

# Tiêu đề chính và Thông tin Tác giả
st.title("📝 Hệ Thống Tra Cứu Câu Hỏi & Đáp Án")
st.caption("✨ **Tác giả:** Eira")  # Dòng hiển thị tên tác giả

UPLOAD_FOLDER = "./documents"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Thanh Sidebar Upload file & Tác giả
with st.sidebar:
    st.markdown("### ✍️ **Tác giả:** Eira")
    st.divider()
    st.header("📁 Tải tệp lên hệ thống")
    uploaded_files = st.file_uploader(
        "Chọn tệp Excel (.xlsx, .xls)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"Đã lưu {len(uploaded_files)} tệp!")
        st.cache_data.clear()  # Xóa cache để cập nhật dữ liệu mới


# Hàm chuẩn hóa chuỗi: Bỏ dấu tiếng Việt, đưa về chữ thường
def remove_accents(input_str):
    if not isinstance(input_str, str):
        input_str = str(input_str)
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


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


# Dùng cache_data để lưu dữ liệu vào bộ nhớ tạm, tăng tốc độ tìm kiếm tức thì
@st.cache_data
def load_all_excel_data(folder_path):
    all_data = []
    files = [
        f
        for f in os.listdir(folder_path)
        if f.endswith((".xlsx", ".xls")) and not f.startswith("~$")
    ]

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
            for sheet_name, df in excel_data.items():
                df = df.fillna("")
                for idx, row in df.iterrows():
                    raw_values = [str(val).strip() for val in row.values]

                    clean_dict = {}
                    for i, val in enumerate(raw_values):
                        if val and val.lower() != "nan":
                            header_name = (
                                STANDARD_HEADERS[i]
                                if i < len(STANDARD_HEADERS)
                                else f"Thông tin {i+1}"
                            )
                            clean_dict[header_name] = val

                    # Bỏ các dòng tiêu đề trùng lặp
                    if (
                        "STT" in clean_dict.values()
                        or "CÂU HỎI" in clean_dict.values()
                    ):
                        continue

                    if clean_dict:
                        full_row_text = " ".join(clean_dict.values())
                        normalized_text = remove_accents(full_row_text)

                        all_data.append(
                            {
                                "file_name": file_name,
                                "sheet": sheet_name,
                                "row_index": idx + 1,
                                "data_dict": clean_dict,
                                "normalized_text": normalized_text,
                            }
                        )
        except Exception as e:
            pass
    return all_data


# Tải toàn bộ dữ liệu vào bộ nhớ
dataset = load_all_excel_data(UPLOAD_FOLDER)
st.info(
    f"Hệ thống đã sẵn sàng tìm kiếm trên **{len(dataset)}** câu hỏi/dòng dữ liệu."
)

# Ô nhập liệu tự động cập nhật kết quả theo từng ký tự gõ
query = st.text_input(
    "Nhập từ khóa cần tìm (gõ không dấu, gõ tắt hoặc gõ từ rời rạc đều được):",
    placeholder="Ví dụ: bao lanh tsc, thanh toan quoc te, 226...",
)

if query.strip():
    norm_query = remove_accents(query.strip())
    keywords = norm_query.split()

    matched_results = []
    for item in dataset:
        if all(word in item["normalized_text"] for word in keywords):
            matched_results.append(item)

    if matched_results:
        st.success(f"Tìm thấy **{len(matched_results)}** kết quả phù hợp:")

        for res in matched_results:
            title_label = f"📄 File: {res['file_name']} | Sheet: {res['sheet']} | Dòng: {res['row_index']}"
            with st.expander(f"📌 **{title_label}**"):
                df_display = pd.DataFrame([res["data_dict"]])
                st.dataframe(df_display, use_container_width=True)

                st.markdown("**Nội dung chi tiết:**")
                for col_title, val in res["data_dict"].items():
                    st.write(f"- **{col_title}:** {val}")
    else:
        st.warning("Không tìm thấy kết quả nào phù hợp với từ khóa trên.")