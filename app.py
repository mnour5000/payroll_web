import os
import re
import pandas as pd


# ============================================================
# دوال مساعدة
# ============================================================

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
# قراءة قاعدة البيانات الأساسية
# ============================================================

def read_database(db_file_path):

    df_db = None
    db_employee_col = None

    for skip in range(0, 15):

        try:

            df_temp = pd.read_excel(
                db_file_path,
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


# ============================================================
# قراءة شيت توزيع الاستمارة
# ============================================================

def read_input_file(input_file_path):

    df_raw = pd.read_excel(
        input_file_path,
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
        input_file_path,
        skiprows=header_row_index,
        keep_default_na=False
    )

    df_input = prepare_dataframe_columns(
        df_input
    )

    # --------------------------------------------------------
    # رقم الموظف = رقم الصرف
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # الرقم القومي
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # نوع التعيين
    # --------------------------------------------------------

    input_category_col = find_column(
        df_input,
        [
            "نوع التعيين",
            "نوع_التعيين",
            "التعيين"
        ]
    )

    # --------------------------------------------------------
    # المبلغ
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # تنظيف رقم الموظف
    # --------------------------------------------------------

    df_input[input_employee_col] = (
        df_input[input_employee_col]
        .apply(clean_employee_number)
    )

    # --------------------------------------------------------
    # تنظيف الرقم القومي
    # --------------------------------------------------------

    if input_id_col:

        df_input[input_id_col] = (
            df_input[input_id_col]
            .apply(clean_id)
        )

    # --------------------------------------------------------
    # المبلغ
    # --------------------------------------------------------

    if input_amount_col:

        df_input[input_amount_col] = (
            df_input[input_amount_col]
            .apply(normalize_amount)
        )

    else:

        input_amount_col = "إجمالي المبالغ"

        df_input[input_amount_col] = 0.0

    # --------------------------------------------------------
    # نوع التعيين
    # --------------------------------------------------------

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


# ============================================================
# المطابقة مع قاعدة البيانات
# ============================================================

def match_with_database(
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

        # ----------------------------------------------------
        # رقم الصرف فارغ
        # ----------------------------------------------------

        if not employee_number:

            output_row[
                "حالة المطابقة"
            ] = ""

        # ----------------------------------------------------
        # موجود في قاعدة البيانات
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # غير موجود في قاعدة البيانات
        # ----------------------------------------------------

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


# ============================================================
# حساب إجمالي المبالغ
# ============================================================

def calculate_total_amounts(df):

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

    # --------------------------------------------------------
    # مكافآت أخرى
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # الإشراف
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # التدريس
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # التصحيح
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # الإجمالي
    # --------------------------------------------------------

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


# ============================================================
# إنشاء شيت المكافآت
# ============================================================

def create_reward_sheet(
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


# ============================================================
# تصدير النتائج
# ============================================================

def export_results(
    matched_df,
    category_col,
    amount_col,
    output_dir
):

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

    # --------------------------------------------------------
    # الأعمدة الأساسية
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # حساب إجمالي المبالغ
    # --------------------------------------------------------

    matched_df = (
        calculate_total_amounts(
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

    # --------------------------------------------------------
    # تحديد عمود رقم الصرف
    # --------------------------------------------------------

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

    # ========================================================
    # تحديد السحب الجديد
    # ========================================================

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

    # ========================================================
    # ملف سحب جديد مستقل
    # ========================================================

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

    # ========================================================
    # ملفات الفئات العادية
    # ========================================================

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

    # ========================================================
    # التوزيع الشامل
    # ========================================================

    all_file = os.path.join(
        result_dir,
        "التوزيع_الشامل.xlsx"
    )

    with pd.ExcelWriter(
        all_file,
        engine="openpyxl"
    ) as writer:

        # ----------------------------------------------------
        # كل البيانات
        # ----------------------------------------------------

        matched_df.to_excel(
            writer,
            sheet_name="كل البيانات",
            index=False
        )

        # ----------------------------------------------------
        # سحب جديد
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # مكافأة الإشراف
        # ----------------------------------------------------

        create_reward_sheet(
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

        # ----------------------------------------------------
        # مكافأة التصحيح
        # ----------------------------------------------------

        create_reward_sheet(
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

        # ----------------------------------------------------
        # مكافأة التدريس
        # ----------------------------------------------------

        create_reward_sheet(
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

    # ========================================================
    # ملف الملخص
    # ========================================================

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

    # ========================================================
    # إضافة السحب الجديد
    # ========================================================

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

    # ========================================================
    # تنسيق إجمالي المبلغ
    # ========================================================

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
    import streamlit as st
import pandas as pd
import os

# 1. ضبط إعدادات وعناوين الواجهة الفخمة للموقع على المتصفح
st.set_page_config(
    page_title="منظومة البيرول الحكومي لتوزيع استمارات الرقم القومي",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق التنسيق والـ CSS لتظهر الواجهة باللون الأخضر والـ Dark Mode الفخم
st.markdown("""
    <style>
    .main-title { font-size:28px !important; font-weight: bold; text-align: center; color: #28a745; margin-bottom: 20px; }
    .section-title { font-size:18px !important; font-weight: bold; color: #17a2b8; margin-top: 10px; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #1e7e34; color: white; }
    .stButton>button:hover { background-color: #155724; color: white; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚙️ نظام تهيئة وتوزيع استمارات البيرول الحكومي</div>', unsafe_allow_html=True)
st.write("---")

# 2. إنشاء إطار رفع الملفات الذكي أمام عينك في الواجهة
st.markdown('<div class="section-title">📁 منطقة رفع وتجهيز استمارات البيرول (الملفات الحية):</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.info("📄 قاعدة البيانات الأساسية للموظفين")
    db_file = st.file_uploader("اختر ملف قاعدة البيانات الأساسية (data new)", type=["xlsx", "xls", "xlsm"], key="db")

with col2:
    st.info("📥 شيت توزيع الاستمارة المجمع")
    input_file = st.file_uploader("اختر الشيت المجمع المراد تفريعه وتفكيكه فئات", type=["xlsx", "xls", "xlsm"], key="input")

st.write("---")

# 3. زر الفرز والتشغيل والانطلاق التاريخي بلمشة زر
if st.button("⚡ تشغيل الفرز والتوزيع التلقائي برقم الصرف والقومي"):
    if db_file is not None and input_file is not None:
        with st.spinner("⏳ جاري الفرز والتطهير وعزل موظفي الخارج الآن..."):
            try:
                # الاستدعاء العبقري للمحرك والألف سطر المكتوبين بداخل ملف payroll_core.py
                import payroll_core
                
                # تشغيل دالة الفرز السحابية المدمجة
                output_buffer, summary_data = payroll_core.process_payroll_splitting_web(db_file, input_file)
                
                st.success("🎉 مبروك يا هندسة! تم الحسم وتطهير الموازنة المادية وعزل الخارج بنجاح مطلق واختفت الـ #N/A!")
                
                # زر التحميل السحري لتحميل ملف الإكسيل الموزع مباشرة على الكمبيوتر
                st.download_button(
                    label="📥 تحميل ملف الاستمارات الموزعة تلقائياً جاهز للبيرول",
                    data=output_buffer,
                    file_name="استمارات_البيرول_الموزعة_تلقائياً.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # 4. رسم جدول الملخص الرسومي والميزان المالي الحكومي (بديل الـ Treeview المطور للويب)
                st.write("")
                st.markdown('<div class="section-title">📊 ملخص الميزان المالي ومخرجات الفئات الموزعة تلقائياً:</div>', unsafe_allow_html=True)
                
                df_summary = pd.DataFrame(summary_data)
                if not df_summary.empty:
                    df_summary.columns = ["اسم الفئة الموزعة (اسم الشيت)", "عدد الموظفين الفعلي", "إجمالي المبالغ بالقرش"]
                    # عرض الجدول منسقاً وكبيراً أمامك
                    st.dataframe(df_summary.style.format({"إجمالي المبالغ بالقرش": "{:,.2f}"}), use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ حدث تداخل غير متوقع أثناء معالجة وقش الملفات الحالية:\n{str(e)}")
    else:
        st.warning("⚠️ يرجى التأكد من اختيار ورفع الملفين معاً أولاً في خانات الرفع بالأعلى!")

# تذييل الصفحة باسم المطور
st.write("---")
st.caption("تصميم وتطوير: مهندس محمد سيد | نظام حوكمة وتفريع استمارات البيرول السحابية الموحدة © 2026")
