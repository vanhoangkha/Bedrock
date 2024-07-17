import streamlit as st

pg = st.navigation([
    st.Page("home.py", title="Home", icon="🏠"),
    st.Page("pages/document_summary.py", title="Tóm tắt tài liệu", icon=":material/local_offer:"),
    st.Page("pages/document_answer.py", title="Hỏi đáp về tài liệu", icon=":material/favorite:"),
    st.Page("pages/stock_analytics.py", title="Phân tích kỹ thuật", icon=":material/work:"),
    st.Page("pages/stock_advisor.py", title="Tư vấn cổ phiếu RAG", icon=":material/attach_money:"),
    st.Page("pages/stock_agent.py", title="Tư vấn cổ phiếu AGENT", icon=":material/lock_open:"),
])
pg.run()
