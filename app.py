import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import re
from datetime import datetime, timedelta

# دعم المكتبات الخارجية
try:
    from fpdf import FPDF
    import arabic_reshaper
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

class LawyerProApp:
    def __init__(self, root):
        self.root = root
        self.main_font_name = "Times New Roman"
        self.root.title("مكتب الأستاذ برادي عزيز - النسخة المطورة")
        self.root.geometry("1580x900") 
        self.root.configure(bg="#f4f7f6")
        
        self.font_main = (self.main_font_name, 14)
        self.font_bold = (self.main_font_name, 14, "bold")
        self.font_header = (self.main_font_name, 16, "bold")

        self.db_file = "lawyer_master_data.json"
        self.docs_dir = "Digital_Archive_Bradi"
        self.backup_dir = "Backups_Bradi" 
        
        if not os.path.exists(self.docs_dir): os.makedirs(self.docs_dir)
        if not os.path.exists(self.backup_dir): os.makedirs(self.backup_dir)
            
        self.cases_list = self.load_data()
        self.editing_index = None 

        style = ttk.Style()
        style.configure("Treeview", font=self.font_main, rowheight=35)
        style.configure("Treeview.Heading", font=self.font_bold)

        self.roles_civil_admin = ["مدعي", "مدعى عليه", "مستأنف", "مستأنف عليه", "مرجع", "مرجع ضده", "منفذ", "منفذ عليه", "قائم بالتنفيذ", "متدخل في الخصام"]
        self.roles_criminal = ["متهم", "ضحية", "مدعي عام", "ذوي الحقوق", "طرف مدني", "مسؤول مدني"]
        self.roles_appeals = ["طاعن", "مطعون ضده", "مستأنف", "مستأنف ضده", "معارض"]
        
        self.outcomes_general = ["جارية", "قيد الدراسة", "لجواب الخصم", "لجوابنا", "للمداولة", "للتحقيق", "تبليغ عريضة", "حكم نهائي", "محكومة"]
        self.outcomes_criminal = ["لحضور الأطراف", "لحضور المتهم", "للجواب", "للمداولة", "محكومة", "حكم نهائي"]
        
        self.sections_map = {
            "civil": ["المدني", "العقاري", "شؤون الأسرة", "التجاري", "الاجتماعي", "الاستعجالي"],
            "criminal": ["جنحة", "جناية", "مخالفة", "تحقيق", "غرفة الاتهام"],
            "admin": ["إلغاء", "تجاوز سلطة", "صفقات عمومية", "استعجالي"],
            "execution": ["تنفيذ مدني", "تنفيذ إداري", "إجراءات الحجز"],
            "appeals": ["استئناف (عادي)", "معارضة (عادي)", "نقض (غير عادي)", "التماس إعادة النظر"],
            "complaints": ["شكوى وكيل الجمهورية", "شكوى الأمن"],
            "study": ["استشارة", "إعداد عريضة", "مراجعة ملف", "جنحة", "جناية", "مدني"]
        }

        self.setup_ui()
        self.refresh_table()
        self.root.bind("<Return>", self.handle_enter_navigation)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- الدوال الأساسية المدمجة ---

    def ar(self, text):
        if not text or not ARABIC_SUPPORT: return text
        t = str(text).replace('(', '<<').replace(')', '>>')
        reshaped = arabic_reshaper.reshape(t)
        parts = re.split(r'(\s+)', reshaped)
        res = [p if (not p.strip() or re.search(r'[0-9]', p)) else p[::-1] for p in parts]
        return "".join(res[::-1])

    def load_data(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for c in data:
                        c.setdefault("total_agreed", 0); c.setdefault("payments_list", []); c.setdefault("index_num", "")
                        c.setdefault("final_type", ""); c.setdefault("final_num", ""); c.setdefault("final_date", "")
                    return data
            except: return []
        return []

    def save_to_json(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.cases_list, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#2c3e50", pady=12); self.top_frame.pack(fill="x")
        tk.Label(self.top_frame, text="البحث الشامل:", fg="white", bg="#2c3e50", font=self.font_bold).pack(side="left", padx=15)
        self.search_var = tk.StringVar(); self.search_var.trace("w", lambda *a: self.execute_global_search())
        self.search_entry = tk.Entry(self.top_frame, textvariable=self.search_var, width=35, font=self.font_main, justify="right")
        self.search_entry.pack(side="left", padx=5)
        tk.Button(self.top_frame, text="📄 طباعة المعروض حالياً", command=self.print_search_results, bg="#e67e22", fg="white", font=self.font_bold, padx=15).pack(side="left", padx=20)
        
        self.stats_frame = tk.Frame(self.top_frame, bg="#34495e", padx=15); self.stats_frame.pack(side="right", padx=20)
        self.lbl_today = tk.Label(self.stats_frame, text="جلسات اليوم: 0", fg="#ff7675", bg="#34495e", font=self.font_bold); self.lbl_today.pack(side="right", padx=10)
        self.lbl_tomorrow = tk.Label(self.stats_frame, text="جلسات الغد: 0", fg="#ffeaa7", bg="#34495e", font=self.font_bold); self.lbl_tomorrow.pack(side="right", padx=10)

        self.search_results_frame = tk.LabelFrame(self.root, text=" نتائج البحث الفوري ", bg="#ecf0f1", font=self.font_bold)
        self.search_results_tree = ttk.Treeview(self.search_results_frame, columns=("9","7","6","5","4","3","2","1"), show="headings", height=5)
        for i, h in zip("97654321", ["الملاحظات", "النوع", "مآل", "الجلسة", "الخصم", "الموكل", "الجهة", "الملف"]):
            self.search_results_tree.heading(i, text=h); self.search_results_tree.column(i, anchor="e", width=140)
        self.search_results_tree.pack(fill="both", expand=True, padx=10, pady=5); self.search_results_tree.bind("<Double-1>", self.load_from_search)

        self.notebook = ttk.Notebook(self.root); self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        tabs_info = [("civil", "القسم المدني"), ("criminal", "الجزائي"), ("admin", "الإداري"), ("execution", "التنفيذ"), ("appeals", "تبويب الطعون"), ("complaints", "الشكاوى"), ("study", "📖 التبويب المكتبي")]
        self.tabs = {}
        for key, title in tabs_info:
            frame = tk.Frame(self.notebook, bg="#f4f7f6")
            self.notebook.add(frame, text=title)
            self.tabs[key] = {"title": title, "data": self.build_tab_content(frame, key)}

        self.archive_tab = tk.Frame(self.notebook, bg="#f4f7f6")
        self.notebook.add(self.archive_tab, text="📁 الأرشيف")
        self.archive_data = self.build_archive_ui(self.archive_tab)

        self.fin_tab = tk.Frame(self.notebook, bg="#f4f7f6"); self.notebook.add(self.fin_tab, text="💰 الأتعاب والمالية")
        self.build_finance_ui(self.fin_tab)

    def build_tab_content(self, parent, mode):
        lbl_bg = "#e8f6f3" if mode == "study" else "white"
        f = tk.LabelFrame(parent, text=" إدارة ملف القضية ", font=self.font_header, bg=lbl_bg, padx=10, pady=10); f.pack(pady=5, padx=10, fill="x")
        fields = {}
        
        if mode in ["civil", "admin", "study"]: roles = self.roles_civil_admin
        elif mode == "criminal": roles = self.roles_criminal
        elif mode == "appeals": roles = self.roles_appeals
        else: roles = ["منفذ", "منفذ عليه", "قائم بالتنفيذ"]
        
        outcomes = self.outcomes_criminal if mode == "criminal" else self.outcomes_general
        jurisdiction = ["المحكمة", "المجلس", "المحكمة العليا", "مجلس الدولة", "مكتب المحامي"]
        
        def add_f(r, c, txt, key, w, dv="", is_cmb=False, vals=None):
            lbl = tk.Label(f, text=txt, bg=lbl_bg, font=self.font_main); lbl.grid(row=r, column=c, sticky="e", pady=5)
            wgt = ttk.Combobox(f, values=vals, width=w, font=self.font_main, state="normal", justify='right') if is_cmb else tk.Entry(f, width=w, justify='right', font=self.font_main)
            if is_cmb: wgt.set(vals[0] if vals else "")
            else: wgt.insert(0, str(dv))
            wgt.grid(row=r, column=c+1, padx=5, sticky="w"); fields[key] = wgt; return lbl, wgt

        num_label = "رقم القضية:" if mode in ["civil", "criminal", "admin"] else "رقم الملف:"
        add_f(0, 0, num_label, "num", 10); add_f(0, 2, "السنة:", "year", 6, datetime.now().year); add_f(0, 4, "رقم الفهرس:", "index_num", 15)
        
        lbl_sec, cmb_sec = add_f(0, 6, "النوع/القسم:", "sec", 20, is_cmb=True, vals=self.sections_map.get(mode))
        cmb_sec.bind("<<ComboboxSelected>>", lambda e: self.update_roles_by_sec(e, fields, mode))

        add_f(1, 0, "الموكل:", "moakal", 20); add_f(1, 2, "صفته:", "m_role", 18, is_cmb=True, vals=roles); add_f(1, 4, "الخصم:", "khasm", 20); add_f(1, 6, "صفته:", "k_role", 18, is_cmb=True, vals=roles)
        
        lbl_exp, w_exp = add_f(2, 0, "المحضر/الخبير:", "expert", 20)
        if mode == "criminal": lbl_exp.grid_forget(); w_exp.grid_forget(); w_exp.insert(0, "N/A")
        add_f(2, 2, "تاريخ الجلسة:", "date", 15, datetime.now().strftime("%d/%m/%Y"))
        st_w = add_f(2, 4, "مآل القضية:", "status", 15, is_cmb=True, vals=outcomes)[1]
        if mode == "study": st_w.set("قيد الدراسة")
        
        add_f(2, 6, "الجهة القضائية:", "lvl", 15, is_cmb=True, vals=jurisdiction)
        
        tk.Label(f, text="ملاحظات:", bg=lbl_bg, font=self.font_main).grid(row=3, column=0, sticky="e")
        w_action = tk.Entry(f, width=105, justify='right', font=self.font_main); w_action.grid(row=3, column=1, columnspan=6, padx=5, pady=10, sticky="w"); fields["action"] = w_action

        btn_f = tk.Frame(parent, bg="#f4f7f6"); btn_f.pack(pady=5)
        tk.Button(btn_f, text="✅ حفظ البيانات", command=lambda: self.save_case(fields, mode), bg="#27ae60", fg="white", width=18, font=self.font_bold).pack(side="right", padx=5)
        if mode == "study": tk.Button(btn_f, text="🚀 تحويل إلى قضية جارية", command=lambda: self.transfer_case_window(), bg="#d35400", fg="white", width=20, font=self.font_bold).pack(side="right", padx=5)
        tk.Button(btn_f, text="📂 فتح المجلد", command=lambda: self.open_case_folder(fields), bg="#2980b9", fg="white", width=15, font=self.font_bold).pack(side="right", padx=5)
        tk.Button(btn_f, text="💰 الموالية المالية", command=lambda: self.go_to_finance(fields), bg="#8e44ad", fg="white", width=15, font=self.font_bold).pack(side="right", padx=5)
        tk.Button(btn_f, text="🗑️ حذف الملف", command=lambda: self.delete_case(mode), bg="#c0392b", fg="white", width=15, font=self.font_bold).pack(side="right", padx=5)
        
        tree = ttk.Treeview(parent, columns=("8","6","5","4","3","2","1"), show="headings", height=12)
        for i, h in zip("8654321", ["الملاحظات", "مآل", "الجلسة", "الخصم", "الموكل", "الجهة", "الملف"]): tree.heading(i, text=h); tree.column(i, anchor="e", width=155)
        tree.pack(fill="both", expand=True, padx=15, pady=5); tree.bind("<Double-1>", lambda e: self.load_to_edit(e, fields)); return {"fields": fields, "tree": tree}

    def build_finance_ui(self, parent):
        stats_f = tk.Frame(parent, bg="#ecf0f1", pady=10); stats_f.pack(fill="x", padx=10, pady=5)
        self.lbl_total_agreed = tk.Label(stats_f, text="إجمالي الاتفاقات: 0.00", font=self.font_bold, fg="#2c3e50", bg="#ecf0f1"); self.lbl_total_agreed.pack(side="right", padx=20)
        self.lbl_total_paid = tk.Label(stats_f, text="إجمالي المحصل: 0.00", font=self.font_bold, fg="#27ae60", bg="#ecf0f1"); self.lbl_total_paid.pack(side="right", padx=20)
        self.lbl_total_remain = tk.Label(stats_f, text="الديون المتبقية: 0.00", font=self.font_bold, fg="#c0392b", bg="#ecf0f1"); self.lbl_total_remain.pack(side="right", padx=20)
        
        search_f = tk.Frame(parent, bg="#f4f7f6"); search_f.pack(fill="x", padx=10, pady=5)
        self.fin_search_var = tk.StringVar(); self.fin_search_var.trace("w", lambda *a: self.update_finance_table())
        tk.Label(search_f, text="بحث في المالية:", font=self.font_main, bg="#f4f7f6").pack(side="right", padx=5)
        self.fin_search_ent = tk.Entry(search_f, textvariable=self.fin_search_var, width=30, font=self.font_main, justify="right"); self.fin_search_ent.pack(side="right", padx=5)
        
        f = tk.LabelFrame(parent, text=" تسجيل دفعة جديدة ", font=self.font_header, bg="white", pady=15); f.pack(fill="x", padx=10, pady=10)
        self.fin_ent_agreed = tk.Entry(f, width=15, justify="center", font=self.font_bold, fg="blue"); self.fin_ent_pay = tk.Entry(f, width=15, justify="center", font=self.font_bold)
        tk.Label(f, text="الاتفاق الكلي:", font=self.font_main).grid(row=0, column=0, padx=5); self.fin_ent_agreed.grid(row=0, column=1, padx=5)
        tk.Label(f, text="دفعة جديدة:", font=self.font_main).grid(row=0, column=2, padx=5); self.fin_ent_pay.grid(row=0, column=3, padx=5)
        tk.Button(f, text="💵 إضافة دفعة", bg="#27ae60", fg="white", command=self.add_payment, width=15, font=self.font_bold).grid(row=0, column=4, padx=10)
        tk.Button(f, text="🔍 كشف حساب وتعديل", bg="#34495e", fg="white", command=self.open_statement_from_finance, font=self.font_bold).grid(row=0, column=5, padx=10)
        
        self.fin_tree = ttk.Treeview(parent, columns=("4","3","2","1"), show="headings")
        for i, h in zip("4321", ["المتبقي", "إجمالي المدفوع", "الموكل", "رقم الملف"]): self.fin_tree.heading(i, text=h); self.fin_tree.column(i, anchor="center")
        self.fin_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.fin_tree.tag_configure('paid_full', background='#d1e7dd'); self.fin_tree.tag_configure('debt', background='#f8d7da')
        self.fin_tree.bind("<<TreeviewSelect>>", self.on_finance_select)

    def open_history_window(self, target):
        win = tk.Toplevel(self.root)
        win.title(f"سجل دفعات: {target.get('moakal')}")
        win.geometry("600x650")
        win.configure(bg="#f4f7f6")
        win.grab_set()

        tk.Label(win, text="للتعديل: اختر الدفعة، اكتب المبلغ الجديد، ثم اضغط حفظ", 
                 font=(self.main_font_name, 11), bg="#f4f7f6", fg="#7f8c8d").pack(pady=5)

        h_tree = ttk.Treeview(win, columns=("a", "d"), show="headings", height=10)
        h_tree.heading("d", text="تاريخ الدفع"); h_tree.heading("a", text="المبلغ (دج)")
        h_tree.column("a", anchor="center", width=150); h_tree.column("d", anchor="center", width=250)
        h_tree.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh_h_tree():
            h_tree.delete(*h_tree.get_children())
            for i, p in enumerate(target.get('payments_list', [])):
                h_tree.insert("", "end", iid=str(i), values=(f"{float(p.get('amount')):,.2f}", p.get('date')))

        refresh_h_tree()

        edit_frame = tk.LabelFrame(win, text=" إدارة الدفعة المختارة ", font=self.font_bold, bg="#f4f7f6", pady=10)
        edit_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(edit_frame, text="المبلغ الجديد:", bg="#f4f7f6", font=self.font_main).grid(row=0, column=0, padx=5)
        new_amt_ent = tk.Entry(edit_frame, font=self.font_bold, width=15, justify="center")
        new_amt_ent.grid(row=0, column=1, padx=5)

        def update_selected_payment():
            sel = h_tree.selection()
            if not sel: messagebox.showwarning("تنبيه", "يرجى اختيار دفعة أولاً"); return
            try:
                idx = int(sel[0])
                new_val = float(new_amt_ent.get())
                target['payments_list'][idx]['amount'] = new_val
                self.save_to_json(); self.update_finance_table(); refresh_h_tree()
                new_amt_ent.delete(0, tk.END)
                messagebox.showinfo("تم", "تم التعديل بنجاح")
            except ValueError: messagebox.showerror("خطأ", "أدخل رقم صحيح")

        def delete_selected_payment():
            sel = h_tree.selection()
            if not sel: return
            if messagebox.askyesno("تأكيد", "حذف هذه الدفعة نهائياً؟"):
                idx = int(sel[0])
                target['payments_list'].pop(idx)
                self.save_to_json(); self.update_finance_table(); refresh_h_tree()

        tk.Button(edit_frame, text="📝 حفظ التعديل", bg="#f39c12", fg="white", font=self.font_bold, command=update_selected_payment).grid(row=0, column=2, padx=5)
        tk.Button(edit_frame, text="🗑️ حذف الدفعة", bg="#e74c3c", fg="white", font=self.font_bold, command=delete_selected_payment).grid(row=0, column=3, padx=5)

        btn_f = tk.Frame(win, bg="#f4f7f6")
        btn_f.pack(fill="x", pady=10)
        tk.Button(btn_f, text="📄 طباعة PDF", bg="#2980b9", fg="white", font=self.font_bold, command=lambda: self.print_client_statement(target)).pack(side="right", padx=20)
        tk.Button(btn_f, text="❌ إغلاق", bg="#95a5a6", fg="white", font=self.font_bold, command=win.destroy).pack(side="left", padx=20)

    # --- الدوال المساعدة الأخرى ---

    def update_roles_by_sec(self, event, fields, mode):
        sec_val = fields["sec"].get()
        if sec_val in ["جنحة", "جناية", "مخالفة", "تحقيق", "غرفة الاتهام"]:
            new_roles = self.roles_criminal; new_outcomes = self.outcomes_criminal
        elif mode == "appeals":
            new_roles = self.roles_appeals; new_outcomes = self.outcomes_general
        else:
            new_roles = self.roles_civil_admin; new_outcomes = self.outcomes_general
        fields["m_role"]['values'] = new_roles; fields["k_role"]['values'] = new_roles
        fields["status"]['values'] = new_outcomes; fields["m_role"].set(new_roles[0])

    def save_case(self, fields, mode):
        d = {k: v.get().strip() for k, v in fields.items()}; d["type"] = mode
        if not d["num"]: return
        if self.editing_index is not None:
            old = self.cases_list[self.editing_index]; d["total_agreed"] = old.get("total_agreed", 0); d["payments_list"] = old.get("payments_list", [])
            d["final_type"] = old.get("final_type", ""); d["final_num"] = old.get("final_num", ""); d["final_date"] = old.get("final_date", "")
            self.cases_list[self.editing_index] = d; self.editing_index = None
        else: d["total_agreed"] = 0; d["payments_list"] = []; d["final_type"] = ""; d["final_num"] = ""; d["final_date"] = ""; self.cases_list.append(d)
        self.save_to_json(); self.refresh_table()
        messagebox.showinfo("تم", "تم الحفظ بنجاح")

    def refresh_table(self):
        td = datetime.now().strftime("%d/%m/%Y"); tm = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        c_today = 0; c_tomorrow = 0
        for k in self.tabs: self.tabs[k]["data"]["tree"].delete(*self.tabs[k]["data"]["tree"].get_children())
        self.archive_data["tree"].delete(*self.archive_data["tree"].get_children())
        for c in sorted(self.cases_list, key=lambda x: self.parse_date(x.get('date'))):
            dt = str(c.get('date','')); status = c.get('status', '')
            if status in ["حكم نهائي", "محكومة"]:
                f_num = c.get('final_num','') if c.get('final_num','') else c.get('index_num','')
                self.archive_data["tree"].insert("", "end", values=(c.get('final_date',''), f_num, c.get('final_type',''), c.get('action',''), status, dt, c.get('khasm',''), c.get('moakal',''), f"{c.get('lvl','')} / {c.get('sec','')}", f"{c.get('num','')}/{c.get('year','')}"))
            else:
                k = c.get("type")
                if k in self.tabs:
                    tr = self.tabs[k]["data"]["tree"]; tag = ('today',) if dt == td else (('tomorrow',) if dt == tm else ())
                    if dt == td: c_today += 1
                    elif dt == tm: c_tomorrow += 1
                    tr.insert("", "end", values=(c.get('action',''), status, dt, c.get('khasm',''), c.get('moakal',''), f"{c.get('lvl','')} / {c.get('sec','')}", f"{c.get('num','')}/{c.get('year','')}"), tags=tag)
        self.lbl_today.config(text=f"جلسات اليوم: {c_today}"); self.lbl_tomorrow.config(text=f"جلسات الغد: {c_tomorrow}"); self.update_finance_table()

    def update_finance_table(self):
        self.fin_tree.delete(*self.fin_tree.get_children()); q = self.fin_search_var.get().lower(); t_agreed = t_paid = t_remain = 0
        for c in sorted(self.cases_list, key=lambda x: str(x.get('num'))):
            p_sum = sum(float(p.get('amount', 0)) for p in c.get('payments_list', [])); agreed = float(c.get('total_agreed', 0)); remain = agreed - p_sum; t_agreed += agreed; t_paid += p_sum; t_remain += remain
            if q in str(c.get('moakal','')).lower() or q in str(c.get('num','')).lower():
                tag = 'paid_full' if remain <= 0 and agreed > 0 else 'debt'
                self.fin_tree.insert("", "end", values=(f"{remain:,.2f}", f"{p_sum:,.2f}", c.get('moakal'), f"{c.get('num')}/{c.get('year')}"), tags=(tag,))
        self.lbl_total_agreed.config(text=f"إجمالي الاتفاقات: {t_agreed:,.2f} دج"); self.lbl_total_paid.config(text=f"إجمالي المحصل: {t_paid:,.2f} دج"); self.lbl_total_remain.config(text=f"الديون المتبقية: {t_remain:,.2f} دج")

    def on_finance_select(self, e):
        sel = self.fin_tree.selection()
        if sel:
            v = self.fin_tree.item(sel[0])['values'][3].split('/')
            t = next((c for c in self.cases_list if str(c.get('num'))==v[0] and str(c.get('year'))==v[1]), None)
            if t: self.fin_ent_agreed.delete(0, tk.END); self.fin_ent_agreed.insert(0, str(t.get('total_agreed', 0)))

    def add_payment(self):
        sel = self.fin_tree.selection()
        if not sel: messagebox.showwarning("تنبيه", "اختر ملفاً أولاً"); return
        v = self.fin_tree.item(sel[0])['values'][3].split('/')
        t = next((c for c in self.cases_list if str(c.get('num'))==v[0] and str(c.get('year'))==v[1]), None)
        if t:
            try:
                t['total_agreed'] = float(self.fin_ent_agreed.get() or 0); amt = float(self.fin_ent_pay.get() or 0)
                if amt > 0: t['payments_list'].append({"amount": amt, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})
                self.save_to_json(); self.update_finance_table(); self.fin_ent_pay.delete(0, tk.END)
                messagebox.showinfo("تم", "تم تسجيل الدفعة")
            except: messagebox.showerror("خطأ", "بيانات غير صحيحة")

    def open_statement_from_finance(self):
        sel = self.fin_tree.selection()
        if sel:
            v = self.fin_tree.item(sel[0])['values'][3].split('/')
            t = next((c for c in self.cases_list if str(c.get('num'))==v[0] and str(c.get('year'))==v[1]), None)
            if t: self.open_history_window(t)
        else: messagebox.showwarning("تنبيه", "يرجى اختيار ملف من الجدول")

    def build_archive_ui(self, parent):
        f_top = tk.LabelFrame(parent, text=" تسجيل بيانات السند القضائي النهائي ", font=self.font_header, bg="#ecf0f1", padx=10, pady=10); f_top.pack(fill="x", padx=10, pady=5)
        self.arch_fields = {}
        tk.Label(f_top, text="نوع القرار/الحالة:", bg="#ecf0f1", font=self.font_main).grid(row=0, column=0)
        self.arch_fields["type"] = ttk.Combobox(f_top, values=["حكم محكمة", "قرار مجلس", "قرار محكمة عليا", "قرار مجلس دولة"], width=15, font=self.font_main, justify="right"); self.arch_fields["type"].grid(row=0, column=1, padx=5)
        tk.Label(f_top, text="رقم الفهرس:", bg="#ecf0f1", font=self.font_main).grid(row=0, column=2); self.arch_fields["num"] = tk.Entry(f_top, width=15, font=self.font_main, justify="center"); self.arch_fields["num"].grid(row=0, column=3, padx=5)
        tk.Label(f_top, text="تاريخ الصدور:", bg="#ecf0f1", font=self.font_main).grid(row=0, column=4); self.arch_fields["date"] = tk.Entry(f_top, width=15, font=self.font_main, justify="center"); self.arch_fields["date"].grid(row=0, column=5, padx=5)
        tk.Button(f_top, text="💾 حفظ التفاصيل", command=self.save_archive_details, bg="#2c3e50", fg="white", font=self.font_bold).grid(row=0, column=6, padx=15)
        tree = ttk.Treeview(parent, columns=("10","9","8","7","6","5","4","3","2","1"), show="headings", height=20)
        headers = [("10", "تاريخ الصدور"), ("9", "رقم الفهرس"), ("8", "نوع القرار"), ("7", "الملاحظات"), ("6", "الحالة"), ("5", "تاريخ الحكم"), ("4", "الخصم"), ("3", "الموكل"), ("2", "الجهة/النوع"), ("1", "الملف")]
        for i, h in headers: tree.heading(i, text=h); tree.column(i, anchor="center", width=110)
        tree.pack(fill="both", expand=True, padx=10, pady=5); tree.bind("<<TreeviewSelect>>", self.on_archive_select); return {"tree": tree}

    def on_archive_select(self, e):
        sel = self.archive_data["tree"].selection()
        if sel:
            v = self.archive_data["tree"].item(sel[0])['values']
            self.arch_fields["date"].delete(0, tk.END); self.arch_fields["date"].insert(0, str(v[0]))
            self.arch_fields["num"].delete(0, tk.END); self.arch_fields["num"].insert(0, str(v[1]))
            self.arch_fields["type"].set(str(v[2]))

    def save_archive_details(self):
        sel = self.archive_data["tree"].selection()
        if not sel: return
        v = self.archive_data["tree"].item(sel[0])['values']
        for c in self.cases_list:
            if str(c.get('num')) == str(v[9]).split('/')[0]:
                c["final_type"] = self.arch_fields["type"].get(); c["final_num"] = self.arch_fields["num"].get(); c["final_date"] = self.arch_fields["date"].get(); break
        self.save_to_json(); self.refresh_table(); messagebox.showinfo("تم", "تم تحديث بيانات الأرشيف")

    def handle_enter_navigation(self, event):
        focused = self.root.focus_get()
        if focused == self.search_entry: self.execute_global_search(); return
        try:
            current_tab_idx = self.notebook.index(self.notebook.select()); tab_keys = list(self.tabs.keys())
            if current_tab_idx < len(tab_keys):
                mode = tab_keys[current_tab_idx]; fields = self.tabs[mode]["data"]["fields"]
                order = ["num", "year", "index_num", "sec", "moakal", "m_role", "khasm", "k_role", "expert", "date", "status", "lvl", "action"]
                widgets = [fields[k] for k in order if k in fields]
                if focused in widgets:
                    idx = widgets.index(focused)
                    if idx == len(widgets)-1: self.save_case(fields, mode); widgets[0].focus_set()
                    else: widgets[idx+1].focus_set()
                    return "break"
        except: pass

    def execute_global_search(self):
        q = self.search_var.get().strip().lower()
        if not q: self.search_results_frame.pack_forget(); return
        self.search_results_frame.pack(fill="x", padx=10, pady=5, before=self.notebook); self.search_results_tree.delete(*self.search_results_tree.get_children())
        for c in sorted([x for x in self.cases_list if q in str(x).lower()], key=lambda x: self.parse_date(x.get('date'))):
            self.search_results_tree.insert("", "end", values=(c.get('action',''), c.get('type',''), c.get('status',''), c.get('date',''), c.get('khasm',''), c.get('moakal',''), c.get('sec',''), f"{c.get('num','')}/{c.get('year','')}"))

    def load_to_edit(self, e, fields):
        tr = e.widget; s = tr.selection()
        if s: self.trigger_edit_by_id(str(tr.item(s[0])['values'][6]).split('/')[0], fields)

    def trigger_edit_by_id(self, num, fields):
        for i, c in enumerate(self.cases_list):
            if str(c.get('num')) == str(num):
                self.editing_index = i
                for k, v in fields.items():
                    if k in c:
                        if isinstance(v, ttk.Combobox): v.set(c.get(k, ''))
                        else: v.delete(0, tk.END); v.insert(0, str(c.get(k, '')))
                break

    def load_from_search(self, e):
        sel = self.search_results_tree.selection()
        if sel:
            it = self.search_results_tree.item(sel[0])['values']
            for i, (k, tab) in enumerate(self.tabs.items()):
                if k == it[1]: self.notebook.select(i); self.trigger_edit_by_id(str(it[7]).split('/')[0], tab["data"]["fields"]); break

    def open_case_folder(self, fields):
        fld = f"{fields['num'].get()}_{fields['moakal'].get()}"; p = os.path.abspath(os.path.join(self.docs_dir, fld))
        if not os.path.exists(p): os.makedirs(p)
        os.startfile(p)

    def delete_case(self, mode):
        tr = self.tabs[mode]["data"]["tree"]; s = tr.selection()
        if s and messagebox.askyesno("تأكيد", "حذف الملف نهائياً؟"):
            v = tr.item(s[0])['values'][6].split('/'); self.cases_list = [c for c in self.cases_list if not (str(c.get('num'))==v[0] and str(c.get('year'))==v[1])]; self.save_to_json(); self.refresh_table()

    def parse_date(self, d):
        if not d: return datetime.max
        for f in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try: return datetime.strptime(str(d).strip(), f)
            except: continue
        return datetime.max

    def go_to_finance(self, fields):
        name = fields['moakal'].get(); num = fields['num'].get(); self.notebook.select(self.fin_tab); self.fin_search_var.set(name if name else num); self.root.after(200, self.select_first_fin_item)

    def select_first_fin_item(self):
        children = self.fin_tree.get_children()
        if children: self.fin_tree.selection_set(children[0]); self.fin_tree.focus(children[0]); self.fin_ent_pay.focus_set()

    def on_closing(self):
        if messagebox.askokcancel("خروج", "هل تريد إغلاق البرنامج؟"):
            self.root.destroy()

    def transfer_case_window(self):
        tr = self.tabs["study"]["data"]["tree"]; sel = tr.selection()
        if not sel: messagebox.showwarning("تنبيه", "يرجى اختيار ملف."); return
        v = tr.item(sel[0])['values'][6].split('/'); target_case = next((c for c in self.cases_list if str(c.get('num'))==v[0] and str(c.get('year'))==v[1]), None)
        if target_case:
            win = tk.Toplevel(self.root); win.title("تحويل الملف"); win.geometry("400x250"); win.grab_set()
            sections = [("القسم المدني", "civil"), ("القسم الجزائي", "criminal"), ("القسم الإداري", "admin"), ("قسم التنفيذ", "execution"), ("تبويب الطعون", "appeals")]
            cmb = ttk.Combobox(win, values=[s[0] for s in sections], state="readonly", font=self.font_main); cmb.set(sections[0][0]); cmb.pack(pady=20)
            
            def do_transfer():
                disp_name = cmb.get(); target_key = next(s[1] for s in sections if s[0] == disp_name)
                target_case["type"] = target_key; self.save_to_json(); self.refresh_table(); win.destroy()
                messagebox.showinfo("نجاح", f"تم تحويل الملف إلى {disp_name}")
            tk.Button(win, text="تأكيد التحويل", command=do_transfer, bg="#d35400", fg="white", font=self.font_bold).pack()

    def print_search_results(self):
        if not ARABIC_SUPPORT: 
            messagebox.showwarning("تنبيه", "مكتبة PDF غير مثبتة")
            return
            
        current_tab_idx = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(current_tab_idx, "text")
        
        # --- التعديل المخصص لتبويب الأتعاب والمالية لطباعة المعروض فقط ---
        if "الأتعاب" in tab_text:
            res_to_print = []
            for child in self.fin_tree.get_children():
                row_vals = self.fin_tree.item(child)['values']
                res_to_print.append({
                    "remain": row_vals[0],
                    "paid": row_vals[1],
                    "moakal": row_vals[2],
                    "file_num": row_vals[3]
                })
            
            if not res_to_print:
                messagebox.showinfo("تنبيه", "الجدول فارغ")
                return
            
            try:
                pdf = FPDF(orientation='P')
                pdf.add_page()
                pdf.add_font('TimesAr', '', "C:/Windows/Fonts/times.ttf", uni=True)
                pdf.set_font('TimesAr', '', 16)
                pdf.cell(0, 10, self.ar("تقرير الحالة المالية للملفات المعروضة"), ln=True, align='C')
                pdf.set_font('TimesAr', '', 12)
                pdf.cell(0, 10, self.ar(f"تاريخ التقرير: {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C')
                pdf.ln(10)
                
                cols = [(40, "المتبقي"), (40, "إجمالي المحصل"), (70, "اسم الموكل"), (40, "رقم الملف")]
                pdf.set_fill_color(230)
                pdf.set_font('TimesAr', '', 13)
                for w, t in cols:
                    pdf.cell(w, 10, self.ar(t), 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_font('TimesAr', '', 12)
                for item in res_to_print:
                    pdf.cell(40, 10, str(item['remain']), 1, 0, 'C')
                    pdf.cell(40, 10, str(item['paid']), 1, 0, 'C')
                    pdf.cell(70, 10, self.ar(item['moakal']), 1, 0, 'R')
                    pdf.cell(40, 10, str(item['file_num']), 1, 1, 'C')
                
                fn = f"Finance_Report_{datetime.now().strftime('%H%M%S')}.pdf"
                pdf.output(fn); os.startfile(fn)
                return
            except Exception as e:
                messagebox.showerror("خطأ", str(e)); return

        # --- طباعة الجداول الأخرى ---
        q = self.search_var.get().strip().lower()
        if q: 
            res_data = [x for x in self.cases_list if q in str(x).lower()]
            report_title = f"نتائج البحث عن: {q}"
        elif "الأرشيف" in tab_text: 
            res_data = [x for x in self.cases_list if x.get('status') in ["حكم نهائي", "محكومة"]]
            report_title = "سجل أرشيف القضايا"
        else:
            tab_keys = list(self.tabs.keys())
            if current_tab_idx < len(tab_keys):
                mode = tab_keys[current_tab_idx]
                res_data = [x for x in self.cases_list if x.get('type') == mode and x.get('status') not in ["حكم نهائي", "محكومة"]]
                report_title = f"جدول قضايا: {self.tabs[mode]['title']}"
            else:
                res_data = [x for x in self.cases_list if x.get('status') not in ["حكم نهائي", "محكومة"]]
                report_title = "الجدول العام للمكتب"

        if not res_data: 
            messagebox.showinfo("معلومة", "لا توجد بيانات للطباعة")
            return

        try:
            pdf = FPDF(orientation='L'); pdf.add_page()
            pdf.add_font('TimesAr', '', "C:/Windows/Fonts/times.ttf", uni=True); pdf.set_font('TimesAr', '', 14)
            pdf.cell(0, 10, self.ar(f"{report_title} - {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C'); pdf.ln(5)
            cols = [(55, "الملاحظات"), (25, "مآل"), (30, "الجلسة"), (45, "الخصم"), (45, "الموكل"), (45, "الجهة"), (30, "الملف")]
            pdf.set_fill_color(220); pdf.set_font('TimesAr', '', 11)
            for w, t in cols: pdf.cell(w, 10, self.ar(t), 1, 0, 'C', True)
            pdf.ln(); pdf.set_font('TimesAr', '', 10)
            for c in sorted(res_data, key=lambda x: self.parse_date(x.get('date'))):
                pdf.cell(55, 10, self.ar(c.get('action','')[:40]), 1, 0, 'R')
                pdf.cell(25, 10, self.ar(c.get('status','')), 1, 0, 'C')
                pdf.cell(30, 10, str(c.get('date','')), 1, 0, 'C')
                pdf.cell(45, 10, self.ar(c.get('khasm','')), 1, 0, 'R')
                pdf.cell(45, 10, self.ar(c.get('moakal','')), 1, 0, 'R')
                pdf.cell(45, 10, self.ar(f"{c.get('lvl','')} / {c.get('sec','')}"), 1, 0, 'C')
                pdf.cell(30, 10, f"{c.get('num')}/{c.get('year')}", 1, 1, 'C')
            fn = f"Print_{datetime.now().strftime('%H%M%S')}.pdf"
            pdf.output(fn); os.startfile(fn)
        except Exception as e: 
            messagebox.showerror("خطأ", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = LawyerProApp(root)
    root.mainloop()