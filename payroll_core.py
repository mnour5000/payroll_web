"""منطق فرز وتوزيع استمارات البيرول بالرقم القومي (مستقل عن الواجهة)."""
import io
import pandas as pd

ID_KEYWORDS = ['قوم', 'الرقم', 'الهوية']
INPUT_ID_KEYWORDS = ['قوم', 'الرقم', 'الهوية', 'كود', 'صرف']
AMOUNT_KEYWORDS = ['مبلغ', 'المبلغ', 'جملة', 'الجملة', 'صافي', 'الصافي', 'قيمة', 'القيمة', 'مكافأة']
CATEGORY_KEYWORDS = ['فئة', 'الفئة', 'جهة', 'الجهة', 'إدارة', 'ادارة', 'قسم', 'مدرسة', 'وظيفة', 'الوظيفة', 'درجة', 'الدرجة', 'شيت', 'تصنيف']

UNMATCHED_LABEL = "غير موجود بقاعدة البيانات"


class PayrollError(Exception):
    pass


def _find_col(columns, keywords):
    for col in columns:
        if any(k in col for k in keywords):
            return col
    return None


def _clean_id(series):
    return series.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)


def _safe_sheet_name(name, used):
    name = str(name).strip() or "بدون فئة"
    for ch in '[]:*?/\\':
        name = name.replace(ch, '-')
    name = name[:31]
    base, i = name, 2
    while name in used:
        suffix = f"_{i}"
        name = base[:31 - len(suffix)] + suffix
        i += 1
    used.add(name)
    return name


def load_db(file):
    for skip in range(0, 15):
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            df = pd.read_excel(file, skiprows=skip)
        except Exception:
            continue
        df.columns = df.columns.astype(str).str.strip()
        id_col = _find_col(df.columns, ID_KEYWORDS)
        if id_col:
            return df, id_col
    raise PayrollError("لم نتمكن من العثور على عمود الرقم القومي داخل ملف قاعدة البيانات!")


def load_input(file):
    for skip in range(0, 15):
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            df = pd.read_excel(file, skiprows=skip)
        except Exception:
            continue
        df.columns = df.columns.astype(str).str.strip()
        id_col = _find_col(df.columns, INPUT_ID_KEYWORDS)
        if not id_col:
            continue
        amount_col = _find_col(df.columns, AMOUNT_KEYWORDS) or df.columns[-1]
        return df, id_col, amount_col
    raise PayrollError("لم نتمكن من تحديد الأعمدة؛ يرجى مراجعة عناوين الشيت المجمع.")


def split_payroll(db_file, input_file, category_col=None):
    """يعيد (bytes ملف Excel, DataFrame الملخص, DataFrame المدموج, اسم عمود المبلغ)."""
    df_db, db_id_col = load_db(db_file)
    df_db[db_id_col] = _clean_id(df_db[db_id_col])

    df_input, input_id_col, amount_col = load_input(input_file)
    df_input[input_id_col] = _clean_id(df_input[input_id_col])
    df_input[amount_col] = pd.to_numeric(df_input[amount_col], errors='coerce').fillna(0)

    if not category_col:
        category_col = _find_col([c for c in df_db.columns if c != db_id_col], CATEGORY_KEYWORDS)
    if not category_col or category_col not in df_db.columns:
        raise PayrollError("لم نتمكن من العثور على عمود الفئة/الجهة في قاعدة البيانات لتوزيع الموظفين عليه!")

    df_db_unique = df_db.drop_duplicates(subset=[db_id_col])
    merged = df_input.merge(
        df_db_unique[[db_id_col, category_col]],
        left_on=input_id_col, right_on=db_id_col, how="left", suffixes=("", "_db")
    )
    if db_id_col != input_id_col and db_id_col in merged.columns:
        merged = merged.drop(columns=[db_id_col])
    merged[category_col] = merged[category_col].fillna(UNMATCHED_LABEL).astype(str).str.strip()

    summary_rows = []
    used_names = set()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for category, group in merged.groupby(category_col, sort=True):
            sheet = _safe_sheet_name(category, used_names)
            group.drop(columns=[category_col]).to_excel(writer, sheet_name=sheet, index=False)
            summary_rows.append((category, len(group), float(group[amount_col].sum())))

        summary_df = pd.DataFrame(summary_rows, columns=["الفئة", "عدد الموظفين", "إجمالي المبلغ"])
        total_row = pd.DataFrame([["الإجمالي العام", summary_df["عدد الموظفين"].sum(), summary_df["إجمالي المبلغ"].sum()]], columns=summary_df.columns)
        pd.concat([summary_df, total_row], ignore_index=True).to_excel(writer, sheet_name=_safe_sheet_name("ملخص", used_names), index=False)

    buffer.seek(0)
    return buffer.getvalue(), summary_df, merged, amount_col
