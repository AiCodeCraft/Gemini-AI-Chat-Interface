import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import pandas as pd
import zipfile
import PyPDF2

# Konfiguration der Seite
st.set_page_config(page_title="Gemini AI Chat", layout="wide")

st.title("🤖 Gemini AI Chat Interface")
st.markdown("""
**Welcome to the Gemini AI Chat Interface!**
Chat seamlessly with Google's advanced Gemini AI models, supporting multiple input types.
🔗 [GitHub Profile](https://github.com/volkansah) | 
📂 [Project Repository](https://github.com/volkansah/gemini-ai-chat) | 
💬 [Soon](https://aicodecraft.io)
""")

# Session State Management
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_content" not in st.session_state:
    st.session_state.uploaded_content = None

# Funktionen zur Dateiverarbeitung
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def process_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type in ["jpg", "jpeg", "png"]:
        return {"type": "image", "content": Image.open(uploaded_file).convert('RGB')}
    
    code_extensions = ["html", "css", "php", "js", "py", "java", "c", "cpp"]
    if file_type in ["txt"] + code_extensions:
        return {"type": "text", "content": uploaded_file.read().decode("utf-8")}
    
    if file_type in ["csv", "xlsx"]:
        df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
        return {"type": "text", "content": df.to_string()}
    
    if file_type == "pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        return {"type": "text", "content": "".join(page.extract_text() for page in reader.pages if page.extract_text())}
    
    if file_type == "zip":
        with zipfile.ZipFile(uploaded_file) as z:  # <- Hier beginnt der Block
            newline = "\n"
            content = f"ZIP Contents:{newline}"
            
            text_extensions = ('.txt', '.csv', '.py', '.html', '.js', '.css', 
                              '.php', '.json', '.xml', '.c', '.cpp', '.java', 
                              '.cs', '.rb', '.go', '.ts', '.swift', '.kt', '.rs', '.sh', '.sql')
            
            for file_info in z.infolist():
                if not file_info.is_dir():
                    try:
                        with z.open(file_info.filename) as file:
                            if file_info.filename.lower().endswith(text_extensions):
                                file_content = file.read().decode('utf-8')
                                content += f"{newline}📄 {file_info.filename}:{newline}{file_content}{newline}"
                            else:
                                raw_content = file.read()
                                try:
                                    decoded_content = raw_content.decode('utf-8')
                                    content += f"{newline}📄 {file_info.filename} (unbekannte Erweiterung):{newline}{decoded_content}{newline}"
                                except UnicodeDecodeError:
                                    content += f"{newline}⚠️ Binärdatei ignoriert: {file_info.filename}{newline}"
                    except Exception as e:
                        content += f"{newline}❌ Fehler bei {file_info.filename}: {str(e)}{newline}"
            
            return {"type": "text", "content": content}  # Korrekt eingerückt
    
    return {"type": "error", "content": "Unsupported file format"}

# Sidebar für Einstellungen
with st.sidebar:
    api_key = st.text_input("Google AI API Key", type="password")
    model = st.selectbox("Model", [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-pro-vision-latest",  # Vision-Modell für Bilder
        "gemini-1.0-pro",
        "gemini-1.0-pro-vision-latest",  # Vision-Modell für Bilder
        "gemini-2.0-pro-exp-02-05",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-exp-image-generation",  # Vision-Modell für Bilder
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking-exp-01-21"
    ])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
    max_tokens = st.slider("Max Tokens", 1, 2048, 1000)

# Datei-Upload
uploaded_file = st.file_uploader("Upload File (Image/Text/PDF/ZIP)", 
                               type=["jpg", "jpeg", "png", "txt", "pdf", "zip", 
                                     "csv", "xlsx", "html", "css", "php", "js", "py"])

if uploaded_file:
    processed = process_file(uploaded_file)
    st.session_state.uploaded_content = processed
    
    if processed["type"] == "image":
        st.image(processed["content"], caption="Uploaded Image", use_container_width=True)
    elif processed["type"] == "text":
        st.text_area("File Preview", processed["content"], height=200)

# Chat-Historie anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat-Eingabe verarbeiten
if prompt := st.chat_input("Your message..."):
    if not api_key:
        st.warning("API Key benötigt!")
        st.stop()
    
    try:
        # API konfigurieren
        genai.configure(api_key=api_key)
        
        # Modell auswählen
        model_instance = genai.GenerativeModel(model)
        
        # Inhalt vorbereiten
        content = [{"text": prompt}]
        
        # Dateiinhalt hinzufügen
        if st.session_state.uploaded_content:
            if st.session_state.uploaded_content["type"] == "image":
                if "vision" not in model.lower():
                    st.error("Bitte ein Vision-Modell für Bilder auswählen!")
                    st.stop()
                content.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encode_image(st.session_state.uploaded_content["content"])
                    }
                })
            elif st.session_state.uploaded_content["type"] == "text":
                content[0]["text"] += f"\n\n[File Content]\n{st.session_state.uploaded_content['content']}"
        
        # Nachricht zur Historie hinzufügen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Antwort generieren
        response = model_instance.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        # Überprüfen, ob die Antwort gültig ist
        if not response.candidates:
            st.error("API Error: Keine gültige Antwort erhalten. Überprüfe die Eingabe oder das Modell.")
        else:
            # Antwort anzeigen
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        if "vision" not in model and st.session_state.uploaded_content["type"] == "image":
            st.error("Für Bilder einen Vision-fähigen Modell auswählen!")

# Instructions in the sidebar
with st.sidebar:
    st.markdown("""
    ## 📝 Instructions:
    1. Enter your Google AI API key
    2. Select a model (use vision models for image analysis)
    3. Adjust temperature and max tokens if needed
    4. Optional: Set a system prompt
    5. Upload an image (optional)
    6. Type your message and press Enter
    ### About
    🔗 [GitHub Profile](https://github.com/volkansah) | 
    📂 [Project Repository](https://github.com/volkansah/gemini-ai-chat) | 
    💬 [Soon](https://aicodecraft.io)
    """)
