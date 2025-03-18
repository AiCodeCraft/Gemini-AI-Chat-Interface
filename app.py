# Copyright Volkan Kücükbudak
# Github: https://github.com/volkansah
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64

st.set_page_config(page_title="Gemini AI Chat", layout="wide")

st.title("🤖 Gemini AI Chat Interface")
st.markdown("""
**Welcome to the Gemini AI Chat Interface!**
Chat seamlessly with Google's advanced Gemini AI models, supporting both text and image inputs.
🔗 [GitHub Profile](https://github.com/volkansah) | 
📂 [Project Repository](https://github.com/volkansah/gemini-ai-chat) | 
💬 [Soon](https://aicodecraft.io)

Follow me for more innovative projects and updates!
""")


def encode_image(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    image_bytes = buffered.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    return encoded_image

# Sidebar for settings
with st.sidebar:
    api_key = st.text_input("Enter Google AI API Key", type="password")
    model = st.selectbox(
        "Select Model",
        [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash-8B",
            "gemini-1.5-pro-vision-latest",
            "gemini-1.0-pro",
            "gemini-1.0-pro-vision-latest",

            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-exp-image-generation",
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking-exp-01-21"
        ]
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
    max_tokens = st.slider("Max Tokens", 1, 2048, 1000000)
    system_prompt = st.text_area("System Prompt (Optional)")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# File uploader for images
uploaded_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
uploaded_image = None
if uploaded_file is not None:
    uploaded_image = Image.open(uploaded_file).convert('RGB')
    st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input and api_key:
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare the model and content
        model_instance = genai.GenerativeModel(model_name=model)
        
        content = []
        if uploaded_image:
            # Convert image to base64
            encoded_image = encode_image(uploaded_image)
            content = [
                {"text": user_input},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        else:
            content = [{"text": user_input}]

        # Generate response
        response = model_instance.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error("If using an image, make sure to select a vision-enabled model (ones with 'vision' in the name)")

elif not api_key and user_input:
    st.warning("Please enter your API key in the sidebar first.")

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
