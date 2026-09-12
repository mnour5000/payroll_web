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
