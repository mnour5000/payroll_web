import customtkinter as ctk
import tkinter as tk

from tkinter import filedialog, messagebox, ttk

import pandas as pd
import os
import re

from supabase import create_client, Client

import arabic_reshaper
from bidi.algorithm import get_display


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = "https://xnpiqugxderlogjyjiuz.supabase.co"

SUPABASE_KEY = (
    "sb_publishable_0ZTqx9KiG-hGJom2BApV5w_HaQvcnCu"
)

SUPABASE_TABLE = "mohamed_said"
LOGIN_LOG_TABLE = "login_logs"

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# RTL
# ============================================================

def rtl_text(text):

    if text is None:
        return ""

    text = str(text)

    if not text.strip():
        return text

    try:
        return get_display(
            arabic_reshaper.reshape(text)
        )

    except Exception:
        return text


def rtl_message(text):

    if text is None:
        return ""

    return "\u200f" + str(text)


# ============================================================
# SUPABASE LOG
# ============================================================

def log_user_action(username, action):

    try:

        supabase.table(
            LOGIN_LOG_TABLE
        ).insert(
            {
                "username": username,
                "action": action
            }
        ).execute()

    except Exception as e:

        print(
            "LOGIN LOG ERROR:",
            repr(e)
        )


# =========================================================
# إعداد المظهر
# =========================================================

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


# =========================================================
# دوال مساعدة
# =========================================================

def clean_text(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value).strip()

    if text.upper() in [
        "#N/A",
        "#NA",
        "N/A",
        "NA"
    ]:
        return "#N/A"

    return text


def is_na_value(value):

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    text = str(value).strip().upper()

    return text in [
        "",
        "#N/A",
        "#NA",
        "N/A",
        "NA",
        "NAN",
        "NONE",
        "NULL"
    ]


def clean_id(value):

    value = clean_text(value)

    if is_na_value(value):
        return ""

    arabic_numbers = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )

    value = value.translate(arabic_numbers)

    value = (
        value
        .replace(" ", "")
        .replace("\u00a0", "")
    )

    if value.endswith(".0"):
        value = value[:-2]

    return value


def clean_employee_number(value):

    value = clean_id(value)

    if not value:
        return ""

    try:

        if re.fullmatch(
            r"[+-]?\d+(?:\.\d+)?[eE][+-]?\d+",
            value
        ):

            number = float(value)

            if number.is_integer():
                return str(int(number))

            return str(number)

    except Exception:
        pass

    return value


def normalize_amount(value):

    if value is None:
        return 0.0

    try:

        if pd.isna(value):
            return 0.0

    except Exception:
        pass

    if isinstance(value, (int, float)):

        try:
            return float(value)

        except Exception:
            return 0.0

    value = clean_text(value)

    if is_na_value(value):
        return 0.0

    arabic_numbers = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )

    value = value.translate(arabic_numbers)

    value = (
        value
        .replace(",", "")
        .replace("،", "")
        .replace(" ", "")
        .replace("جنيه", "")
        .replace("جم", "")
    )

    try:

        return float(value)

    except Exception:

        return 0.0


def find_column(df, keywords):

    for col in df.columns:

        col_text = clean_text(col)

        if not col_text:
            continue

        for keyword in keywords:

            keyword_text = clean_text(keyword)

            if (
                keyword_text
                and keyword_text in col_text
            ):

                return col

    return None


def prepare_dataframe_columns(df):

    df = df.copy()

    cleaned_columns = []

    for col in df.columns:

        col_text = clean_text(col)

        if not col_text:
            col_text = "عمود_غير_مسمى"

        cleaned_columns.append(col_text)

    df.columns = cleaned_columns

    return df


def safe_sheet_name(name):

    name = clean_text(name)

    if not name:
        name = "غير محدد"

    name = re.sub(
        r'[\\/*?:\[\]]',
        "-",
        name
    )

    name = name[:31]

    if not name:
        name = "غير محدد"

    return name


def safe_row_to_text(row):

    values = []

    for value in row:

        value_text = clean_text(value)

        if value_text:
            values.append(value_text)

    return " ".join(values)


# ============================================================
# شاشة الدخول الاحترافية
# ============================================================

