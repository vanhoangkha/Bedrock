import streamlit as st 
import Libs as glib 
from PyPDF2 import PdfReader
import Libs as glib 
import base

st.set_page_config(page_title="Tóm tắt tài liệu", page_icon="img/favicon.ico", layout="wide")
st.title('Tóm tắt tài liệu')

base.init_slidebar()
base.init_animation()

uploaded_file = st.file_uploader("Tải tài liệu định dạng PDF")
docs = []

if uploaded_file is not None:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        docs.append(page.extract_text())

    response = glib.summary_stream(docs)
    st.write_stream(response)
   