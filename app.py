import streamlit as st
import tempfile
import pandas as pd
from utils.update import process_file_gpt
from utils.update_ollama import process_file_ollama
from io import BytesIO

if "llm_option" not in st.session_state:
    st.session_state.llm_option = "GPT"
    
st.session_state.llm_option = st.selectbox(
    "Which LLM?",
    ("GPT", "Ollama"),
)
# File uploader
document = st.file_uploader(label="Upload Excel Sheet:", type=['xlsx'])
if "excel_data" not in st.session_state:
    st.session_state['excel_data'] = None
if "uploaded_file" not in st.session_state:
    st.session_state['uploaded_file'] = None  
if "result" not in st.session_state:
    st.session_state['result'] = None    
if document:
    if st.button("Process"):
        st.session_state['uploaded_file'] = [document.name,document.getvalue()]
        # Process the uploaded file
        with st.status(label="Processing...",expanded=True) as status:
            status.update(label="Started")
            with tempfile.NamedTemporaryFile(prefix=st.session_state['uploaded_file'][0], suffix='.xlsx') as temp_file:
                temp_file.write(st.session_state['uploaded_file'][1])
                if st.session_state.llm_option=="GPT":
                    st.session_state['result'] = process_file_gpt(temp_file, status)
                elif st.session_state.llm_option=="Ollama":
                    st.session_state['result'] = process_file_ollama(temp_file, status)    
                status.update(
                label="Process complete!", state="complete", expanded=False
                )
        
        # Convert DataFrame to Excel and provide download button
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data

        st.session_state['excel_data'] = (convert_df_to_excel(st.session_state['result']))

if st.session_state['excel_data']:
    st.download_button(
        label="Download Processed Data as Excel",
        data=st.session_state['excel_data'],
        file_name="processed_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    # Display the result
    st.write(st.session_state['result'])