class LoginWindow(ctk.CTk):

    def __init__(self):

        super().__init__()

        # -------------------------------------------------
        # إعداد النافذة
        # -------------------------------------------------

        self.title(
            rtl_text("نظام فرز البيرول - تسجيل الدخول")
        )

        self.geometry("560x650")
        self.resizable(False, False)

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        # -------------------------------------------------
        # الخلفية الرئيسية
        # -------------------------------------------------

        self.configure(
            fg_color=(
                "#eef2f7",
                "#111827"
            )
        )

        # -------------------------------------------------
        # البطاقة الرئيسية
        # -------------------------------------------------

        self.login_frame = ctk.CTkFrame(
            self,
            width=440,
            height=570,
            corner_radius=22,
            fg_color=(
                "#ffffff",
                "#1f2937"
            ),
            border_width=1,
            border_color=(
                "#dbe3ec",
                "#374151"
            )
        )

        self.login_frame.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.login_frame.pack_propagate(False)

        # =================================================
        # الشعار
        # =================================================

        self.logo_label = ctk.CTkLabel(
            self.login_frame,
            text="⚙️",
            font=ctk.CTkFont(
                size=48
            )
        )

        self.logo_label.pack(
            pady=(28, 5)
        )

        # =================================================
        # العنوان
        # =================================================

        self.title_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "نظام فرز البيرول"
            ),
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            ),
            text_color=(
                "#14532d",
                "#86efac"
            )
        )

        self.title_label.pack(
            pady=(0, 5)
        )

        # =================================================
        # العنوان الفرعي
        # =================================================

        self.subtitle_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "منظومة فرز وتوزيع استمارات البيرول"
            ),
            font=ctk.CTkFont(
                size=14
            ),
            text_color=(
                "#64748b",
                "#cbd5e1"
            )
        )

        self.subtitle_label.pack(
            pady=(0, 8)
        )

        # =================================================
        # وصف النظام
        # =================================================

        self.description_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "تسجيل دخول آمن للوصول إلى منظومة التوزيع"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#94a3b8",
                "#9ca3af"
            )
        )

        self.description_label.pack(
            pady=(0, 22)
        )

        # =================================================
        # اسم المستخدم
        # =================================================

        self.username_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "اسم المستخدم"
            ),
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            anchor="e"
        )

        self.username_label.pack(
            padx=48,
            fill="x",
            pady=(0, 5)
        )

        self.username_entry = ctk.CTkEntry(
            self.login_frame,
            width=340,
            height=44,
            corner_radius=10,
            justify="center",
            font=ctk.CTkFont(
                size=14
            ),
            placeholder_text=rtl_text(
                "أدخل اسم المستخدم"
            )
        )

        self.username_entry.pack(
            pady=(0, 17)
        )

        # اسم المستخدم الافتراضي
        self.username_entry.insert(
            0,
            "mohamed_said"
        )

        # =================================================
        # كلمة المرور
        # =================================================

        self.password_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "كلمة المرور"
            ),
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            anchor="e"
        )

        self.password_label.pack(
            padx=48,
            fill="x",
            pady=(0, 5)
        )

        self.password_entry = ctk.CTkEntry(
            self.login_frame,
            width=340,
            height=44,
            corner_radius=10,
            justify="center",
            font=ctk.CTkFont(
                size=14
            ),
            show="*",
            placeholder_text=rtl_text(
                "أدخل كلمة المرور"
            )
        )

        self.password_entry.pack(
            pady=(0, 8)
        )

        # =================================================
        # إظهار كلمة المرور
        # =================================================

        self.show_password_var = tk.BooleanVar(
            value=False
        )

        self.show_password_check = ctk.CTkCheckBox(
            self.login_frame,
            text=rtl_text(
                "إظهار كلمة المرور"
            ),
            variable=self.show_password_var,
            command=self.toggle_password,
            font=ctk.CTkFont(
                size=12
            ),
            checkbox_width=20,
            checkbox_height=20
        )

        self.show_password_check.pack(
            pady=(0, 18)
        )

        # =================================================
        # زر الدخول
        # =================================================

        self.login_button = ctk.CTkButton(
            self.login_frame,
            text=rtl_text(
                "🔐  تسجيل الدخول"
            ),
            width=340,
            height=48,
            corner_radius=11,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            fg_color=(
                "#15803d",
                "#16a34a"
            ),
            hover_color=(
                "#166534",
                "#15803d"
            ),
            command=self.login
        )

        self.login_button.pack(
            pady=(0, 12)
        )

        # =================================================
        # حالة الاتصال
        # =================================================

        self.status_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "● النظام جاهز لتسجيل الدخول"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#16a34a",
                "#4ade80"
            )
        )

        self.status_label.pack(
            pady=(0, 18)
        )

        # =================================================
        # خط فاصل
        # =================================================

        self.separator = ctk.CTkFrame(
            self.login_frame,
            height=1,
            fg_color=(
                "#e2e8f0",
                "#374151"
            )
        )

        self.separator.pack(
            fill="x",
            padx=48,
            pady=(0, 12)
        )

        # =================================================
        # حقوق التصميم
        # =================================================

        self.footer_label = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "تصميم وتطوير: محمد سيد"
            ),
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=(
                "#64748b",
                "#cbd5e1"
            )
        )

        self.footer_label.pack(
            pady=(0, 2)
        )

        self.footer_subtitle = ctk.CTkLabel(
            self.login_frame,
            text=rtl_text(
                "نظام فرز وتوزيع استمارات البيرول"
            ),
            font=ctk.CTkFont(
                size=14
            ),
            text_color=(
                "#94a3b8",
                "#9ca3af"
            )
        )

        self.footer_subtitle.pack()

        # =================================================
        # Enter
        # =================================================

        self.bind(
            "<Return>",
            lambda event: self.login()
        )

        # =================================================
        # التركيز
        # =================================================

        self.username_entry.focus()

    # =====================================================
    # إظهار / إخفاء كلمة المرور
    # =====================================================

    def toggle_password(self):

        if self.show_password_var.get():

            self.password_entry.configure(
                show=""
            )

        else:

            self.password_entry.configure(
                show="*"
            )

    # =====================================================
    # تسجيل الدخول
    # =====================================================

    def login(self):

        username = (
            self.username_entry
            .get()
            .strip()
        )

        password = (
            self.password_entry
            .get()
        )

        # -------------------------------------------------
        # التحقق من اسم المستخدم
        # -------------------------------------------------

        if not username:

            self.login_failed(
                "برجاء إدخال اسم المستخدم."
            )

            return

        # -------------------------------------------------
        # التحقق من كلمة المرور
        # -------------------------------------------------

        if not password:

            self.login_failed(
                "برجاء إدخال كلمة المرور."
            )

            return

        # -------------------------------------------------
        # حالة الانتظار
        # -------------------------------------------------

        self.login_button.configure(
            state="disabled",
            text=rtl_text(
                "⏳  جاري التحقق..."
            )
        )

        self.status_label.configure(
            text=rtl_text(
                "● جاري الاتصال بقاعدة بيانات المستخدمين..."
            ),
            text_color=(
                "#d97706",
                "#fbbf24"
            )
        )

        self.update_idletasks()

        try:

            # =================================================
            # جلب المستخدمين من Supabase
            # =================================================

            response = (
                supabase
                .table(SUPABASE_TABLE)
                .select(
                    "username,password,status,role"
                )
                .execute()
            )

            users = (
                response.data
                or []
            )

            user = None

            # -------------------------------------------------
            # البحث مع إزالة المسافات
            # -------------------------------------------------

            for item in users:

                db_username_check = str(
                    item.get(
                        "username",
                        ""
                    )
                ).strip()

                if db_username_check == username:

                    user = item

                    break

            # -------------------------------------------------
            # المستخدم غير موجود
            # -------------------------------------------------

            if user is None:

                self.login_failed(
                    "اسم المستخدم أو كلمة المرور غير صحيحة."
                )

                return

            # =================================================
            # بيانات المستخدم
            # =================================================

            db_username = str(
                user.get(
                    "username",
                    ""
                )
            ).strip()

            db_password = str(
                user.get(
                    "password",
                    ""
                )
            )

            db_status = str(
                user.get(
                    "status",
                    "active"
                )
            ).strip().lower()

            db_role = str(
                user.get(
                    "role",
                    "reviewer"
                )
            ).strip().lower()

            # =================================================
            # التحقق من حالة الحساب
            # =================================================

            if db_status not in (
                "",
                "active"
            ):

                self.login_failed(
                    "هذا الحساب غير نشط."
                )

                return

            # =================================================
            # التحقق من كلمة المرور
            # =================================================

            if password != db_password:

                self.login_failed(
                    "اسم المستخدم أو كلمة المرور غير صحيحة."
                )

                return

            # =================================================
            # الصلاحية
            # =================================================

            if db_role not in (
                "admin",
                "reviewer",
                "user"
            ):

                db_role = "reviewer"

            # =================================================
            # تسجيل الدخول في السجل
            # =================================================

            log_user_action(
                db_username,
                "login"
            )

            # =================================================
            # نجاح الدخول
            # =================================================

            self.login_button.configure(
                text=rtl_text(
                    "✓  تم تسجيل الدخول"
                )
            )

            self.status_label.configure(
                text=rtl_text(
                    "● تم التحقق بنجاح — جاري فتح النظام..."
                ),
                text_color=(
                    "#16a34a",
                    "#4ade80"
                )
            )

            self.after(
                350,
                lambda: self.open_main_app(
                    db_username,
                    db_role
                )
            )

        except Exception as err:

            self.login_button.configure(
                state="normal",
                text=rtl_text(
                    "🔐  تسجيل الدخول"
                )
            )

            self.status_label.configure(
                text=rtl_text(
                    "● تعذر الاتصال بقاعدة البيانات"
                ),
                text_color=(
                    "#dc2626",
                    "#f87171"
                )
            )

            messagebox.showerror(
                rtl_text(
                    "خطأ في الاتصال"
                ),
                rtl_message(
                    "تعذر الاتصال بقاعدة بيانات المستخدمين.\n\n"
                    f"تفاصيل الخطأ:\n{err}"
                ),
                parent=self
            )

    # =====================================================
    # فشل تسجيل الدخول
    # =====================================================

    def login_failed(self, message):

        self.login_button.configure(
            state="normal",
            text=rtl_text(
                "🔐  تسجيل الدخول"
            )
        )

        self.status_label.configure(
            text=rtl_text(
                "● يرجى التحقق من بيانات الدخول"
            ),
            text_color=(
                "#dc2626",
                "#f87171"
            )
        )

        messagebox.showwarning(
            rtl_text(
                "تنبيه تسجيل الدخول"
            ),
            rtl_message(
                message
            ),
            parent=self
        )

        self.password_entry.focus()

        self.password_entry.select_range(
            0,
            tk.END
        )

    # =====================================================
    # فتح البرنامج الرئيسي
    # =====================================================

    def open_main_app(
        self,
        username,
        role
    ):

        self.destroy()

        app = ctk.CTk()

        app.title(
            rtl_text(
                "نظام فرز البيرول"
            )
        )

        app.geometry(
            "1200x750"
        )

        app.minsize(
            1000,
            650
        )

        app.configure(
            fg_color=(
                "#f1f5f9",
                "#111827"
            )
        )

        PayrollSplitterFrame(
            app,
            logged_username=username,
            user_role=role
        )

        app.mainloop()

    # =====================================================
    # إغلاق البرنامج
    # =====================================================

    def close_application(self):

        try:

            self.destroy()

        except Exception:

            pass


# =========================================================
# البرنامج الرئيسي - واجهة احترافية
# =========================================================

