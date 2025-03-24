import streamlit as st
import pandas as pd
import math
import bcrypt
import google.generativeai as genai

# Configure Google Gemini API
GEMINI_API_KEY = "AIzaSyCFbnID7J4KnD-hoveRc37CEx_MV9eXUEk"
genai.configure(api_key=GEMINI_API_KEY)

# Authentication Module
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

users = {
    "admin": {
        "name": "Admin",
        "password": hash_password("admin123")  # Hashed password
    }
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
            st.session_state.authenticated = True
            st.success(f"Welcome {users[username]['name']}!")
            st.rerun()
        else:
            st.error("Username/password is incorrect")
else:
    # Data Loading Module
    @st.cache_data
    def load_data(uploaded_file):
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name="Main-Data")
            df.columns = df.iloc[0]  # Set first row as column headers
            df = df[1:].reset_index(drop=True)  # Cleaned data
            df.columns = df.columns.str.strip().str.lower()
            numeric_cols = ["speed (rpm)", "power (kw)"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df.dropna(subset=numeric_cols)
        return None

    # User Interface Module
    st.title("Flexible Disc Coupling Finder")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df = load_data(uploaded_file)
        st.success("File uploaded successfully!")
    else:
        df = None
        st.warning("Please upload an Excel file to proceed.")

    speed_min = st.number_input("Enter Minimum Speed (RPM)", min_value=0, step=10)
    speed_max = st.number_input("Enter Maximum Speed (RPM)", min_value=speed_min, step=10)
    power_min = st.number_input("Enter Minimum Power (kW)", min_value=0.0, step=0.1)
    power_max = st.number_input("Enter Maximum Power (kW)", min_value=power_min, step=0.1)

    # Coupling Matching Module with Gemini AI
    if st.button("Find Best Coupling") and df is not None:
        df_filtered = df[(df["speed (rpm)"].between(speed_min, speed_max)) & (df["power (kw)"].between(power_min, power_max))]
        
        if not df_filtered.empty:
            st.success("Best Matching Couplings:")
            for _, row in df_filtered.iterrows():
                st.write("Coupling Suggestion:")
                st.write(row.to_dict())
                st.markdown("---")
            
            # Generate additional insights using Gemini API
            prompt = f"Suggest the best coupling based on the following data: {df_filtered.to_dict(orient='records')}"
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            st.subheader("AI Recommendation:")
            st.write(response.text)

        else:
            st.error("No matches found within the given range.")
