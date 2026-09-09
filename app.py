import re
import unicodedata
import pandas as pd
import streamlit as st
from st_keyup import st_keyup

# 1. Cấu hình trang
st.set_page_config(
    page_title="Tra Cứu Cực Nhanh - Tác giả Eira",
    page_icon="🎯",
    layout="wide",
)

# 2. CSS Ẩn thông tin tài khoản & tối ưu giao diện
st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
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


# Hàm bỏ dấu tiếng Việt
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


# Hàm xử lý file Excel trực tiếp trong RAM riêng của người dùng
def process_uploaded_files(uploaded_files):
    records = []
    for uploaded_file in uploaded_files:
        try:
            excel_data = pd.read_excel(uploaded_file, sheet_name=None, header=None)
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

                            if header_name == "CÂU HỎI" or i == 1:
                                question_text += " " + val
                            else:
                                other_text += " " + val

                    if (
                        "STT" in clean_dict.values()
                        or "CÂU HỎI" in clean_dict.values()
                    ):
                        continue

                    if clean_dict:
                        full_row_text = " ".join(clean_dict.values())
                        records.append(
                            {
                                "file_name": uploaded_file.name,
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


# Thanh Sidebar
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
    st.header("📁 Tải tệp dữ liệu cá nhân")
    uploaded_files = st.file_uploader(
        "Chọn các tệp Excel (.xlsx, .xls)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
    )

# Xử lý dữ liệu riêng cho thiết bị/phiên làm việc hiện tại
if uploaded_files:
    df_dataset = process_uploaded_files(uploaded_files)
    total_rows = len(df_dataset)
    st.success(
        f"✅ Đã nạp thành công **{total_rows}** dòng dữ liệu từ {len(uploaded_files)} tệp của bạn."
    )
else:
    df_dataset = pd.DataFrame()
    st.info("👈 Hãy tải (upload) tệp Excel của bạn ở thanh menu bên trái để bắt đầu tra cứu.")

# Ô tìm kiếm phản hồi mượt mà
query = st_keyup(
    "Nhập từ khóa tra cứu (Tự động cập nhật kết quả):",
    placeholder="Gõ từ khóa câu hỏi vào đây...",
    debounce=250,
    key="search_box",
)

if query and not df_dataset.empty:
    norm_query = remove_accents(query)
    keywords = norm_query.split()

    if keywords:
        regex_pattern = "".join([f"(?=.*{re.escape(k)})" for k in keywords])

        if "Chỉ tìm trong CÂU HỎI" in search_mode:
            mask = df_dataset["question_search"].str.contains(
                regex_pattern, regex=True, na=False
            )
        else:
            mask = df_dataset["full_search"].str.contains(
                regex_pattern, regex=True, na=False
            )

        matched_df = df_dataset[mask]
        total_found = len(matched_df)

        if total_found > 0:
            st.success(f"🎯 Tìm thấy **{total_found}** kết quả phù hợp:")

            display_records = matched_df.head(25).to_dict("records")

            for res in display_records:
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

            if total_found > 25:
                st.caption(
                    f"💡 Đang hiển thị 25/{total_found} kết quả. Hãy gõ thêm từ khóa để thu hẹp kết quả."
                )
        else:
            st.warning("Không tìm thấy câu hỏi nào chứa từ khóa trên.")
elif query and df_dataset.empty:
    st.warning("Bạn chưa tải tệp dữ liệu nào lên hệ thống!")