class PayrollSplitterFrame(ctk.CTkFrame):

    def __init__(
        self,
        master,
        logged_username="",
        user_role="reviewer"
    ):

        super().__init__(
            master,
            fg_color=(
                "#f1f5f9",
                "#111827"
            )
        )

        self.master = master

        self.logged_username = (
            logged_username or ""
        )

        self.user_role = str(
            user_role or "reviewer"
        ).strip().lower()

        # -------------------------------------------------
        # مسارات الملفات
        # -------------------------------------------------

        self.db_file_path = None
        self.input_file_path = None

        self.pack(
            fill="both",
            expand=True
        )

        # =================================================
        # الشريط العلوي
        # =================================================

        self.header = ctk.CTkFrame(
            self,
            height=92,
            corner_radius=0,
            fg_color=(
                "#166534",
                "#14532d"
            )
        )

        self.header.pack(
            fill="x"
        )

        self.header.pack_propagate(False)

        # -------------------------------------------------
        # اسم النظام
        # -------------------------------------------------

        self.header_title = ctk.CTkLabel(
            self.header,
            text=rtl_text(
                "⚙️  نظام فرز البيرول"
            ),
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            ),
            text_color="white"
        )

        self.header_title.pack(
            side="right",
            padx=30,
            pady=(15, 0)
        )

        self.header_subtitle = ctk.CTkLabel(
            self.header,
            text=rtl_text(
                "منظومة فرز وتوزيع استمارات البيرول الحكومي"
            ),
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#dcfce7"
        )

        self.header_subtitle.pack(
            side="right",
            padx=32,
            pady=(0, 12)
        )

        # -------------------------------------------------
        # بيانات المستخدم
        # -------------------------------------------------

        role_text = (
            "مدير"
            if self.user_role == "admin"
            else
            "مراجع"
            if self.user_role == "reviewer"
            else
            "مستخدم"
        )

        self.header_user = ctk.CTkLabel(
            self.header,
            text=rtl_text(
                f"👤 {self.logged_username}  |  {role_text}"
            ),
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color="#f0fdf4"
        )

        self.header_user.pack(
            side="left",
            padx=30,
            pady=32
        )

        # =================================================
        # المحتوى الرئيسي
        # =================================================

        self.content = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=24
        )

        # =================================================
        # عنوان الصفحة
        # =================================================

        self.page_title = ctk.CTkLabel(
            self.content,
            text=rtl_text(
                "تهيئة وفرز وتوزيع استمارات البيرول"
            ),
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            ),
            anchor="e"
        )

        self.page_title.pack(
            fill="x",
            pady=(0, 4)
        )

        self.page_description = ctk.CTkLabel(
            self.content,
            text=rtl_text(
                "اختر الملفات المطلوبة ثم شغّل عملية الفرز والتوزيع التلقائي"
            ),
            font=ctk.CTkFont(
                size=12
            ),
            text_color=(
                "#64748b",
                "#94a3b8"
            ),
            anchor="e"
        )

        self.page_description.pack(
            fill="x",
            pady=(0, 20)
        )

        # =================================================
        # بطاقات اختيار الملفات
        # =================================================

        self.files_container = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        self.files_container.pack(
            fill="x"
        )

        self.files_container.grid_columnconfigure(
            0,
            weight=1
        )

        self.files_container.grid_columnconfigure(
            1,
            weight=1
        )

        # =================================================
        # بطاقة قاعدة البيانات
        # =================================================

        self.db_card = ctk.CTkFrame(
            self.files_container,
            corner_radius=16,
            fg_color=(
                "#ffffff",
                "#1f2937"
            ),
            border_width=1,
            border_color=(
                "#dbe3ec",
                "#374151"
            )
        )

        self.db_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        self.db_icon = ctk.CTkLabel(
            self.db_card,
            text="🗄️",
            font=ctk.CTkFont(
                size=34
            )
        )

        self.db_icon.pack(
            pady=(18, 4)
        )

        self.db_title = ctk.CTkLabel(
            self.db_card,
            text=rtl_text(
                "قاعدة البيانات الأساسية"
            ),
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.db_title.pack(
            pady=(0, 3)
        )

        self.db_hint = ctk.CTkLabel(
            self.db_card,
            text=rtl_text(
                "ملف بيانات الموظفين الأساسي"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#64748b",
                "#94a3b8"
            )
        )

        self.db_hint.pack(
            pady=(0, 10)
        )

        self.lbl_db = ctk.CTkLabel(
            self.db_card,
            text=rtl_text(
                "لم يتم اختيار الملف"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#94a3b8",
                "#9ca3af"
            ),
            wraplength=330
        )

        self.lbl_db.pack(
            padx=20,
            pady=(0, 12)
        )

        self.btn_db = ctk.CTkButton(
            self.db_card,
            text=rtl_text(
                "📁  اختيار قاعدة البيانات"
            ),
            height=40,
            corner_radius=9,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            fg_color=(
                "#2563eb",
                "#3b82f6"
            ),
            hover_color=(
                "#1d4ed8",
                "#2563eb"
            ),
            command=self.select_db_file
        )

        self.btn_db.pack(
            padx=20,
            pady=(0, 18),
            fill="x"
        )

        # =================================================
        # بطاقة شيت التوزيع
        # =================================================

        self.input_card = ctk.CTkFrame(
            self.files_container,
            corner_radius=16,
            fg_color=(
                "#ffffff",
                "#1f2937"
            ),
            border_width=1,
            border_color=(
                "#dbe3ec",
                "#374151"
            )
        )

        self.input_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        self.input_icon = ctk.CTkLabel(
            self.input_card,
            text="📋",
            font=ctk.CTkFont(
                size=34
            )
        )

        self.input_icon.pack(
            pady=(18, 4)
        )

        self.input_title = ctk.CTkLabel(
            self.input_card,
            text=rtl_text(
                "شيت توزيع الاستمارة"
            ),
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.input_title.pack(
            pady=(0, 3)
        )

        self.input_hint = ctk.CTkLabel(
            self.input_card,
            text=rtl_text(
                "شيت التوزيع المجمع للمكافآت"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#64748b",
                "#94a3b8"
            )
        )

        self.input_hint.pack(
            pady=(0, 10)
        )

        self.lbl_input = ctk.CTkLabel(
            self.input_card,
            text=rtl_text(
                "لم يتم اختيار الملف"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#94a3b8",
                "#9ca3af"
            ),
            wraplength=330
        )

        self.lbl_input.pack(
            padx=20,
            pady=(0, 12)
        )

        self.btn_input = ctk.CTkButton(
            self.input_card,
            text=rtl_text(
                "📥  اختيار شيت التوزيع"
            ),
            height=40,
            corner_radius=9,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            fg_color=(
                "#0f766e",
                "#14b8a6"
            ),
            hover_color=(
                "#115e59",
                "#0f766e"
            ),
            command=self.select_input_file
        )

        self.btn_input.pack(
            padx=20,
            pady=(0, 18),
            fill="x"
        )

        # =================================================
        # منطقة التشغيل
        # =================================================

        self.action_frame = ctk.CTkFrame(
            self.content,
            corner_radius=16,
            fg_color=(
                "#ffffff",
                "#1f2937"
            ),
            border_width=1,
            border_color=(
                "#dbe3ec",
                "#374151"
            )
        )

        self.action_frame.pack(
            fill="x",
            pady=18
        )

        self.action_title = ctk.CTkLabel(
            self.action_frame,
            text=rtl_text(
                "⚡ تنفيذ عملية الفرز والتوزيع"
            ),
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.action_title.pack(
            pady=(14, 4)
        )

        self.action_hint = ctk.CTkLabel(
            self.action_frame,
            text=rtl_text(
                "سيتم الاعتماد على رقم الصرف في المطابقة وتحديد السحب الجديد تلقائيًا"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=(
                "#64748b",
                "#94a3b8"
            )
        )

        self.action_hint.pack(
            pady=(0, 10)
        )

        self.btn_run = ctk.CTkButton(
            self.action_frame,
            text=rtl_text(
                "⚡  تشغيل الفرز والتوزيع التلقائي"
            ),
            width=420,
            height=50,
            corner_radius=11,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            fg_color=(
                "#15803d",
                "#16a34a"
            ),
            hover_color=(
                "#166534",
                "#15803d"
            ),
            command=self.process_payroll_splitting
        )

        self.btn_run.pack(
            pady=(0, 16)
        )

        # =================================================
        # أزرار الإدارة والخروج
        # =================================================

        self.bottom_actions = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        self.bottom_actions.pack(
            fill="x",
            pady=(0, 12)
        )

        if self.user_role == "admin":

            self.btn_users = ctk.CTkButton(
                self.bottom_actions,
                text=rtl_text(
                    "👥  إدارة المستخدمين"
                ),
                width=190,
                height=38,
                corner_radius=9,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold"
                ),
                fg_color=(
                    "#475569",
                    "#64748b"
                ),
                hover_color=(
                    "#334155",
                    "#475569"
                ),
                command=self.open_user_management
            )

            self.btn_users.pack(
                side="right"
            )

        self.btn_logout = ctk.CTkButton(
            self.bottom_actions,
            text=rtl_text(
                "🚪  تسجيل الخروج"
            ),
            width=170,
            height=38,
            corner_radius=9,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            fg_color=(
                "#b91c1c",
                "#dc2626"
            ),
            hover_color=(
                "#991b1b",
                "#b91c1c"
            ),
            command=self.logout
        )

        self.btn_logout.pack(
            side="left"
        )

        # =================================================
        # الملخص
        # =================================================

        self.summary_title = ctk.CTkLabel(
            self.content,
            text=rtl_text(
                "📊 ملخص نتائج التوزيع"
            ),
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            anchor="e"
        )

        self.summary_title.pack(
            fill="x",
            pady=(4, 8)
        )

        self.frame_summary = ctk.CTkFrame(
            self.content,
            corner_radius=14,
            fg_color=(
                "#ffffff",
                "#1f2937"
            ),
            border_width=1,
            border_color=(
                "#dbe3ec",
                "#374151"
            )
        )

        self.frame_summary.pack(
            fill="both",
            expand=True
        )

        # -------------------------------------------------
        # تنسيق Treeview
        # -------------------------------------------------

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except Exception:

            pass

        style.configure(
            "Payroll.Treeview",
            rowheight=34,
            font=(
                "Segoe UI",
                11
            ),
            borderwidth=0
        )

        style.configure(
            "Payroll.Treeview.Heading",
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            padding=8
        )

        style.map(
            "Payroll.Treeview",
            background=[
                ("selected", "#bbf7d0")
            ],
            foreground=[
                ("selected", "#14532d")
            ]
        )

        self.tree = ttk.Treeview(
            self.frame_summary,
            columns=(
                "category",
                "count",
                "total"
            ),
            show="headings",
            style="Payroll.Treeview"
        )

        self.tree.heading(
            "category",
            text="اسم الفئة / الشيت"
        )

        self.tree.heading(
            "count",
            text="عدد الموظفين"
        )

        self.tree.heading(
            "total",
            text="إجمالي المبلغ"
        )

        self.tree.column(
            "category",
            anchor="center",
            width=420
        )

        self.tree.column(
            "count",
            anchor="center",
            width=180
        )

        self.tree.column(
            "total",
            anchor="center",
            width=220
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=14
        )

        # =================================================
        # شريط الحالة السفلي
        # =================================================

        self.status_bar = ctk.CTkLabel(
            self,
            text=rtl_text(
                "● النظام جاهز — في انتظار اختيار الملفات"
            ),
            height=28,
            font=ctk.CTkFont(
                size=11
            ),
            anchor="e",
            padx=20,
            text_color=(
                "#64748b",
                "#94a3b8"
            )
        )

        self.status_bar.pack(
            fill="x",
            side="bottom"
        )

        # -------------------------------------------------
        # تسجيل الخروج
        # -------------------------------------------------

        self.btn_logout = ctk.CTkButton(
            self,
            text=rtl_text(
                "🚪 تسجيل الخروج"
            ),
            width=220,
            height=38,
            fg_color="#8b1e1e",
            hover_color="#641515",
            command=self.logout
        )

        self.btn_logout.pack(
            pady=(0, 15)
        )

        # -------------------------------------------------
        # الملخص
        # -------------------------------------------------

        self.frame_summary = ctk.CTkFrame(
            self
        )

        self.frame_summary.pack(
            pady=10,
            padx=20,
            fill="both",
            expand=True
        )

        self.tree = ttk.Treeview(
            self.frame_summary,
            columns=(
                "category",
                "count",
                "total"
            ),
            show="headings"
        )

        self.tree.heading(
            "category",
            text="اسم الفئة / الشيت"
        )

        self.tree.heading(
            "count",
            text="عدد الموظفين"
        )

        self.tree.heading(
            "total",
            text="إجمالي المبلغ"
        )

        self.tree.column(
            "category",
            anchor="center",
            width=300
        )

        self.tree.column(
            "count",
            anchor="center",
            width=150
        )

        self.tree.column(
            "total",
            anchor="center",
            width=180
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

    # =====================================================
    # تسجيل الخروج
    # =====================================================

    def logout(self):

        confirm = messagebox.askyesno(
            rtl_text("تسجيل الخروج"),
            rtl_message(
                "هل تريد تسجيل الخروج من النظام؟"
            ),
            parent=self.master
        )

        if not confirm:
            return

        try:

            if self.logged_username:

                log_user_action(
                    self.logged_username,
                    "logout"
                )

        except Exception:
            pass

        try:

            self.master.destroy()

        except Exception:
            pass

        login_app = LoginWindow()

        login_app.mainloop()

    # =====================================================
    # اختيار قاعدة البيانات
    # =====================================================

    def select_db_file(self):

        file_path = filedialog.askopenfilename(
            title=rtl_text(
                "اختيار ملف قاعدة البيانات الأساسية"
            ),
            filetypes=[
                (
                    "Excel Files",
                    "*.xlsx *.xls *.xlsm"
                )
            ]
        )

        if file_path:

            self.db_file_path = file_path

            self.lbl_db.configure(
                text=os.path.basename(
                    file_path
                ),
                text_color="#28a745"
            )
            
            self.status_bar.configure(
    text=rtl_text(
        "● تم اختيار قاعدة البيانات الأساسية بنجاح"
    ),
    text_color=(
        "#15803d",
        "#4ade80"
    )
)
    # =====================================================
    # اختيار ملف التوزيع
    # =====================================================

    def select_input_file(self):

        file_path = filedialog.askopenfilename(
            title=rtl_text(
                "اختيار شيت توزيع الاستمارة"
            ),
            filetypes=[
                (
                    "Excel Files",
                    "*.xlsx *.xls *.xlsm"
                )
            ]
        )

        if file_path:

            self.input_file_path = file_path

            self.lbl_input.configure(
                text=os.path.basename(
                    file_path
                ),
                text_color="#28a745"
            )
            
            self.status_bar.configure(
    text=rtl_text(
        "● تم اختيار شيت التوزيع بنجاح"
    ),
    text_color=(
        "#15803d",
        "#4ade80"
    )
)
    # =====================================================
    # قراءة قاعدة البيانات
    # =====================================================

    def read_database(self):

        df_db = None
        db_employee_col = None

        for skip in range(0, 15):

            try:

                df_temp = pd.read_excel(
                    self.db_file_path,
                    skiprows=skip
                )

                df_temp = prepare_dataframe_columns(
                    df_temp
                )

                db_employee_col = find_column(
                    df_temp,
                    [
                        "رقم الصـرف",
                        "رقم الصرف",
                        "رقم صرف"
                    ]
                )

                if db_employee_col:

                    df_db = df_temp

                    break

            except Exception:

                continue

        if (
            df_db is None
            or
            db_employee_col is None
        ):

            raise ValueError(
                "لم نتمكن من العثور على عمود (رقم الصرف) في قاعدة البيانات الأساسية."
            )

        df_db[db_employee_col] = (
            df_db[db_employee_col]
            .apply(clean_employee_number)
        )

        return (
            df_db,
            db_employee_col
        )

    # =====================================================
    # قراءة ملف التوزيع
    # =====================================================

    def read_input_file(self):

        df_raw = pd.read_excel(
            self.input_file_path,
            header=None,
            keep_default_na=False
        )

        header_row_index = 0

        for idx, row in df_raw.iterrows():

            row_str = safe_row_to_text(
                row
            )

            if (
                "رقم الصرف" in row_str
                or "رقم الصـرف" in row_str
                or "رقم صرف" in row_str
                or "الرقم القومي" in row_str
                or "الرقم القومى" in row_str
                or "رقم قومي" in row_str
                or "رقم قومى" in row_str
                or "القومي" in row_str
                or "نوع التعيين" in row_str
                or "نوع_التعيين" in row_str
                or "التعيين" in row_str
            ):

                header_row_index = idx

                break

        df_input = pd.read_excel(
            self.input_file_path,
            skiprows=header_row_index,
            keep_default_na=False
        )

        df_input = prepare_dataframe_columns(
            df_input
        )

        # -------------------------------------------------
        # رقم الموظف = رقم الصرف
        # -------------------------------------------------

        input_employee_col = find_column(
            df_input,
            [
                "رقم الصـرف",
                "رقم الصرف",
                "رقم صرف"
            ]
        )

        if not input_employee_col:

            raise ValueError(
                "لم نتمكن من العثور على عمود (رقم الصرف) في شيت توزيع الاستمارة."
            )

        # -------------------------------------------------
        # الرقم القومي
        # -------------------------------------------------

        input_id_col = find_column(
            df_input,
            [
                "الرقم القومي",
                "الرقم القومى",
                "رقم قومي",
                "رقم قومى",
                "القومي",
                "الهوية"
            ]
        )

        # -------------------------------------------------
        # نوع التعيين
        # -------------------------------------------------

        input_category_col = find_column(
            df_input,
            [
                "نوع التعيين",
                "نوع_التعيين",
                "التعيين"
            ]
        )

        # -------------------------------------------------
        # المبلغ
        # -------------------------------------------------

        input_amount_col = find_column(
            df_input,
            [
                "إجمالي المبلغ",
                "إجمالى المبلغ",
                "اجمالي المبلغ",
                "اجمالى المبلغ",
                "إجمالي المبالغ",
                "إجمالى المبالغ",
                "اجمالي المبالغ",
                "اجمالى المبالغ",
                "المبلغ",
                "جملة",
                "الجملة",
                "صافي",
                "الصافي",
                "المستحق",
                "قيمة"
            ]
        )

        if not input_category_col:

            if "Unnamed: 0" in df_input.columns:

                input_category_col = "Unnamed: 0"

            elif len(df_input.columns) > 0:

                input_category_col = (
                    df_input.columns[0]
                )

        # -------------------------------------------------
        # تنظيف رقم الموظف
        # -------------------------------------------------

        df_input[input_employee_col] = (
            df_input[input_employee_col]
            .apply(clean_employee_number)
        )

        # -------------------------------------------------
        # تنظيف الرقم القومي
        # -------------------------------------------------

        if input_id_col:

            df_input[input_id_col] = (
                df_input[input_id_col]
                .apply(clean_id)
            )

        # -------------------------------------------------
        # المبلغ
        # -------------------------------------------------

        if input_amount_col:

            df_input[input_amount_col] = (
                df_input[input_amount_col]
                .apply(normalize_amount)
            )

        else:

            input_amount_col = "إجمالي المبالغ"

            df_input[input_amount_col] = 0.0

        # -------------------------------------------------
        # نوع التعيين
        # -------------------------------------------------

        if input_category_col:

            df_input[input_category_col] = (
                df_input[input_category_col]
                .apply(clean_text)
            )

        else:

            input_category_col = "نوع التعيين"

            df_input[input_category_col] = (
                "غير محدد"
            )

        return (
            df_input,
            input_employee_col,
            input_id_col,
            input_category_col,
            input_amount_col
        )

    # =====================================================
    # المطابقة مع قاعدة البيانات
    # =====================================================

    def match_with_database(
        self,
        df_input,
        input_employee_col,
        df_db,
        db_employee_col
    ):

        db = df_db.copy()

        db[db_employee_col] = (
            db[db_employee_col]
            .apply(clean_employee_number)
        )

        db = db[
            db[db_employee_col] != ""
        ]

        db = db.drop_duplicates(
            subset=[
                db_employee_col
            ],
            keep="first"
        )

        db_indexed = db.set_index(
            db_employee_col,
            drop=False
        )

        rows = []

        for _, row in df_input.iterrows():

            employee_number = (
                clean_employee_number(
                    row.get(
                        input_employee_col,
                        ""
                    )
                )
            )

            output_row = row.to_dict()

            # -------------------------------------------------
            # رقم الصرف فارغ
            # -------------------------------------------------

            if not employee_number:

                output_row[
                    "حالة المطابقة"
                ] = ""

            # -------------------------------------------------
            # موجود في قاعدة البيانات
            # -------------------------------------------------

            elif employee_number in db_indexed.index:

                db_row = db_indexed.loc[
                    employee_number
                ]

                if isinstance(
                    db_row,
                    pd.DataFrame
                ):

                    db_row = db_row.iloc[0]

                for col in db.columns:

                    if col == db_employee_col:
                        continue

                    if col not in output_row:

                        output_row[col] = (
                            db_row[col]
                        )

                output_row[
                    "حالة المطابقة"
                ] = "مطابق"

            # -------------------------------------------------
            # غير موجود في قاعدة البيانات
            # -------------------------------------------------

            else:

                output_row[
                    "حالة المطابقة"
                ] = "سحب جديد"

            rows.append(
                output_row
            )

        return pd.DataFrame(
            rows
        )

    # =====================================================
    # حساب إجمالي المبالغ
    # =====================================================

    def calculate_total_amounts(self, df):

        df = df.copy()

        other_keywords = [
            "مكافآت اخرى غير متكررة",
            "مكافآت أخرى غير متكررة",
            "مكافأت اخرى غير متكررة",
            "مكافأت أخرى غير متكررة",
            "مكافآت غير متكررة",
            "مكافأت غير متكررة",
            "اخرى غير متكررة",
            "أخرى غير متكررة"
        ]

        supervision_keywords = [
            "مكافأت الإشراف",
            "مكافأة الإشراف",
            "مكافآت الإشراف",
            "مكافآت الاشراف",
            "مكافأت الاشراف",
            "الإشراف",
            "الاشراف"
        ]

        teaching_keywords = [
            "مكافأت التدريس",
            "مكافأة التدريس",
            "مكافآت التدريس",
            "التدريس"
        ]

        correction_keywords = [
            "مكافأت التصحيح",
            "مكافأة التصحيح",
            "مكافآت التصحيح",
            "التصحيح"
        ]

        other_col = find_column(
            df,
            other_keywords
        )

        supervision_col = find_column(
            df,
            supervision_keywords
        )

        teaching_col = find_column(
            df,
            teaching_keywords
        )

        correction_col = find_column(
            df,
            correction_keywords
        )

        # -------------------------------------------------
        # مكافآت أخرى
        # -------------------------------------------------

        if other_col:

            df[other_col] = (
                df[other_col]
                .apply(normalize_amount)
            )

            df[
                "مكافآت أخرى غير متكررة"
            ] = df[other_col]

        else:

            df[
                "مكافآت أخرى غير متكررة"
            ] = 0.0

        # -------------------------------------------------
        # الإشراف
        # -------------------------------------------------

        if supervision_col:

            df[supervision_col] = (
                df[supervision_col]
                .apply(normalize_amount)
            )

            df[
                "مكافأت الإشراف"
            ] = df[supervision_col]

        else:

            df[
                "مكافأت الإشراف"
            ] = 0.0

        # -------------------------------------------------
        # التدريس
        # -------------------------------------------------

        if teaching_col:

            df[teaching_col] = (
                df[teaching_col]
                .apply(normalize_amount)
            )

            df[
                "مكافأت التدريس"
            ] = df[teaching_col]

        else:

            df[
                "مكافأت التدريس"
            ] = 0.0

        # -------------------------------------------------
        # التصحيح
        # -------------------------------------------------

        if correction_col:

            df[correction_col] = (
                df[correction_col]
                .apply(normalize_amount)
            )

            df[
                "مكافأت التصحيح"
            ] = df[correction_col]

        else:

            df[
                "مكافأت التصحيح"
            ] = 0.0

        # -------------------------------------------------
        # الإجمالي
        # -------------------------------------------------

        df[
            "إجمالي المبالغ"
        ] = (
            df[
                "مكافآت أخرى غير متكررة"
            ]
            +
            df[
                "مكافأت الإشراف"
            ]
            +
            df[
                "مكافأت التدريس"
            ]
            +
            df[
                "مكافأت التصحيح"
            ]
        )

        return df

    # =====================================================
    # إنشاء شيت المكافآت
    # =====================================================

    def create_reward_sheet(
        self,
        writer,
        df,
        category_col,
        amount_col,
        sheet_name,
        keywords
    ):

        reward_df = pd.DataFrame()

        reward_col = None

        for col in df.columns:

            col_text = clean_text(
                col
            )

            if not col_text:
                continue

            for keyword in keywords:

                keyword_text = clean_text(
                    keyword
                )

                if (
                    keyword_text
                    and keyword_text in col_text
                ):

                    reward_col = col

                    break

            if reward_col:
                break

        if reward_col:

            reward_values = (
                df[reward_col]
                .apply(normalize_amount)
            )

            reward_df = df[
                reward_values > 0
            ].copy()

            if not reward_df.empty:

                reward_df[
                    "قيمة المكافأة"
                ] = (
                    reward_df[reward_col]
                    .apply(normalize_amount)
                )

        if reward_df.empty:

            category_series = (
                df[category_col]
                .apply(clean_text)
            )

            for keyword in keywords:

                keyword_text = clean_text(
                    keyword
                )

                if not keyword_text:
                    continue

                temp = df[
                    category_series.str.contains(
                        re.escape(
                            keyword_text
                        ),
                        case=False,
                        na=False
                    )
                ].copy()

                if not temp.empty:

                    reward_df = temp

                    reward_df[
                        "قيمة المكافأة"
                    ] = (
                        reward_df[amount_col]
                        .apply(
                            normalize_amount
                        )
                    )

                    break

        sheet_name = safe_sheet_name(
            sheet_name
        )

        if reward_df.empty:

            empty_df = pd.DataFrame(
                columns=[
                    "رقم الصرف",
                    "الرقم القومي",
                    "الاسم",
                    "قيمة المكافأة"
                ]
            )

            empty_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

        else:

            reward_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

    # =====================================================
    # تصدير النتائج
    # =====================================================

    def export_results(
        self,
        matched_df,
        category_col,
        amount_col
    ):

        output_dir = filedialog.askdirectory(
            title=rtl_text(
                "اختيار مجلد حفظ نتائج التوزيع"
            )
        )

        if not output_dir:
            return None

        result_dir = os.path.join(
            output_dir,
            "نتائج توزيع البيرول"
        )

        os.makedirs(
            result_dir,
            exist_ok=True
        )

        matched_df = matched_df.copy()

        # -------------------------------------------------
        # الأعمدة الأساسية
        # -------------------------------------------------

        if category_col not in matched_df.columns:

            matched_df[category_col] = (
                "غير محدد"
            )

        matched_df[category_col] = (
            matched_df[category_col]
            .apply(clean_text)
        )

        if amount_col not in matched_df.columns:

            matched_df[amount_col] = 0.0

        matched_df[amount_col] = (
            matched_df[amount_col]
            .apply(normalize_amount)
        )

        # -------------------------------------------------
        # حساب إجمالي المبالغ
        # -------------------------------------------------

        matched_df = (
            self.calculate_total_amounts(
                matched_df
            )
        )

        matched_df[
            "إجمالي المبالغ"
        ] = (
            matched_df[
                "إجمالي المبالغ"
            ]
            .apply(normalize_amount)
        )

        # -------------------------------------------------
        # تحديد عمود رقم الصرف
        # -------------------------------------------------

        employee_col = find_column(
            matched_df,
            [
                "رقم الصـرف",
                "رقم الصرف",
                "رقم صرف"
            ]
        )

        if not employee_col:

            raise ValueError(
                "لم نتمكن من تحديد عمود رقم الصرف في النتائج."
            )

        matched_df[employee_col] = (
            matched_df[employee_col]
            .apply(clean_employee_number)
        )

        # =================================================
        # تحديد السحب الجديد
        # =================================================

        new_pull_mask = (
            matched_df[employee_col]
            .apply(clean_employee_number)
            .ne("")
            &
            matched_df[
                "حالة المطابقة"
            ]
            .apply(clean_text)
            .eq("سحب جديد")
        )

        new_pull_df = matched_df[
            new_pull_mask
        ].copy()

        normal_df = matched_df[
            ~new_pull_mask
        ].copy()

        # =================================================
        # ملف سحب جديد مستقل
        # =================================================

        new_pull_file = os.path.join(
            result_dir,
            "سحب جديد.xlsx"
        )

        if new_pull_df.empty:

            empty_new_pull = pd.DataFrame(
                columns=matched_df.columns
            )

            empty_new_pull.to_excel(
                new_pull_file,
                sheet_name="سحب جديد",
                index=False
            )

        else:

            new_pull_df.to_excel(
                new_pull_file,
                sheet_name="سحب جديد",
                index=False
            )

        # =================================================
        # ملفات الفئات العادية
        # =================================================

        normal_df = normal_df[
            normal_df[category_col] != ""
        ].copy()

        categories = (
            normal_df[category_col]
            .dropna()
            .unique()
            .tolist()
        )

        summary = []

        for category in categories:

            category_text = clean_text(
                category
            )

            if not category_text:
                continue

            category_df = normal_df[
                normal_df[category_col] == category
            ].copy()

            if category_df.empty:
                continue

            category_df[
                "إجمالي المبالغ"
            ] = (
                category_df[
                    "إجمالي المبالغ"
                ]
                .apply(normalize_amount)
            )

            file_name = safe_sheet_name(
                category_text
            )

            output_file = os.path.join(
                result_dir,
                f"{file_name}.xlsx"
            )

            with pd.ExcelWriter(
                output_file,
                engine="openpyxl"
            ) as writer:

                category_df.to_excel(
                    writer,
                    sheet_name="التوزيع",
                    index=False
                )

            count = len(
                category_df
            )

            total = (
                pd.to_numeric(
                    category_df[
                        "إجمالي المبالغ"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            summary.append(
                (
                    category_text,
                    count,
                    float(total)
                )
            )

        # =================================================
        # التوزيع الشامل
        # =================================================

        all_file = os.path.join(
            result_dir,
            "التوزيع_الشامل.xlsx"
        )

        with pd.ExcelWriter(
            all_file,
            engine="openpyxl"
        ) as writer:

            # -------------------------------------------------
            # كل البيانات
            # -------------------------------------------------

            matched_df.to_excel(
                writer,
                sheet_name="كل البيانات",
                index=False
            )

            # -------------------------------------------------
            # سحب جديد
            # -------------------------------------------------

            if new_pull_df.empty:

                pd.DataFrame(
                    columns=matched_df.columns
                ).to_excel(
                    writer,
                    sheet_name="سحب جديد",
                    index=False
                )

            else:

                new_pull_df.to_excel(
                    writer,
                    sheet_name="سحب جديد",
                    index=False
                )

            # -------------------------------------------------
            # مكافأة الإشراف
            # -------------------------------------------------

            self.create_reward_sheet(
                writer,
                normal_df,
                category_col,
                amount_col,
                "مكافأت الإشراف",
                [
                    "مكافأت الإشراف",
                    "مكافأة الإشراف",
                    "مكافآت الإشراف",
                    "مكافأت الاشراف",
                    "الإشراف",
                    "الاشراف"
                ]
            )

            # -------------------------------------------------
            # مكافأة التصحيح
            # -------------------------------------------------

            self.create_reward_sheet(
                writer,
                normal_df,
                category_col,
                amount_col,
                "مكافأت التصحيح",
                [
                    "مكافأت التصحيح",
                    "مكافأة التصحيح",
                    "مكافآت التصحيح",
                    "التصحيح"
                ]
            )

            # -------------------------------------------------
            # مكافأة التدريس
            # -------------------------------------------------

            self.create_reward_sheet(
                writer,
                normal_df,
                category_col,
                amount_col,
                "مكافأت التدريس",
                [
                    "مكافأت التدريس",
                    "مكافأة التدريس",
                    "مكافآت التدريس",
                    "التدريس"
                ]
            )

        # =================================================
        # ملف الملخص
        # =================================================

        summary_file = os.path.join(
            result_dir,
            "ملخص_التوزيع.xlsx"
        )

        summary_df = pd.DataFrame(
            summary,
            columns=[
                "الفئة",
                "عدد الموظفين",
                "إجمالي المبلغ"
            ]
        )

        if not summary_df.empty:

            summary_df[
                "عدد الموظفين"
            ] = (
                pd.to_numeric(
                    summary_df[
                        "عدد الموظفين"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .astype(int)
            )

            summary_df[
                "إجمالي المبلغ"
            ] = (
                pd.to_numeric(
                    summary_df[
                        "إجمالي المبلغ"
                    ],
                    errors="coerce"
                )
                .fillna(0.0)
            )

        # =================================================
        # إضافة السحب الجديد
        # =================================================

        new_pull_total = 0.0

        if not new_pull_df.empty:

            new_pull_df[
                "إجمالي المبالغ"
            ] = (
                new_pull_df[
                    "إجمالي المبالغ"
                ]
                .apply(normalize_amount)
            )

            new_pull_total = (
                pd.to_numeric(
                    new_pull_df[
                        "إجمالي المبالغ"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            summary_df = pd.concat(
                [
                    summary_df,
                    pd.DataFrame(
                        [
                            [
                                "سحب جديد",
                                len(new_pull_df),
                                float(
                                    new_pull_total
                                )
                            ]
                        ],
                        columns=summary_df.columns
                    )
                ],
                ignore_index=True
            )

        # =================================================
        # تنسيق إجمالي المبلغ
        # =================================================

        summary_df[
            "إجمالي المبلغ"
        ] = (
            pd.to_numeric(
                summary_df[
                    "إجمالي المبلغ"
                ],
                errors="coerce"
            )
            .fillna(0.0)
        )

        with pd.ExcelWriter(
            summary_file,
            engine="openpyxl"
        ) as writer:

            summary_df.to_excel(
                writer,
                sheet_name="الملخص",
                index=False
            )

            worksheet = writer.sheets[
                "الملخص"
            ]

            for cell in worksheet["C"][1:]:

                cell.number_format = (
                    '#,##0.00'
                )

        return (
            result_dir,
            summary,
            len(new_pull_df),
            float(new_pull_total)
        )

    # =====================================================
    # البحث عن عمود الرقم القومي
    # =====================================================

    def find_national_id_column(
        self,
        df
    ):

        col = find_column(
            df,
            [
                "الرقم القومي",
                "الرقم القومى",
                "رقم قومي",
                "رقم قومى",
                "القومي",
                "الهوية"
            ]
        )

        if col:
            return col

        for c in df.columns:

            text = clean_text(c)

            if (
                "قومي" in text
                or
                "قومى" in text
            ):

                return c

        return None

    # =====================================================
    # إدارة المستخدمين
    # =====================================================

    def open_user_management(self):

        if self.user_role != "admin":

            messagebox.showwarning(
                rtl_text("غير مسموح"),
                rtl_message(
                    "ليس لديك صلاحية لإدارة المستخدمين."
                ),
                parent=self.master
            )

            return

        window = ctk.CTkToplevel(
            self.master
        )

        window.title(
            rtl_text(
                "👥 إدارة المستخدمين"
            )
        )

        window.geometry(
            "800x560"
        )

        window.minsize(
            700,
            500
        )

        window.transient(
            self.master
        )

        # -------------------------------------------------
        # العنوان
        # -------------------------------------------------

        title = ctk.CTkLabel(
            window,
            text=rtl_text(
                "👥 إدارة مستخدمي النظام"
            ),
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        title.pack(
            pady=20
        )

        # -------------------------------------------------
        # إطار الجدول
        # -------------------------------------------------

        table_frame = ctk.CTkFrame(
            window
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        columns = (
            "username",
            "role",
            "status"
        )

        user_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        user_tree.heading(
            "username",
            text="اسم المستخدم"
        )

        user_tree.heading(
            "role",
            text="الصلاحية"
        )

        user_tree.heading(
            "status",
            text="الحالة"
        )

        user_tree.column(
            "username",
            anchor="center",
            width=250
        )

        user_tree.column(
            "role",
            anchor="center",
            width=180
        )

        user_tree.column(
            "status",
            anchor="center",
            width=150
        )

        user_tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # -------------------------------------------------
        # ترجمة الصلاحية
        # -------------------------------------------------

        def role_display(role):

            role = str(
                role or ""
            ).strip().lower()

            if role == "admin":
                return "مدير"

            if role == "reviewer":
                return "مراجع"

            return "مستخدم"

        # -------------------------------------------------
        # ترجمة الحالة
        # -------------------------------------------------

        def status_display(status):

            status = str(
                status or ""
            ).strip().lower()

            if status == "active":
                return "نشط"

            return "غير نشط"

        # -------------------------------------------------
        # تحميل المستخدمين
        # -------------------------------------------------

        def load_users():

            for item in user_tree.get_children():

                user_tree.delete(
                    item
                )

            try:

                response = (
                    supabase
                    .table(SUPABASE_TABLE)
                    .select(
                        "username,role,status"
                    )
                    .execute()
                )

                users = (
                    response.data
                    or []
                )

                for user in users:

                    username = str(
                        user.get(
                            "username",
                            ""
                        )
                    ).strip()

                    role = str(
                        user.get(
                            "role",
                            "reviewer"
                        )
                    ).strip().lower()

                    status = str(
                        user.get(
                            "status",
                            "active"
                        )
                    ).strip().lower()

                    user_tree.insert(
                        "",
                        "end",
                        values=(
                            username,
                            role_display(role),
                            status_display(status)
                        )
                    )

            except Exception as err:

                messagebox.showerror(
                    rtl_text("خطأ"),
                    rtl_message(
                        f"تعذر تحميل المستخدمين.\n\n{err}"
                    ),
                    parent=window
                )

        # -------------------------------------------------
        # الحصول على المستخدم المحدد
        # -------------------------------------------------

        def get_selected_username():

            selected = (
                user_tree.selection()
            )

            if not selected:

                messagebox.showwarning(
                    rtl_text("تنبيه"),
                    rtl_message(
                        "برجاء اختيار مستخدم أولاً."
                    ),
                    parent=window
                )

                return None

            values = user_tree.item(
                selected[0],
                "values"
            )

            if not values:
                return None

            return str(
                values[0]
            ).strip()

        # -------------------------------------------------
        # إضافة مستخدم
        # -------------------------------------------------

        def add_user():

            dialog = ctk.CTkToplevel(
                window
            )

            dialog.title(
                rtl_text(
                    "إضافة مستخدم"
                )
            )

            dialog.geometry(
                "450x470"
            )

            dialog.transient(
                window
            )

            ctk.CTkLabel(
                dialog,
                text=rtl_text(
                    "إضافة مستخدم جديد"
                ),
                font=ctk.CTkFont(
                    size=20,
                    weight="bold"
                )
            ).pack(
                pady=20
            )

            ctk.CTkLabel(
                dialog,
                text=rtl_text(
                    "اسم المستخدم"
                )
            ).pack(
                pady=(10, 3)
            )

            username_entry = ctk.CTkEntry(
                dialog,
                width=320,
                justify="center"
            )

            username_entry.pack()

            ctk.CTkLabel(
                dialog,
                text=rtl_text(
                    "كلمة المرور"
                )
            ).pack(
                pady=(15, 3)
            )

            password_entry = ctk.CTkEntry(
                dialog,
                width=320,
                justify="center",
                show="*"
            )

            password_entry.pack()

            ctk.CTkLabel(
                dialog,
                text=rtl_text(
                    "الصلاحية"
                )
            ).pack(
                pady=(15, 3)
            )

            role_var = tk.StringVar(
                value="reviewer"
            )

            role_menu = ctk.CTkOptionMenu(
                dialog,
                width=320,
                variable=role_var,
                values=[
                    "admin",
                    "reviewer",
                    "user"
                ]
            )

            role_menu.pack()

            ctk.CTkLabel(
                dialog,
                text=rtl_text(
                    "admin = مدير   |   reviewer = مراجع   |   user = مستخدم"
                ),
                font=ctk.CTkFont(
                    size=11
                )
            ).pack(
                pady=15
            )

            def save_new_user():

                username = (
                    username_entry
                    .get()
                    .strip()
                )

                password = (
                    password_entry
                    .get()
                )

                role = (
                    role_var
                    .get()
                    .strip()
                    .lower()
                )

                if not username:

                    messagebox.showwarning(
                        rtl_text("تنبيه"),
                        rtl_message(
                            "برجاء إدخال اسم المستخدم."
                        ),
                        parent=dialog
                    )

                    return

                if not password:

                    messagebox.showwarning(
                        rtl_text("تنبيه"),
                        rtl_message(
                            "برجاء إدخال كلمة المرور."
                        ),
                        parent=dialog
                    )

                    return

                if role not in (
                    "admin",
                    "reviewer",
                    "user"
                ):

                    role = "reviewer"

                try:

                    existing_response = (
                        supabase
                        .table(SUPABASE_TABLE)
                        .select(
                            "username"
                        )
                        .execute()
                    )

                    existing_users = (
                        existing_response.data
                        or []
                    )

                    exists = any(
                        str(
                            item.get(
                                "username",
                                ""
                            )
                        ).strip() == username
                        for item in existing_users
                    )

                    if exists:

                        messagebox.showwarning(
                            rtl_text("تنبيه"),
                            rtl_message(
                                "اسم المستخدم موجود بالفعل."
                            ),
                            parent=dialog
                        )

                        return

                    (
                        supabase
                        .table(SUPABASE_TABLE)
                        .insert(
                            {
                                "username": username,
                                "password": password,
                                "role": role,
                                "status": "active"
                            }
                        )
                        .execute()
                    )

                    messagebox.showinfo(
                        rtl_text("تم"),
                        rtl_message(
                            "تمت إضافة المستخدم بنجاح."
                        ),
                        parent=dialog
                    )

                    dialog.destroy()

                    load_users()

                except Exception as err:

                    messagebox.showerror(
                        rtl_text("خطأ"),
                        rtl_message(
                            f"تعذر إضافة المستخدم.\n\n{err}"
                        ),
                        parent=dialog
                    )

            ctk.CTkButton(
                dialog,
                text=rtl_text(
                    "💾 حفظ المستخدم"
                ),
                width=320,
                height=40,
                command=save_new_user
            ).pack(
                pady=10
            )

        # -------------------------------------------------
        # تعديل مستخدم
        # -------------------------------------------------

        def edit_user():

            username = (
                get_selected_username()
            )

            if not username:
                return

            try:

                response = (
                    supabase
                    .table(SUPABASE_TABLE)
                    .select(
                        "username,password,role,status"
                    )
                    .execute()
                )

                users = (
                    response.data
                    or []
                )

                user = None

                for item in users:

                    if str(
                        item.get(
                            "username",
                            ""
                        )
                    ).strip() == username:

                        user = item

                        break

                if user is None:

                    messagebox.showerror(
                        rtl_text("خطأ"),
                        rtl_message(
                            "لم يتم العثور على المستخدم."
                        ),
                        parent=window
                    )

                    return

                dialog = ctk.CTkToplevel(
                    window
                )

                dialog.title(
                    rtl_text(
                        "تعديل المستخدم"
                    )
                )

                dialog.geometry(
                    "450x500"
                )

                dialog.transient(
                    window
                )

                ctk.CTkLabel(
                    dialog,
                    text=rtl_text(
                        f"تعديل المستخدم: {username}"
                    ),
                    font=ctk.CTkFont(
                        size=19,
                        weight="bold"
                    )
                ).pack(
                    pady=20
                )

                ctk.CTkLabel(
                    dialog,
                    text=rtl_text(
                        "كلمة المرور الجديدة"
                    )
                ).pack(
                    pady=(10, 3)
                )

                password_entry = ctk.CTkEntry(
                    dialog,
                    width=320,
                    justify="center",
                    show="*"
                )

                password_entry.insert(
                    0,
                    str(
                        user.get(
                            "password",
                            ""
                        )
                    )
                )

                password_entry.pack()

                ctk.CTkLabel(
                    dialog,
                    text=rtl_text(
                        "الصلاحية"
                    )
                ).pack(
                    pady=(20, 3)
                )

                current_role = str(
                    user.get(
                        "role",
                        "reviewer"
                    )
                ).strip().lower()

                if current_role not in (
                    "admin",
                    "reviewer",
                    "user"
                ):

                    current_role = "reviewer"

                role_var = tk.StringVar(
                    value=current_role
                )

                ctk.CTkOptionMenu(
                    dialog,
                    width=320,
                    variable=role_var,
                    values=[
                        "admin",
                        "reviewer",
                        "user"
                    ]
                ).pack()

                ctk.CTkLabel(
                    dialog,
                    text=rtl_text(
                        "admin = مدير   |   reviewer = مراجع   |   user = مستخدم"
                    ),
                    font=ctk.CTkFont(
                        size=11
                    )
                ).pack(
                    pady=15
                )

                status_var = tk.StringVar(
                    value=str(
                        user.get(
                            "status",
                            "active"
                        )
                    ).strip().lower()
                    or "active"
                )

                ctk.CTkOptionMenu(
                    dialog,
                    width=320,
                    variable=status_var,
                    values=[
                        "active",
                        "inactive"
                    ]
                ).pack(
                    pady=5
                )

                def save_changes():

                    new_password = (
                        password_entry
                        .get()
                    )

                    new_role = (
                        role_var
                        .get()
                        .strip()
                        .lower()
                    )

                    new_status = (
                        status_var
                        .get()
                        .strip()
                        .lower()
                    )

                    if not new_password:

                        messagebox.showwarning(
                            rtl_text("تنبيه"),
                            rtl_message(
                                "كلمة المرور لا يمكن أن تكون فارغة."
                            ),
                            parent=dialog
                        )

                        return

                    if new_role not in (
                        "admin",
                        "reviewer",
                        "user"
                    ):

                        new_role = "reviewer"

                    if new_status not in (
                        "active",
                        "inactive"
                    ):

                        new_status = "active"

                    # منع تعطيل الحساب الحالي
                    if (
                        username
                        ==
                        self.logged_username
                        and
                        new_status != "active"
                    ):

                        messagebox.showwarning(
                            rtl_text("غير مسموح"),
                            rtl_message(
                                "لا يمكن تعطيل الحساب المستخدم حاليًا."
                            ),
                            parent=dialog
                        )

                        return

                    try:

                        (
                            supabase
                            .table(SUPABASE_TABLE)
                            .update(
                                {
                                    "password": new_password,
                                    "role": new_role,
                                    "status": new_status
                                }
                            )
                            .eq(
                                "username",
                                user.get(
                                    "username"
                                )
                            )
                            .execute()
                        )

                        messagebox.showinfo(
                            rtl_text("تم"),
                            rtl_message(
                                "تم تعديل المستخدم بنجاح."
                            ),
                            parent=dialog
                        )

                        dialog.destroy()

                        load_users()

                    except Exception as err:

                        messagebox.showerror(
                            rtl_text("خطأ"),
                            rtl_message(
                                f"تعذر تعديل المستخدم.\n\n{err}"
                            ),
                            parent=dialog
                        )

                ctk.CTkButton(
                    dialog,
                    text=rtl_text(
                        "💾 حفظ التعديلات"
                    ),
                    width=320,
                    height=42,
                    command=save_changes
                ).pack(
                    pady=20
                )

            except Exception as err:

                messagebox.showerror(
                    rtl_text("خطأ"),
                    rtl_message(
                        f"تعذر فتح بيانات المستخدم.\n\n{err}"
                    ),
                    parent=window
                )

        # -------------------------------------------------
        # حذف مستخدم
        # -------------------------------------------------

        def delete_user():

            username = (
                get_selected_username()
            )

            if not username:
                return

            if username == self.logged_username:

                messagebox.showwarning(
                    rtl_text("غير مسموح"),
                    rtl_message(
                        "لا يمكن حذف الحساب المستخدم حاليًا."
                    ),
                    parent=window
                )

                return

            confirm = messagebox.askyesno(
                rtl_text("تأكيد الحذف"),
                rtl_message(
                    f"هل تريد حذف المستخدم:\n{username} ؟"
                ),
                parent=window
            )

            if not confirm:
                return

            try:

                (
                    supabase
                    .table(SUPABASE_TABLE)
                    .delete()
                    .eq(
                        "username",
                        username
                    )
                    .execute()
                )

                messagebox.showinfo(
                    rtl_text("تم"),
                    rtl_message(
                        "تم حذف المستخدم بنجاح."
                    ),
                    parent=window
                )

                load_users()

            except Exception as err:

                messagebox.showerror(
                    rtl_text("خطأ"),
                    rtl_message(
                        f"تعذر حذف المستخدم.\n\n{err}"
                    ),
                    parent=window
                )

        # -------------------------------------------------
        # تغيير حالة المستخدم
        # -------------------------------------------------

        def toggle_status():

            username = (
                get_selected_username()
            )

            if not username:
                return

            if username == self.logged_username:

                messagebox.showwarning(
                    rtl_text("غير مسموح"),
                    rtl_message(
                        "لا يمكن تعطيل الحساب المستخدم حاليًا."
                    ),
                    parent=window
                )

                return

            try:

                response = (
                    supabase
                    .table(SUPABASE_TABLE)
                    .select(
                        "username,status"
                    )
                    .execute()
                )

                users = (
                    response.data
                    or []
                )

                user = None

                for item in users:

                    if str(
                        item.get(
                            "username",
                            ""
                        )
                    ).strip() == username:

                        user = item

                        break

                if user is None:
                    return

                current_status = str(
                    user.get(
                        "status",
                        "active"
                    )
                ).strip().lower()

                new_status = (
                    "inactive"
                    if current_status == "active"
                    else "active"
                )

                (
                    supabase
                    .table(SUPABASE_TABLE)
                    .update(
                        {
                            "status": new_status
                        }
                    )
                    .eq(
                        "username",
                        user.get(
                            "username"
                        )
                    )
                    .execute()
                )

                load_users()

            except Exception as err:

                messagebox.showerror(
                    rtl_text("خطأ"),
                    rtl_message(
                        f"تعذر تغيير حالة المستخدم.\n\n{err}"
                    ),
                    parent=window
                )

        # -------------------------------------------------
        # أزرار الإدارة
        # -------------------------------------------------

        buttons_frame = ctk.CTkFrame(
            window
        )

        buttons_frame.pack(
            fill="x",
            padx=20,
            pady=15
        )

        ctk.CTkButton(
            buttons_frame,
            text=rtl_text(
                "➕ إضافة مستخدم"
            ),
            command=add_user,
            width=150
        ).pack(
            side="right",
            padx=5
        )

        ctk.CTkButton(
            buttons_frame,
            text=rtl_text(
                "✏️ تعديل"
            ),
            command=edit_user,
            width=120
        ).pack(
            side="right",
            padx=5
        )

        ctk.CTkButton(
            buttons_frame,
            text=rtl_text(
                "🔄 تغيير الحالة"
            ),
            command=toggle_status,
            width=140
        ).pack(
            side="right",
            padx=5
        )

        ctk.CTkButton(
            buttons_frame,
            text=rtl_text(
                "🗑 حذف"
            ),
            command=delete_user,
            width=120,
            fg_color="#8b1e1e",
            hover_color="#641515"
        ).pack(
            side="right",
            padx=5
        )

        ctk.CTkButton(
            buttons_frame,
            text=rtl_text(
                "🔃 تحديث"
            ),
            command=load_users,
            width=100
        ).pack(
            side="left",
            padx=5
        )

        load_users()

    # =====================================================
    # تشغيل النظام
    # =====================================================

    def process_payroll_splitting(self):

        if not self.db_file_path:

            messagebox.showwarning(
                rtl_text("تنبيه النظام"),
                rtl_message(
                    "يرجى اختيار ملف قاعدة البيانات الأساسية أولاً!"
                ),
                parent=self.master
            )

            return

        if not self.input_file_path:

            messagebox.showwarning(
                rtl_text("تنبيه النظام"),
                rtl_message(
                    "يرجى اختيار شيت التوزيع المجمع أولاً!"
                ),
                parent=self.master
            )

            return

        # -------------------------------------------------
        # تنظيف الملخص السابق
        # -------------------------------------------------

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        self.btn_run.configure(
            state="disabled",
            text=rtl_text(
                "⏳ جاري الفرز والتوزيع..."
            )
        )
        
        self.status_bar.configure(
    text=rtl_text(
        "● جاري قراءة الملفات ومطابقة أرقام الصرف..."
    ),
    text_color=(
        "#d97706",
        "#fbbf24"
    )
)
        self.status_bar.configure(
    text=rtl_text(
        "● النظام جاهز لتنفيذ عملية جديدة"
    ),
    text_color=(
        "#15803d",
        "#4ade80"
    )
)
        
        self.update_idletasks()

        try:

            # -------------------------------------------------
            # قراءة قاعدة البيانات
            # -------------------------------------------------

            (
                df_db,
                db_employee_col
            ) = self.read_database()

            # -------------------------------------------------
            # قراءة ملف التوزيع
            # -------------------------------------------------

            (
                df_input,
                input_employee_col,
                input_id_col,
                input_category_col,
                input_amount_col
            ) = self.read_input_file()

            # -------------------------------------------------
            # المطابقة
            # -------------------------------------------------

            matched_df = (
                self.match_with_database(
                    df_input,
                    input_employee_col,
                    df_db,
                    db_employee_col
                )
            )

            # -------------------------------------------------
            # التصدير
            # -------------------------------------------------

            export_result = (
                self.export_results(
                    matched_df,
                    input_category_col,
                    input_amount_col
                )
            )

            if export_result is None:

                return

            (
                result_dir,
                summary,
                new_pull_count,
                new_pull_total
            ) = export_result

            # -------------------------------------------------
            # عرض الملخص
            # -------------------------------------------------

            for category, count, total in summary:

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        category,
                        count,
                        f"{total:,.2f}"
                    )
                )

            # -------------------------------------------------
            # عرض السحب الجديد
            # -------------------------------------------------

            if new_pull_count > 0:

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        "سحب جديد",
                        new_pull_count,
                        f"{new_pull_total:,.2f}"
                    )
                )

            # -------------------------------------------------
            # رسالة النجاح
            # -------------------------------------------------

            messagebox.showinfo(
                rtl_text(
                    "✅ تمت العملية بنجاح"
                ),
                rtl_message(
                    "تم فرز وتوزيع البيانات بنجاح.\n\n"
                    "تمت المطابقة باستخدام رقم الصرف.\n\n"
                    "قاعدة السحب الجديد:\n"
                    "أي رقم صرف موجود في شيت التوزيع "
                    "وغير موجود في قاعدة البيانات "
                    "تم تصنيفه كسحب جديد.\n\n"
                    "الصفوف التي لا تحتوي على رقم صرف "
                    "لا يتم احتسابها كسحب جديد.\n\n"
                    f"عدد الفئات: {len(summary)}\n"
                    f"عدد السحب الجديد: {new_pull_count}\n\n"
                    f"إجمالي مبالغ السحب الجديد: "
                    f"{new_pull_total:,.2f}\n\n"
                    f"مكان حفظ النتائج:\n{result_dir}"
                ),
                parent=self.master
            )

        except Exception as err:

            messagebox.showerror(
                rtl_text(
                    "❌ خطأ أثناء التوزيع"
                ),
                rtl_message(
                    "حدث خطأ أثناء معالجة الملفات.\n\n"
                    f"نوع الخطأ: {type(err).__name__}\n\n"
                    f"تفاصيل الخطأ:\n{err}"
                ),
                parent=self.master
            )

        finally:

            self.btn_run.configure(
                state="normal",
                text=rtl_text(
                    "⚡ تشغيل الفرز والتوزيع التلقائي برقم الصرف"
                )
            )


# =========================================================
# تشغيل البرنامج
# =========================================================

if __name__ == "__main__":

    login_app = LoginWindow()

    login_app.mainloop()
