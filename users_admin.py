"""شاشة إدارة المستخدمين وكلمات المرور (جدول Supabase)."""
import pandas as pd
import requests
import streamlit as st

STATUS_ACTIVE = "Active"
STATUS_BLOCKED = "Blocked"


class UserStore:
    """CRUD على جدول المستخدمين عبر Supabase REST. في الوضع التجريبي يُخزَّن في الجلسة فقط."""

    def __init__(self, url, key, table, demo=False):
        self.url = f"{url.rstrip('/')}/rest/v1/{table}"
        self.key = key
        self.demo = demo
        if demo and "demo_users" not in st.session_state:
            st.session_state.demo_users = [
                {"username": "admin", "password": "1234", "status": STATUS_ACTIVE},
                {"username": "ahmed", "password": "abcd", "status": STATUS_BLOCKED},
            ]

    def _headers(self, prefer=None):
        h = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if prefer:
            h["Prefer"] = prefer
        return h

    def _check(self, r):
        if r.status_code >= 300:
            raise RuntimeError(f"خطأ من Supabase ({r.status_code}): {r.text[:300]}")

    def list_users(self):
        if self.demo:
            return list(st.session_state.demo_users)
        r = requests.get(self.url, headers=self._headers(), params={"select": "username,password,status", "order": "username"}, timeout=15)
        self._check(r)
        return r.json()

    def add_user(self, username, password, status=STATUS_ACTIVE):
        if self.demo:
            if any(u["username"] == username for u in st.session_state.demo_users):
                raise RuntimeError("اسم المستخدم موجود بالفعل!")
            st.session_state.demo_users.append({"username": username, "password": password, "status": status})
            return
        r = requests.post(self.url, headers=self._headers("return=minimal"), json={"username": username, "password": password, "status": status}, timeout=15)
        if r.status_code == 409:
            raise RuntimeError("اسم المستخدم موجود بالفعل!")
        self._check(r)

    def update_user(self, username, **fields):
        if self.demo:
            for u in st.session_state.demo_users:
                if u["username"] == username:
                    u.update(fields)
            return
        r = requests.patch(self.url, headers=self._headers("return=minimal"), params={"username": f"eq.{username}"}, json=fields, timeout=15)
        self._check(r)

    def delete_user(self, username):
        if self.demo:
            st.session_state.demo_users = [u for u in st.session_state.demo_users if u["username"] != username]
            return
        r = requests.delete(self.url, headers=self._headers("return=minimal"), params={"username": f"eq.{username}"}, timeout=15)
        self._check(r)


def render_users_admin(store: UserStore, current_user: str):
    st.title("👥 إدارة المستخدمين وكلمات المرور")

    try:
        users = store.list_users()
    except Exception as e:
        st.error(f"تعذر تحميل المستخدمين: {e}")
        return

    # ---- إضافة مستخدم جديد ----
    with st.expander("➕ إضافة مستخدم جديد", expanded=not users):
        with st.form("add_user", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            new_user = c1.text_input("اسم المستخدم")
            new_pass = c2.text_input("كلمة المرور", type="password")
            new_status = c3.selectbox("الحالة", [STATUS_ACTIVE, STATUS_BLOCKED])
            if st.form_submit_button("إضافة", type="primary", use_container_width=True):
                if not new_user.strip() or not new_pass:
                    st.warning("اكتب اسم المستخدم وكلمة المرور.")
                else:
                    try:
                        store.add_user(new_user.strip(), new_pass, new_status)
                        st.success(f"تمت إضافة المستخدم {new_user.strip()}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    if not users:
        st.info("لا يوجد مستخدمون بعد.")
        return

    # ---- جدول المستخدمين ----
    df = pd.DataFrame(users)
    df["password"] = df["password"].astype(str).str.replace(r".", "•", regex=True)
    df = df.rename(columns={"username": "اسم المستخدم", "password": "كلمة المرور", "status": "الحالة"})
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- تعديل مستخدم ----
    st.subheader("✏️ تعديل مستخدم")
    names = [u["username"] for u in users]
    selected = st.selectbox("اختر المستخدم", names)
    user = next(u for u in users if u["username"] == selected)
    is_self = selected == current_user

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.form("change_pass"):
            st.markdown("**تغيير كلمة المرور**")
            p1 = st.text_input("كلمة المرور الجديدة", type="password")
            p2 = st.text_input("تأكيد كلمة المرور", type="password")
            if st.form_submit_button("حفظ", use_container_width=True):
                if not p1:
                    st.warning("اكتب كلمة المرور الجديدة.")
                elif p1 != p2:
                    st.error("كلمتا المرور غير متطابقتين.")
                else:
                    try:
                        store.update_user(selected, password=p1)
                        st.success("تم تغيير كلمة المرور.")
                    except Exception as e:
                        st.error(str(e))

    with c2:
        st.markdown("**الحالة**")
        blocked = user.get("status") == STATUS_BLOCKED
        st.write("🚫 محظور" if blocked else "✅ مفعّل")
        label = "تفعيل الحساب" if blocked else "حظر الحساب"
        if st.button(label, use_container_width=True, disabled=is_self and not blocked):
            try:
                store.update_user(selected, status=STATUS_ACTIVE if blocked else STATUS_BLOCKED)
                st.rerun()
            except Exception as e:
                st.error(str(e))
        if is_self:
            st.caption("لا يمكنك حظر حسابك الحالي.")

    with c3:
        st.markdown("**حذف المستخدم**")
        confirm = st.checkbox("أؤكد الحذف النهائي", key=f"del_{selected}")
        if st.button("🗑️ حذف", use_container_width=True, disabled=not confirm or is_self):
            try:
                store.delete_user(selected)
                st.rerun()
            except Exception as e:
                st.error(str(e))
        if is_self:
            st.caption("لا يمكنك حذف حسابك الحالي.")
