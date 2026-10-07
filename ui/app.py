import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.title("HR Service Request Triage")
st.caption("Suggestions require human review. The app does not perform external actions.")
api_url = os.getenv("API_URL", "http://localhost:8000")

with st.form("request"):
    subject = st.text_input("Subject", "Payslip access issue")
    text = st.text_area("Request", "I cannot open my March payslip in the employee portal.")
    submitted = st.form_submit_button("Analyze")

if submitted:
    try:
        response = httpx.post(
            api_url + "/api/analyze",
            json={"subject": subject, "text": text},
            timeout=75,
            trust_env=False,
        )
        response.raise_for_status()
        a = response.json()["analysis"]
        st.subheader(a["category"].title())
        st.write(f"Priority: **{a['priority']}**")
        st.write(a["summary"])
        st.write("Next action: " + a["next_action"])
        st.warning("Requires review. Nothing has been approved, sent or paid.")
    except httpx.HTTPStatusError as exc:
        st.error(f"API returned {exc.response.status_code}. Check the input or inference server.")
    except httpx.RequestError:
        st.error("API is unreachable. Check API_URL and the backend process.")

st.subheader("Recent results")
try:
    rows = httpx.get(api_url + "/api/history", timeout=10, trust_env=False).json()
    st.dataframe(
        [
            {"category": r["analysis"]["category"], "priority": r["analysis"]["priority"],
             "summary": r["analysis"]["summary"]}
            for r in rows
        ]
    )
except httpx.HTTPError:
    st.caption("History unavailable.")