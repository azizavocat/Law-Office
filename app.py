import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- إعدادات الملفات ---
DB_FILE = "lawyer_master_data.json"
CONFIG_FILE = "config.json"

# --- دالات إدارة الإعدادات وكلمة السر ---
def get_password():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("password", "1234")
        except: return "1234"
    return "1234"

def save_password(new_pwd):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"password": new_pwd}, f)

# --- نظام الحماية والدخول ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; color: #2c3e50;'>مكتب الأستاذ برادي عزيز</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>يرجى إدخال كلمة المرور للوصول إلى بيانات المكتب</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("كلمة المرور:", type="password")
            if st.button("دخول للنظام"):
                if pwd == get_password():
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("كلمة المرور غير صحيحة ❌")
        return False
    return True

# --- تشغيل البرنامج بعد التحقق ---
if check_password():
    st.set_page_config(page_title="مكتب الأستاذ برادي عزيز", layout="wide")

    # ثوابت البيانات القانونية
    SECTIONS_MAP = {
        "civil": ["المدني", "العقاري", "شؤون الأسرة", "التجاري", "الاجتماعي", "الاستعجالي"],
        "criminal": ["جنحة", "جناية", "مخالفة", "تحقيق", "غرفة الاتهام"],
        "admin": ["إلغاء", "تجاوز سلطة", "صفقات عمومية", "استعجالي"],
        "execution": ["تنفيذ مدني", "تنفيذ إداري", "إجراءات الحجز"],
        "appeals": ["استئناف (عادي)", "معارضة (عادي)", "نقض (غير عادي)", "التماس إعادة النظر"],
        "study": ["استشارة", "إعداد عريضة", "مراجعة ملف"]
    }
    OUTCOMES = ["جارية", "قيد الدراسة", "لجواب الخصم", "لجوابنا", "للمداولة", "للتحقيق", "تبليغ عريضة", "حكم نهائي", "محكومة"]

    # دالات إدارة البيانات
    def load_data():
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for c in data:
                        c.setdefault("total_agreed", 0)
                        c.setdefault("payments_list", [])
                    return data
            except: return []
        return []

    def save_data(data):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    cases = load_data()

    # --- القائمة الجانبية ---
    st.sidebar.title("⚖️ إدارة المكتب")
    menu = ["📊 جدول القضايا", "➕ إضافة/تعديل ملف", "💰 المالية والأتعاب", "📁 الأرشيف", "⚙️ الإعدادات"]
    choice = st.sidebar.radio("اختر القسم:", menu)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 1. جدول القضايا ---
    if choice == "📊 جدول القضايا":
        st.subheader("📋 القضايا الجارية والبحث")
        if not cases:
            st.info("لا توجد قضايا مسجلة حالياً.")
        else:
            df = pd.DataFrame(cases)
            ongoing = df[~df['status'].isin(["حكم نهائي", "محكومة"])]
            search = st.text_input("🔍 ابحث عن اسم موكل أو رقم قضية:")
            if search:
                ongoing = ongoing[ongoing.astype(str).apply(lambda x: search in x.values, axis=1)]
            st.dataframe(ongoing[["num", "year", "moakal", "khasm", "date", "status", "sec", "action"]], use_container_width=True)

    # --- 2. إضافة وتعديل الملفات ---
    elif choice == "➕ إضافة/تعديل ملف":
        st.subheader("📝 تسجيل أو تحديث ملف قضية")
        with st.form("case_form"):
            col1, col2 = st.columns(2)
            with col1:
                num = st.text_input("رقم القضية")
                year = st.text_input("السنة", value=str(datetime.now().year))
                moakal = st.text_input("اسم الموكل")
                mode = st.selectbox("نوع التبويب", list(SECTIONS_MAP.keys()))
            with col2:
                khasm = st.text_input("اسم الخصم")
                sec = st.selectbox("القسم/الفرع", SECTIONS_MAP[mode])
                date = st.text_input("تاريخ الجلسة", value=datetime.now().strftime("%d/%m/%Y"))
                status = st.selectbox("وضعية القضية", OUTCOMES)
            action = st.text_area("الملاحظات والإجراءات")
            
            if st.form_submit_button("✅ حفظ"):
                if num and moakal:
                    new_case = {"num": num, "year": year, "moakal": moakal, "khasm": khasm, "type": mode, "sec": sec, "date": date, "status": status, "action": action, "total_agreed": 0, "payments_list": []}
                    cases = [c for c in cases if not (c['num'] == num and c['year'] == year)]
                    cases.append(new_case)
                    save_data(cases)
                    st.success("تم الحفظ!")
                else: st.error("أكمل البيانات الأساسية.")

    # --- 3. النظام المالي ---
    elif choice == "💰 المالية والأتعاب":
        st.subheader("💵 تتبع المستحقات المالية")
        if cases:
            names = [f"{c['num']}/{c['year']} - {c['moakal']}" for c in cases]
            sel_case_name = st.selectbox("اختر ملف الموكل:", names)
            target = next(c for c in cases if f"{c['num']}/{c['year']} - {c['moakal']}" == sel_case_name)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                target['total_agreed'] = st.number_input("إجمالي الاتفاق (دج)", value=float(target.get('total_agreed', 0)))
            with col2:
                paid_sum = sum(p['amount'] for p in target.get('payments_list', []))
                st.metric("المبلغ المحصل", f"{paid_sum:,.2f}")
            with col3:
                st.metric("الديون المتبقية", f"{(target['total_agreed'] - paid_sum):,.2f}")
            
            new_pay = st.number_input("تسجيل دفعة جديدة (دج)", min_value=0.0)
            if st.button("💵 حفظ الدفعة"):
                if new_pay > 0:
                    target['payments_list'].append({"amount": new_pay, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})
                    save_data(cases)
                    st.success("تم!")
                    st.rerun()

    # --- 4. الأرشيف ---
    elif choice == "📁 الأرشيف":
        st.subheader("📁 الأرشيف")
        df = pd.DataFrame(cases)
        if not df.empty:
            arch = df[df['status'].isin(["حكم نهائي", "محكومة"])]
            st.dataframe(arch, use_container_width=True)

    # --- 5. الإعدادات ---
    elif choice == "⚙️ الإعدادات":
        st.subheader("⚙️ الإعدادات")
        old_p = st.text_input("الحالية", type="password")
        new_p = st.text_input("الجديدة", type="password")
        if st.button("تغيير"):
            if old_p == get_password():
                save_password(new_p)
                st.success("تم التغيير!")
            else: st.error("خطأ!")
