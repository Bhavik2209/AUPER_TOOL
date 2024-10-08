import streamlit as st
import PyPDF2
from gtts import gTTS
import google.generativeai as genai
import re
from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu
import time
import os

GOOGLE_API_KEY = st.secrets['default']['GOOGLE_API_KEY']

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    return text

def clean_text(text):
    # Remove special characters like * or @
    text = re.sub(r"[*@#^&(){}\[\]:;<>,.!?]", "", text)
    
    # Optionally, replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def chunk_text(text, chunk_size=3000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    for word in words:
        if current_size + len(word) > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def summarize_with_gemini(text):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"Please provide a detailed summary of the following text. Note that this summary will be used to convert into an audio podcast, so write accordingly, explaining all key points in simple words:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def text_to_speech_gtts(text, output_file, language='en'):
    # Clean the text to remove special characters
    cleaned_text = clean_text(text)
    
    # Generate speech from cleaned text
    tts = gTTS(cleaned_text, lang=language)
    tts.save(output_file)


# Set page config
st.set_page_config(page_title="Research Paper to Audio", layout="wide", page_icon="🔊")

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
    }
    .uploadedFile {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .css-1kyxreq {
        justify-content: center;
    }
    .st-emotion-cache-nahz7x {
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    selected = option_menu("Menu", ["Home", "About"], 
        icons=['house', 'info-circle'], menu_icon="list", default_index=0)

# Main app
if selected == "Home":
    st.title("📑➜🔊 Research Paper to Audio Converter")

    col1, col2 = st.columns([2, 1])

    with col1:
        with stylable_container(
            key="file_uploader",
            css_styles=""""""
        ):
            uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

        if uploaded_file is not None:
            st.success("File uploaded successfully!")
            
            with st.expander("File Details"):
                st.write(f"Filename: {uploaded_file.name}")
                st.write(f"File size: {uploaded_file.size} bytes")

            output_file = st.text_input("Enter output file name (including .mp3 extension)", "output.mp3")
            
            if st.button("Convert to Audio", key="convert"):
                with st.spinner("Converting... This may take a few minutes."):
                    # Create a progress bar
                    progress_bar = st.progress(0)
                    
                    # Extract text from PDF
                    text = extract_text_from_pdf(uploaded_file)
                    progress_bar.progress(20)
                    
                    # Chunk the text
                    chunks = chunk_text(text)
                    progress_bar.progress(40)
                    
                    # Generate summary for each chunk
                    full_summary = ""
                    for i, chunk in enumerate(chunks):
                        chunk_summary = summarize_with_gemini(chunk)
                        full_summary += chunk_summary + "\n\n"
                        progress_bar.progress(40 + (i + 1) * 30 // len(chunks))
                    
                    # Convert summary to speech using gTTS
                    text_to_speech_gtts(full_summary, output_file)
                    progress_bar.progress(100)
                    
                    time.sleep(1)  # Give users a moment to see the 100% progress
                    st.success("Conversion complete!")
                    
                    # Offer file for download
                    with open(output_file, "rb") as file:
                        btn = st.download_button(
                            label="Download Audio",
                            data=file,
                            file_name=output_file,
                            mime="audio/mpeg"
                        )

    with col2:
        st.markdown("""
        ### How it works:
        1. Upload your PDF file
        2. Convert PDF file to Audio file.
        3. Download it 
        """)

elif selected == "About":
    st.title("About This App")
    st.write("""
    This app converts research papers (in PDF format) to audio files. It uses advanced AI to summarize the content
    and then converts the summary to speech. This tool is perfect for researchers, students, or anyone who wants to
    consume research papers in audio format.
    
    Enjoy listening to your research papers!
    """)

    st.info("For any issues or feature requests, please contact the developer (bhavikrohit22@gmail.com).")

# Footer
st.markdown("---")
st.markdown("Created with 🇦🇮 ✨ by Bhavik Rohit")