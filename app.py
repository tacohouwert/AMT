import os
import logging
import streamlit as st
from pyairtable import Table

# Logging
logging.basicConfig(level=logging.DEBUG)

# Secrets ophalen
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]
QUESTIONS_TABLE = "Questions"

# Connectie maken met Questions-tabel
table = Table(AIRTABLE_TOKEN, BASE_ID, QUESTIONS_TABLE)

# Vraaggegevens ophalen
try:
    records = table.all()
except Exception as e:
    st.error(f"Fout bij ophalen van vragen: {e}")
    st.write("→ Controleer of je tabelnaam exact klopt met Airtable.")
    st.stop()

questions = [r for r in records if not r['fields'].get('Answers')]

if not questions:
    st.success("Alle vragen zijn al beantwoord ✅")
    st.stop()

# Huidige vraag bepalen
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

# Helperfunctie om naam op te halen bij ID
def get_name_by_id(records, record_id, name_field="Name"):
    for r in records:
        if r["id"] == record_id:
            return r["fields"].get(name_field, "Onbekend")
    return "Onbekend"

# Companies ophalen
companies = Table(AIRTABLE_TOKEN, BASE_ID, "Companies").all()
company_names = [c["fields"]["Name"] for c in companies]

# Huidige gelinkte company (optioneel)
company_id = q["fields"].get("Company", [None])[0]
selected_company_name = get_name_by_id(companies, company_id, name_field="Name") if company_id else ""

selected_company = st.selectbox(
    "Selecteer bedrijf",
    [""] + company_names,
    index=([""] + company_names).index(selected_company_name) if selected_company_name in company_names else 0
)

# Robots ophalen (naamveld = "Robotic System")
robots = Table(AIRTABLE_TOKEN, BASE_ID, "Robots").all()
robot_names = [r["fields"].get("Robotic System", "Onbekend") for r in robots]

# Huidige gelinkte robot
robot_id = q["fields"].get("Robot", [None])[0]
selected_robot_name = get_name_by_id(robots, robot_id, name_field="Robotic System") if robot_id else ""

selected_robot = st.selectbox(
    "Selecteer robot",
    [""] + robot_names,
    index=([""] + robot_names).index(selected_robot_name) if selected_robot_name in robot_names else 0
)

# Dynamische Robotic System dropdown op basis van unieke waarden uit robot_names
robotic_system_options = sorted(list(set(robot_names)))
current_value = q["fields"].get("Robotic System", "")
robotic_system = st.selectbox(
    "Robotic System",
    [""] + robotic_system_options,
    index=([""] + robotic_system_options).index(current_value) if current_value in robotic_system_options else 0
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

        # Company koppelen
        if selected_company:
            matching = [c for c in companies if c["fields"]["Name"] == selected_company]
            if matching:
                update_fields["Company"] = [matching[0]["id"]]

        # Robot koppelen op basis van 'Robotic System'
        if selected_robot:
            matching = [r for r in robots if r["fields"].get("Robotic System") == selected_robot]
            if matching:
                update_fields["Robot"] = [matching[0]["id"]]

        # Update uitvoeren in Airtable
        table.update(q_id, update_fields)
        st.success("Opgeslagen!")
        st.session_state.q_index = index + 1
        st.experimental_rerun()
