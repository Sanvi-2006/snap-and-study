import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
import smtplib
from email.message import EmailMessage
import re

def send_email(recipient_email, explanation):
    msg = EmailMessage()
    msg["Subject"] = "Snap & Study - Study Explanation"
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = recipient_email

    clean_explanation = explanation.replace("*", "")
    clean_explanation = re.sub(r'(?m)^#+\s*', '', clean_explanation)
    clean_explanation = re.sub(r'(?m)^---+\s*$', '', clean_explanation)
    clean_explanation = re.sub(r'(?m)^\|---.*\|$', '', clean_explanation)
    clean_explanation = clean_explanation.replace("|", "   ")

    msg.set_content(clean_explanation)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            st.secrets["EMAIL_ADDRESS"],
            st.secrets["EMAIL_APP_PASSWORD"]
        )
        smtp.send_message(msg)

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚"
)

st.title("📚 Snap & Study")
st.write("Your AI Study Assistant - Learn smarter, one question at a time.")

st.divider()

if "explanation" not in st.session_state:
    st.session_state.explanation = ""

# Gemini API key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Create Gemini client
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,
            initial_delay=1,
            max_delay=30,
            http_status_codes=[408, 429, 500, 502, 503, 504]
        )
    )
)

# User question
question = st.text_area(
    "📝 Ask your study question",
    placeholder="Example: Explain the OSI model in simple words.",
    height=120
)

# Image upload
uploaded_file = st.file_uploader(
    "📷 Upload notes, question or diagram",
    type=["jpg", "jpeg", "png"],
    help="Upload a clear photo of your notes, question, or diagram."
)

if st.button("🤖 Get Explanation", type="primary", use_container_width=True):

    if not question and not uploaded_file:
        st.warning("Please enter a question or upload an image.")

    else:
        parts = []

        if uploaded_file:
            image_bytes = uploaded_file.getvalue()

            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=uploaded_file.type
                )
            )

        if question:
            parts.append(question)
        else:
            parts.append(
                "Explain this image in simple language "
                "and give an exam-friendly explanation."
            )

        with st.spinner("🤔 Studying..."):

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=parts,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                )
            )
            st.session_state.explanation = response.text

if st.session_state.explanation:
    st.divider()
    st.subheader("📖 Explanation")
    st.write(st.session_state.explanation)
    st.success("✅ Explanation generated successfully!")

    st.divider()
    st.subheader("📧 Share Explanation")

    recipient_email = st.text_input(
        "Enter email address",
        placeholder="student@example.com",
        help="Send the generated explanation to your email."
    )

    if st.button("📨 Send Email", use_container_width=True):
        if not recipient_email:
            st.warning("Please enter an email address.")
        else:
            try:
                send_email(
                    recipient_email,
                    st.session_state.explanation
                )
                st.success("Explanation sent successfully!")
            except Exception as e:
                st.error(f"Could not send email: {e}")