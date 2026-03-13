import streamlit as st
import pandas as pd
import datetime

# إعدادات الصفحة لتناسب الهاتف والحاسوب
st.set_page_config(page_title="مكتب الأستاذ برادي عزيز", layout="wide")

# تصميم الهيدر كما طلبت سابقاً
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>مكتب الأستاذ برادي عزيز</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>نظام إدارة القضايا السحابي</h3>", unsafe_allow_html=True)

# دالة لحفظ وتحميل البيانات (ستكون سحابية لاحقاً، حالياً للتجربة محلياً)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["الموكل", "رقم القضية", "التاريخ", "الحالة"])

# القائمة الجانبية (تظهر في الهاتف عند الضغط على ☰)
menu = ["إضافة قضية", "جدول الجلسات", "البحث"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "إضافة قضية":
    st.subheader("تسجيل قضية جديدة")
    with st.form("case_form"):
        client_name = st.text_input("اسم الموكل")
        case_num = st.text_input("رقم القضية")
        case_date = st.date_input("تاريخ الجلسة", datetime.date.today())
        status = st.selectbox("الحالة", ["قيد الانتظار", "جلسة قادمة", "محكومة"])
        
        submit = st.form_submit_button("حفظ البيانات")
        if submit:
            new_data = {"الموكل": client_name, "رقم القضية": case_num, "التاريخ": str(case_date), "الحالة": status}
            st.session_state.data = st.session_state.data.append(new_data, ignore_index=True)
            st.success(f"تم تسجيل قضية {client_name} بنجاح!")

elif choice == "جدول الجلسات":
    st.subheader("مواعيد الجلسات المسجلة")
    st.table(st.session_state.data)

elif choice == "البحث":
    search = st.text_input("ابحث باسم الموكل أو رقم القضية")
    if search:
        filtered = st.session_state.data[st.session_state.data['الموكل'].str.contains(search)]
        st.write(filtered)