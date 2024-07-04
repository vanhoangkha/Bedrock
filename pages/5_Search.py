import streamlit as st 
import Libs as glib 
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.set_page_config(page_title="Search Knowledge base")
st.markdown("Đánh giá cổ phiếu ACB") 
st.markdown("Phân tích tình hình tài chính công ty HPG") 
st.markdown("Định giá cổ phiếu VND theo phương pháp chiết khấu dòng tiền") 

input_text = st.text_input("Search Knowledge base") 
if input_text: 
    st_callback = StreamlitCallbackHandler(st.container())
    response = glib.search(input_text, st_callback) 
    st.write(response["result"])
    st.write(response)
    
