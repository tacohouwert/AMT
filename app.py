import streamlit as st
from pyairtable import Table

# Airtable connectie
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]
TABLE_NAME = st.secrets["TABLE_NAME"]

table = Table(AIRTABLE_TOKEN, BASE_ID, TABLE_NAME)

st.title("Elana® Form Submission")

name = st.text_input("Name")
email = st.text_input("Email")
feedback = st.text_area("Your feedback")

if st.button("Submit"):
    if name and email:
        table.create({
            "Name": name,
            "Email": email,
            "Feedback": feedback
        })
        st.success("Thanks for your feedback!")
    else:
        st.warning("Please enter both name and email.")
