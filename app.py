import logging
import streamlit as st
from pyairtable import Table

# Logging (voor debug)
logging.basicConfig(level=logging.DEBUG)

# Secrets ophalen
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]
QUESTIONS_TABLE = "Questions"

# Connectie met Airtable
table = Table(AIRTABLE_TOKEN, BASE_ID, QUESTIONS_TABLE)

# Vragen ophalen (met foutafhandeling)
try:
    records = table.all()
except Exception as e:
    st.error(f"Fout bij ophalen van vragen: {e}")
    st.write("→ Controleer of je tabelnaam exact klopt met Airtable.")
    st.stop()


# Filter vragen zonder antwoord
questions = [r for r in records if not r['fields'].get('Answers')]

if not questions:
    st.success("Alle vragen zijn al beantwoord ✅")
    st.stop()

# Een vraag per keer
index = st.session_state.get("q_index", 0)

if index >= len(questions):
    st.success("Je hebt alle vragen behandeld.")
    st.stop()

q = questions[index]
q_id = q['id']
q_text = q['fields'].get("Question", "Geen vraagtekst")

st.header("Beantwoord de volgende vraag:")
st.write(f"**{q_text}**")

# Antwoordveld
answer = st.text_area("Antwoord", key="answer")

# Robotic System dropdown
robotic_system = st.selectbox(
    "Robotic System",
    [""] + ["Da Vinci", "Hugo", "Symani", "Andere"]
)

# Actieknoppen
col1, col2 = st.columns(2)

with col1:
    if st.button("Skip"):
        st.session_state.q_index = index + 1
        st.experimental_rerun()

with col2:
    if st.button("Opslaan"):
        update_fields = {
            "Answers": answer,
            "Robotic System": robotic_system
        }

        table.update(q_id, update_fields)
        st.success("Opgeslagen!")
        st.session_state.q_index = index + 1
        st.experimental_rerun()
