import os
from datetime import datetime

import requests
import streamlit as st

from payroll_core import PayrollError, split_payroll
from users_admin import UserStore, render_users_admin

st.set_page_config(page_title="نظام فرز البيرول السحابي", page_icon="⚙️", layout="wide")

# ---- إعدادات Supabase (من st.secrets على Streamlit Cloud أو من متغيرات البيئة) ----
_HAS_SECRETS = any(os.path.exists(p) for p in (
    os.path.expanduser("~/.streamlit/secrets.toml"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml"),
))


def _setting(name, default=""):
    if _HAS_SECRETS:
        try:
            if name in st.secrets:
                return st.secrets[name]
        except Exception:
            pass
    return os.environ.get(name, default)

SUPABASE_URL = _setting("SUPABASE_URL", "https://xnpiqugxderlogjyjiuz.supabase.co")
SUPABASE_KEY = _setting("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhucGlxdWd4ZGVybG9nanlqaXV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NzMzNTcsImV4cCI6MjEwMzM0OTM1N30.Fe_Oy6lgU3PDKMYZzXskt23x-cfXLyyQ428Iq5rC2Ls")
SUPABASE_TABLE = _setting("SUPABASE_TABLE", "mohamed_said")
SUPABASE_LOG_TABLE = _setting("SUPABASE_LOG_TABLE", "payroll_runs")
DEMO_MODE = _setting("DEMO_MODE") == "1" and not SUPABASE_KEY
# أسماء المديرين المسموح لهم بإدارة المستخدمين (مفصولة بفاصلة) - مثال: ADMIN_USERS = "admin,mohamed"
ADMIN_USERS = [u.strip() for u in str(_setting("ADMIN_USERS", "admin,mohamed_said")).split(",") if u.strip()]


def sb_headers(extra=None):
    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def sb_url(table):
    return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"


def cloud_login(username, password):
    """يعيد (ok, message)."""
    if not SUPABASE_KEY:
        if DEMO_MODE:
            return True, ""
        return False, "لم يتم ضبط SUPABASE_KEY في الإعدادات (Secrets)."
    try:
        r = requests.get(sb_url(SUPABASE_TABLE), headers=sb_headers(),
                         params={"username": f"ilike.{username}%", "select": "username,password,status"}, timeout=15)
    except requests.exceptions.RequestException as e:
        return False, f"فشل الاتصال بالسيرفر السحابي: {e}"
    if r.status_code != 200:
        return False, f"السيرفر رد بخطأ ({r.status_code}): {r.text[:200]}"
    users = [u for u in r.json() if str(u.get("username", "")).strip().lower() == username.lower()]
    if not users or str(users[0].get("password", "")).strip() != password:
        return False, "اسم المستخدم أو كلمة المرور غير صحيحة!"
    if str(users[0].get("status", "")).strip().lower() == "blocked":
        return False, "🚫 هذا الحساب تم إيقافه من قبل مدير النظام!"
    return True, ""


def log_run(username, summary_df, file_name):
    try:
        requests.post(sb_url(SUPABASE_LOG_TABLE), headers=sb_headers({"Prefer": "return=minimal"}), timeout=10, json={
            "username": username,
            "run_at": datetime.now().isoformat(),
            "output_file": file_name,
            "categories": int(len(summary_df)),
            "employees": int(summary_df["عدد الموظفين"].sum()),
            "total_amount": float(summary_df["إجمالي المبلغ"].sum()),
        })
    except Exception:
        pass


# ---- RTL styling ----
st.markdown("""
<style>
  html, body, [class*="css"], .stApp { direction: rtl; }
  .stTextInput input, .stMarkdown, .stDataFrame, label, p, h1, h2, h3 { text-align: right; }
  div[data-testid="stFileUploader"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# ---- 1. تسجيل الدخول ----
if not st.session_state.user:
    st.title("🔒 نظام فرز البيرول - تسجيل دخول سحابي")
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button("تحقق والاتصال بالسحابة", use_container_width=True, type="primary")
        if submitted:
            if not username or not password:
                st.warning("برجاء كتابة اسم المستخدم وكلمة المرور أولاً!")
            else:
                ok, msg = cloud_login(username.strip(), password.strip())
                if ok:
                    st.session_state.user = username.strip()
                    st.rerun()
                else:
                    st.error(msg)
    st.stop()

# ---- 2. شاشة الفرز والتوزيع ----
is_admin = st.session_state.user in ADMIN_USERS

with st.sidebar:
    st.success(f"👤 مرحباً، {st.session_state.user}" + (" (مدير)" if is_admin else ""))
    pages = ["⚙️ فرز وتوزيع البيرول"] + (["👥 إدارة المستخدمين"] if is_admin else [])
    page = st.radio("الصفحات", pages, label_visibility="collapsed")
    if st.button("تسجيل الخروج", use_container_width=True):
        st.session_state.user = None
        st.rerun()

if page == "👥 إدارة المستخدمين":
    render_users_admin(UserStore(SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, demo=DEMO_MODE), st.session_state.user)
    st.stop()

st.title("⚙️ نظام تهيئة وتوزيع استمارات البيرول الحكومي (الرقم القومي)")

c1, c2 = st.columns(2)
with c1:
    db_file = st.file_uploader("📁 ملف قاعدة البيانات الأساسية", type=["xlsx", "xls", "xlsm"])
with c2:
    input_file = st.file_uploader("📥 شيت توزيع الاستمارة (المجمع)", type=["xlsx", "xls", "xlsm"])

run = st.button("⚡ تشغيل الفرز والتوزيع التلقائي بالرقم القومي", type="primary", use_container_width=True,
                disabled=not (db_file and input_file))

if run:
    with st.spinner("جارٍ الفرز والتوزيع..."):
        try:
            excel_bytes, summary_df, merged, amount_col = split_payroll(db_file, input_file)
            file_name = f"توزيع_البيرول_{datetime.now():%Y-%m-%d_%H-%M}.xlsx"
            st.session_state.result = (excel_bytes, summary_df, merged, amount_col, file_name)
            log_run(st.session_state.user, summary_df, file_name)
        except PayrollError as e:
            st.session_state.result = None
            st.error(str(e))
        except Exception as e:
            st.session_state.result = None
            st.error(f"حدث خطأ أثناء المعالجة: {e}")

if st.session_state.get("result"):
    excel_bytes, summary_df, merged, amount_col, file_name = st.session_state.result
    st.success(f"✅ تم توزيع {len(merged)} موظف على {len(summary_df)} شيت.")
    st.download_button("⬇️ تحميل ملف التوزيع (Excel)", data=excel_bytes, file_name=file_name,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", use_container_width=True)

    st.subheader("📊 ملخص الميزان المالي ومخرجات الفئات الموزعة")
    m1, m2, m3 = st.columns(3)
    m1.metric("عدد الفئات", len(summary_df))
    m2.metric("عدد الموظفين", int(summary_df["عدد الموظفين"].sum()))
    m3.metric("إجمالي المبلغ", f"{summary_df['إجمالي المبلغ'].sum():,.2f}")
    st.dataframe(summary_df.style.format({"إجمالي المبلغ": "{:,.2f}"}), use_container_width=True, hide_index=True)

    with st.expander("عرض البيانات المدموجة"):
        st.dataframe(merged, use_container_width=True, hide_index=True)
