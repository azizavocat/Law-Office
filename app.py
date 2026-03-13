import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="مكتب الأستاذ برادي عزيز", layout="wide")

# تخصيص التصميم عبر CSS ليشبه نسخة الحاسوب
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2c3e50; color: white; }
    .stDataFrame { border: 1px solid #2c3e50; border-radius: 5px; }
    h1, h2, h3 { color: #2c3e50; text-align: right; font-family: 'Arial'; }
    div[data-testid="stExpander"] { background-color: white; border: 1px solid #d1d8e0; }
    .css-10trblm { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- إدارة البيانات (نفس منطق حاسوبك) ---
DB_FILE = "lawyer_master_data.json"
CONFIG_FILE = "config.json"

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

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # التأكد من وجود الحقول المالية لكل قضية
                for c in data:
                    c.setdefault("total_agreed", 0)
                    c.setdefault("payments_list", [])
                return data
        except: return []
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- نظام الحماية ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.markdown("<h2 style='text-align: center;'>🔐 نظام إدارة القضايا - الأستاذ برادي عزيز</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        pwd = st.text_input("ادخل كلمة مرور المكتب:", type="password")
        if st.button("دخول"):
            if pwd == get_password():
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("عذراً، كلمة المرور خاطئة ❌")
    st.stop()

# --- البرنامج الرئيسي (بعد الدخول) ---
cases = load_data()

# القائمة الجانبية بتنسيق واضح
st.sidebar.markdown(f"<h3 style='text-align:center;'>المحامي: برادي عزيز</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = ["📊 جدول القضايا العام", "➕ إضافة ملف جديد", "💰 المحاسبة والأتعاب", "📁 أرشيف القضايا", "⚙️ إعدادات النظام"]
choice = st.sidebar.radio("الانتقال إلى:", menu)

# --- 1. جدول القضايا (بتنسيق معرب بالكامل) ---
if choice == "📊 جدول القضايا العام":
    st.markdown("## 📋 جدول سير القضايا")
    if not cases:
        st.info("لا توجد قضايا مسجلة حالياً.")
    else:
        # تحويل البيانات لجدول وتسمية الأعمدة بالعربية
        df = pd.DataFrame(cases)
        # تصفية القضايا غير المنتهية فقط
        active_df = df[~df['status'].isin(["حكم نهائي", "محكومة"])]
        
        # إعادة تسمية الأعمدة للعرض فقط
        display_df = active_df.rename(columns={
            "num": "رقم القضية",
            "year": "السنة",
            "moakal": "الموكل",
            "khasm": "الخصم",
            "sec": "القسم/الفرع",
            "date": "تاريخ الجلسة",
            "status": "مآل القضية",
            "action": "الإجراء المتخذ"
        })
        
        search = st.text_input("🔍 بحث سريع في الملفات (اسم، رقم، تاريخ...):")
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: search in x.values, axis=1)]
        
        st.dataframe(display_df[["رقم القضية", "السنة", "الموكل", "الخصم", "القسم/الفرع", "تاريخ الجلسة", "مآل القضية", "الإجراء المتخذ"]], use_container_width=True)

# --- 2. إضافة ملف (محاكاة شكل Tkinter) ---
elif choice == "➕ إضافة ملف جديد":
    st.markdown("## 📝 إدخال بيانات قضية جديدة")
    with st.container():
        with st.form("add_form", clear_on_submit=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c1:
                num = st.text_input("رقم القضية")
                year = st.text_input("السنة", value=str(datetime.now().year))
            with r1c2:
                moakal = st.text_input("اسم الموكل (الطالب)")
                khasm = st.text_input("اسم الخصم (المطلوب)")
            with r1c3:
                date = st.text_input("تاريخ أول جلسة", value=datetime.now().strftime("%d/%m/%Y"))
                status = st.selectbox("وضعية الملف", ["جارية", "قيد الدراسة", "لجواب الخصم", "للمداولة", "تبليغ", "حكم نهائي"])
            
            r2c1, r2c2 = st.columns([1, 2])
            with r2c1:
                sec = st.selectbox("القسم القضائي", ["المدني", "العقاري", "شؤون الأسرة", "الجزائي", "الاستعجالي", "الإداري"])
            with r2c2:
                action = st.text_area("ملاحظات إضافية حول الإجراءات")
            
            submit = st.form_submit_button("📥 حفظ الملف في قاعدة البيانات")
            if submit:
                if num and moakal:
                    new_case = {
                        "num": num, "year": year, "moakal": moakal, "khasm": khasm,
                        "sec": sec, "date": date, "status": status, "action": action,
                        "total_agreed": 0, "payments_list": []
                    }
                    # حذف القديم إذا كان تحديث أو إضافة جديد
                    cases = [c for c in cases if not (c['num'] == num and c['year'] == year)]
                    cases.append(new_case)
                    save_data(cases)
                    st.success(f"✅ تم تسجيل قضية الموكل {moakal} بنجاح")
                else:
                    st.error("⚠️ يرجى إدخال رقم القضية واسم الموكل.")

# --- 3. المحاسبة (نفس دوالك المالية) ---
elif choice == "💰 المحاسبة والأتعاب":
    st.markdown("## 💰 إدارة المستحقات المالية")
    if cases:
        names = [f"{c['num']}/{c['year']} - {c['moakal']}" for c in cases]
        sel = st.selectbox("اختر ملف الموكل لمراجعة حسابه:", names)
        target = next(c for c in cases if f"{c['num']}/{c['year']} - {c['moakal']}" == sel)
        
        col_pay1, col_pay2 = st.columns(2)
        with col_pay1:
            st.markdown("### ملخص الحساب")
            total = st.number_input("إجمالي الأتعاب المتفق عليها (دج):", value=float(target.get('total_agreed', 0)))
            target['total_agreed'] = total
            paid = sum(p['amount'] for p in target.get('payments_list', []))
            st.write(f"**المبلغ المقبوض:** {paid:,.2f} دج")
            st.write(f"**المبلغ المتبقي:** {total - paid:,.2f} دج")
            if st.button("تحديث الإجمالي"):
                save_data(cases)
                st.success("تم تحديث المبلغ الإجمالي")

        with col_pay2:
            st.markdown("### تسجيل دفعة")
            amount = st.number_input("مبلغ الدفعة الجديدة (دج):", min_value=0.0)
            if st.button("➕ تأكيد استلام الدفعة"):
                if amount > 0:
                    target['payments_list'].append({"amount": amount, "date": datetime.now().strftime("%d/%m/%Y")})
                    save_data(cases)
                    st.success("تم تسجيل الدفعة بنجاح")
                    st.rerun()

# --- 5. الإعدادات ---
elif choice == "⚙️ إعدادات النظام":
    st.markdown("## ⚙️ التحكم في النظام")
    with st.expander("تغيير كلمة مرور الدخول"):
        old_p = st.text_input("كلمة المرور الحالية", type="password")
        new_p = st.text_input("كلمة المرور الجديدة", type="password")
        if st.button("حفظ كلمة السر الجديدة"):
            if old_p == get_password():
                save_password(new_p)
                st.success("تم التغيير! استخدم الكلمة الجديدة في الدخول القادم.")
            else: st.error("الكلمة الحالية غير صحيحة")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state["password_correct"] = False
    st.rerun()
