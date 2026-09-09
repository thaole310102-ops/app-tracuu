import re
import unicodedata
import pandas as pd
import streamlit as st
from st_keyup import st_keyup

# 1. Cấu hình trang
st.set_page_config(
    page_title="Tra Cứu Nhanh Đề Thi - Tác giả Eira",
    page_icon="🎯",
    layout="wide",
)

# 2. CSS Ẩn thông tin cá nhân & tối ưu giao diện
st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    section[data-testid="stSidebar"] div[class*="viewerBadge"],
    section[data-testid="stSidebar"] div[class*="profile"] {
        display: none !important;
    }
    .stAlert { padding: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎯 Hệ Thống Tra Cứu Đề Thi Siêu Tốc")
st.caption("✨ **Tác giả:** Eira | Tìm kiếm thông minh 75% Nghiệp vụ & 25% Kiến thức chung")


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


# Hàm xử lý file Excel phân loại danh mục
def process_category_files(uploaded_files, category_label, priority_rank):
    records = []
    if not uploaded_files:
        return records

    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

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
                                "category": category_label,
                                "priority": priority_rank,  # 1 cho Nghiệp vụ, 2 cho Kiến thức chung
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

    return records


# Thanh Sidebar đơn giản hóa tối đa
with st.sidebar:
    st.markdown("### ✍️ **Tác giả:** Eira")
    st.divider()

    st.header("⚙️ Chế độ tra cứu")
    search_field = st.radio(
        "Phạm vi tìm kiếm:",
        ["Chỉ tìm trong CÂU HỎI (Khuyên dùng)", "Tìm trong TOÀN BỘ (Cả Đáp án)"],
        index=0,
    )

    st.divider()
    st.header("📁 Tải tệp dữ liệu")

    st.markdown("**1. 📘 File Nghiệp Vụ (75%)**")
    file_nghiep_vu = st.file_uploader(
        "Tải 1 file Nghiệp vụ",
        type=["xlsx", "xls"],
        key="file_nv",
    )

    st.markdown("**2. 📚 Files Kiến Thức Chung (25%)**")
    files_kien_thuc = st.file_uploader(
        "Tải các file Kiến thức chung",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="files_kt",
    )

# Xử lý gộp dữ liệu
all_records = []
if file_nghiep_vu:
    all_records.extend(process_category_files(file_nghiep_vu, "📘 NGHIỆP VỤ", 1))

if files_kien_thuc:
    all_records.extend(process_category_files(files_kien_thuc, "📚 KIẾN THỨC CHUNG", 2))

if all_records:
    df_dataset = pd.DataFrame(all_records)
    total_rows = len(df_dataset)
    st.success(f"✅ Đã sẵn sàng tra cứu **{total_rows}** câu hỏi từ tất cả các file!")
else:
    df_dataset = pd.DataFrame()
    st.info("👈 Hãy tải file Nghiệp vụ và Kiến thức chung ở thanh menu bên trái để bắt đầu.")

# Ô tìm kiếm phản hồi tức thì
query = st_keyup(
    "Nhập từ khóa câu hỏi cần tìm trong bài thi:",
    placeholder="Gõ vài từ khóa chính trong câu hỏi...",
    debounce=200,
    key="search_box",
)

if query and not df_dataset.empty:
    norm_query = remove_accents(query)
    keywords = norm_query.split()

    if keywords:
        regex_pattern = "".join([f"(?=.*{re.escape(k)})" for k in keywords])

        if "Chỉ tìm trong CÂU HỎI" in search_field:
            mask = df_dataset["question_search"].str.contains(
                regex_pattern, regex=True, na=False
            )
        else:
            mask = df_dataset["full_search"].str.contains(
                regex_pattern, regex=True, na=False
            )

        matched_df = df_dataset[mask]

        # Ưu tiên sắp xếp câu Nghiệp vụ (75%) hiển thị lên trước
        matched_df = matched_df.sort_values(by="priority")
        total_found = len(matched_df)

        if total_found > 0:
            st.success(f"🎯 Tìm thấy **{total_found}** kết quả phù hợp:")

            display_records = matched_df.head(25).to_dict("records")

            for res in display_records:
                question_preview = res["data_dict"].get(
                    "CÂU HỎI", "Chi tiết dòng"
                )
                if len(question_preview) > 85:
                    question_preview = question_preview[:85] + "..."

                title_label = f"[{res['category']}] ❓ {question_preview} | 📄 {res['file_name']} (Dòng {res['row_index']})"

                with st.expander(f"📌 **{title_label}**"):
                    for col_title, val in res["data_dict"].items():
                        if "ĐÁP ÁN ĐÚNG" in col_title.upper():
                            st.markdown(f"- 🔴 **{col_title}:** **{val}**")
                        else:
                            st.write(f"- **{col_title}:** {val}")

            if total_found > 25:
                st.caption(
                    f"💡 Đang hiển thị 25/{total_found} kết quả. Hãy gõ thêm từ khóa để tìm chính xác nhất."
                )
        else:
            st.warning("Không tìm thấy kết quả nào phù hợp.")
elif query and df_dataset.empty:
    st.warning("Bạn chưa tải tệp dữ liệu nào lên hệ thống!")