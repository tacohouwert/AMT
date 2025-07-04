import streamlit as st
from pyairtable import Table
from pyairtable.formulas import match

# Secrets ophalen
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]
QUESTIONS_TABLE = "Questions"

# Connectie maken
table = Table(AIRTABLE_TOKEN, BASE_ID, QUESTIONS_TABLE)

# Vragen ophalen
records = table.all()
questions = [r for r in records if not r['fields'].get('Answers')]

if not questions:
    st.success("Alle vragen zijn al beantwoord ✅")
    st.stop()

# Een vraag per keer tonen
index = st.session_state.get("q_index", 0)

if index >= len(questions):
    st.success("Je hebt alle vragen behandeld.")
    st.stop()

q = questions[index]
q_id = q['id']
q_text = q['fields'].get("Question", "Geen vraagtekst")

st.header("Beantwoord de volgende vraag:")
st.write(f"**{q_text}**")

answer = st.text_area("Antwoord", key="answer")

# Ophalen van linked tables (optioneel: cache als performance belangrijk wordt)
companies_table = Table(AIRTABLE_TOKEN, BASE_ID, "Companies")
companies = companies_table.all()
company_names = [c["fields"]["Name"] for c in companies]
selected_company = st.selectbox("Selecteer bedrijf", [""] + company_names)

robots_table = Table(AIRTABLE_TOKEN, BASE_ID, "Robots")
robots = robots_table.all()
robot_names = [r["fields"]["Name"] for r in robots]
selected_robot = st.selectbox("Selecteer robot", [""] + robot_names)

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

        # Linken aan de juiste records in Companies en Robots
        if selected_company:
            matching = [c for c in companies if c["fields"]["Name"] == selected_company]
            if matching:
                update_fields["Company"] = [matching[0]["id"]]

        if selected_robot:
            matching = [r for r in robots if r["fields"]["Name"] == selected_robot]
            if matching:
                update_fields["Robot"] = [matching[0]["id"]]

        table.update(q_id, update_fields)
        st.success("Opgeslagen!")
        st.session_state.q_index = index + 1
        st.experimental_rerun()
