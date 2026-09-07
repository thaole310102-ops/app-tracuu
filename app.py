import os
import re
import unicodedata
import pandas as pd
import streamlit as st
from st_keyup import st_keyup

# 1. Cấu hình trang
st.set_page_config(
    page_title="Tra Cứu Chính Xác - Tác giả Eira",
    page_icon="🎯",
    layout="wide",
)

# 2. Mã CSS sửa lỗi: Giữ lại menu chức năng, chỉ ẩn footer & thông tin tài khoản
st.markdown(
    """
    <style>
    /* Ẩn Footer mặc định của Streamlit */
    footer {visibility: hidden;}
    
    /* Ẩn thanh biểu tượng Streamlit góc trên bên phải */
    #MainMenu {visibility: hidden;}
    
    /* Ẩn chỉ riêng phần thông tin Profile/Email đăng nhập dưới góc Sidebar */
    section[data-testid="stSidebar"] div[class*="viewerBadge"],
    section[data-testid="stSidebar"] div[class*="profile"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎯 Hệ Thống Tra Cứu Câu Hỏi & Đáp Án")
st.caption("✨ **Tác giả:** Eira")

UPLOAD_FOLDER = "./documents"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Thanh Sidebar Upload file & Cấu hình
with st.sidebar:
    st.markdown("### ✍️ **Tác giả:** Eira")
    st.divider()
    st.header("⚙️ Chế độ tra cứu")
    search_mode = st.radio(
        "Phạm vi tìm kiếm:",
        ["Chỉ tìm trong CÂU HỎI (Khuyên dùng)", "Tìm trong TOÀN BỘ (Cả Đáp án)"],
        index=0,
    )
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


# Hàm bỏ dấu tiếng Việt chuẩn xác
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


# Tách riêng trường văn bản CÂU HỎI và NỘI DUNG KHÁC
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
                    question_text = ""
                    other_text = ""

                    for i, val in enumerate(raw_values):
                        if val and val.lower() != "nan":
                            header_name = (
                                STANDARD_HEADERS[i]
                                if i < len(STANDARD_HEADERS)
                                else f"Thông tin {i+1}"
                            )
                            clean_dict[header_name] = val

                            # Phân loại: Lấy riêng CÂU HỎI (thường nằm ở cột 2 - index 1)
                            if header_name == "CÂU HỎI" or i == 1:
                                question_text += " " + val
                            else:
                                other_text += " " + val

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
                                "question_search": remove_accents(question_text),
                                "full_search": remove_accents(full_row_text),
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
                "question_search",
                "full_search",
            ]
        )

    return pd.DataFrame(records)


# Tải toàn bộ dữ liệu
df_dataset = load_and_optimize_dataset(UPLOAD_FOLDER)
total_rows = len(df_dataset)
st.info(f"Hệ thống đã nạp **{total_rows}** dòng dữ liệu sẵn sàng tra cứu.")

# Ô nhập liệu tự động cập nhật
query = st_keyup(
    "Nhập từ khóa tra cứu (Kết quả cập nhật liên tục):",
    placeholder="Gõ từ khóa câu hỏi vào đây...",
    debounce=200,
    key="search_box",
)

if query and not df_dataset.empty:
    norm_query = remove_accents(query)
    keywords = norm_query.split()

    if keywords:
        regex_pattern = "".join([f"(?=.*{re.escape(k)})" for k in keywords])

        if "Chỉ tìm trong CÂU HỎI" in search_mode:
            # Lọc ưu tiên: Chỉ quét trên cột CÂU HỎI
            mask = df_dataset["question_search"].str.contains(
                regex_pattern, regex=True, na=False
            )
            matched_df = df_dataset[mask]
        else:
            # Quét trên toàn bộ dữ liệu
            mask = df_dataset["full_search"].str.contains(
                regex_pattern, regex=True, na=False
            )
            matched_df = df_dataset[mask]

        total_found = len(matched_df)

        if total_found > 0:
            st.success(
                f"🎯 Tìm thấy **{total_found}** kết quả phù hợp ({search_mode}):"
            )

            display_records = matched_df.head(30).to_dict("records")

            for res in display_records:
                # Lấy riêng nội dung câu hỏi hiển thị lên tiêu đề cho dễ nhìn
                question_preview = res["data_dict"].get(
                    "CÂU HỎI", "Chi tiết dòng"
                )
                if len(question_preview) > 90:
                    question_preview = question_preview[:90] + "..."

                title_label = f"❓ {question_preview} | 📄 {res['file_name']} (Dòng {res['row_index']})"

                with st.expander(f"📌 **{title_label}**"):
                    for col_title, val in res["data_dict"].items():
                        if "ĐÁP ÁN ĐÚNG" in col_title.upper():
                            st.markdown(f"- 🔴 **{col_title}:** **{val}**")
                        else:
                            st.write(f"- **{col_title}:** {val}")

            if total_found > 30:
                st.caption(
                    f"💡 Đang hiển thị 30/{total_found} kết quả. Hãy gõ thêm từ khóa để thu hẹp kết quả."
                )
        else:
            st.warning("Không tìm thấy câu hỏi nào chứa từ khóa trên.")