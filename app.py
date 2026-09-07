import os
import re
import unicodedata
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Tra Cứu Tốc Độ Cao - Tác giả Eira",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Hệ Thống Tra Cứu Tốc Độ Cao")
st.caption("✨ **Tác giả:** Eira")

UPLOAD_FOLDER = "./documents"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Thanh Sidebar
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
        st.cache_data.clear()


# Hàm bỏ dấu siêu tốc
def remove_accents(input_str):
    if not isinstance(input_str, str):
        input_str = str(input_str)
    input_str = input_str.replace("đ", "d").replace("Đ", "d")
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


# Nạp và tiền xử lý toàn bộ dữ liệu thành 1 DataFrame lớn trong RAM
@st.cache_data
def load_and_optimize_dataset(folder_path):
    records = []
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
                        records.append(
                            {
                                "file_name": file_name,
                                "sheet": sheet_name,
                                "row_index": idx + 1,
                                "data_dict": clean_dict,
                                "search_text": remove_accents(full_row_text),
                            }
                        )
        except Exception:
            pass

    if not records:
        return pd.DataFrame(
            columns=[
                "file_name",
                "sheet",
                "row_index",
                "data_dict",
                "search_text",
            ]
        )

    # Chuyển đổi thành Pandas DataFrame để tối ưu hóa truy vấn bằng C
    return pd.DataFrame(records)


# Tải toàn bộ dữ liệu
df_dataset = load_and_optimize_dataset(UPLOAD_FOLDER)
total_rows = len(df_dataset)
st.info(f"Hệ thống đã nạp **{total_rows}** dòng dữ liệu sẵn sàng tìm kiếm.")

# Ô nhập dữ liệu
query = st.text_input(
    "Nhập từ khóa tra cứu (Tự động cập nhật kết quả siêu tốc):",
    placeholder="Ví dụ: dau moi, 227, ban chinh sach tin dung...",
)

if query.strip() and not df_dataset.empty:
    norm_query = remove_accents(query.strip())
    keywords = norm_query.split()

    # Xây dựng regex Lookahead giúp quét siêu tốc toàn bộ tập dữ liệu cùng lúc
    # Mẫu Regex: (?=.*tu1)(?=.*tu2)(?=.*tu3)
    regex_pattern = "".join([f"(?=.*{re.escape(k)})" for k in keywords])

    # Lọc dữ liệu bằng C-Engine của Pandas (tốc độ ánh sáng)
    mask = df_dataset["search_text"].str.contains(
        regex_pattern, regex=True, na=False
    )
    matched_df = df_dataset[mask]

    total_found = len(matched_df)

    if total_found > 0:
        st.success(f"⚡ Tìm thấy **{total_found}** kết quả phù hợp:")

        # Giới hạn hiển thị 50 kết quả đầu tiên nếu tìm thấy quá nhiều để giao diện không bị giật
        display_records = matched_df.head(50).to_dict("records")

        for res in display_records:
            title_label = f"📄 File: {res['file_name']} | Sheet: {res['sheet']} | Dòng: {res['row_index']}"
            with st.expander(f"📌 **{title_label}**"):
                # Bảng chi tiết
                st.dataframe(
                    pd.DataFrame([res["data_dict"]]), use_container_width=True
                )

                # Danh sách văn bản
                st.markdown("**Chi tiết nội dung:**")
                for col_title, val in res["data_dict"].items():
                    st.write(f"- **{col_title}:** {val}")

        if total_found > 50:
            st.info(
                f"Đang hiển thị 50/{total_found} kết quả đầu tiên. Hãy gõ thêm từ khóa chi tiết hơn để thu hẹp tìm kiếm."
            )
    else:
        st.warning("Không tìm thấy kết quả phù hợp.")