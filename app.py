import streamlit as st
import logging
from pyairtable import Table

# Setup logging
logging.basicConfig(level=logging.INFO)

# Secrets ophalen
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]
QUESTIONS_TABLE = "Questions"

# Connectie met Airtable-tabellen
questions_table = Table(AIRTABLE_TOKEN, BASE_ID, QUESTIONS_TABLE)
companies_table = Table(AIRTABLE_TOKEN, BASE_ID, "Companies")
robots_table = Table(AIRTABLE_TOKEN, BASE_ID, "Robots")

# Alle data ophalen
try:
    all_questions = questions_table.all()
    companies = companies_table.all()
    robots = robots_table.all()
except Exception as e:
    st.error(f"Fout bij ophalen van data: {e}")
    st.stop()

# Helper om naam op te halen
def get_name_by_id(records, record_id, name_field="Name"):
    for r in records:
        if r["id"] == record_id:
            return r["fields"].get(name_field, "Onbekend")
    return "Onbekend"

# Company-namen en robotic systems uit robots
company_ids_in_questions = set()
for q in all_questions:
    if "Company" in q["fields"]:
        company_ids_in_questions.update(q["fields"]["Company"])

companies_with_questions = [c for c in companies if c["id"] in company_ids_in_questions]
company_names_with_questions = [c["fields"]["Name"] for c in companies_with_questions]

robot_names = [r["fields"].get("Robotic System", "Onbekend") for r in robots]
robotic_system_options = sorted(list(set(robot_names)))

# === PER BEDRIJF SCHERM ===
st.title("🗂️ Vragen beantwoorden per bedrijf")

if not company_names_with_questions:
    st.info("Er zijn nog geen bedrijven met gekoppelde vragen.")
else:
    selected_company_overview = st.selectbox("Kies een bedrijf", company_names_with_questions, key="company_overview")
    selected_company_id = next(
        (c["id"] for c in companies_with_questions if c["fields"]["Name"] == selected_company_overview), None
    )

    # ➕ Nieuwe vraag toevoegen
    st.markdown("### ➕ Voeg een nieuwe vraag toe")

    with st.form("nieuwe_vraag_formulier", clear_on_submit=True):
        nieuwe_vraag = st.text_area("Vraagtekst", key="nieuwe_vraag_input")
        nieuw_antwoord = st.text_area("Antwoord", key="nieuwe_antwoord_input")
        nieuw_robotic_system = st.selectbox("Optioneel: Robotic System koppelen", [""] + robotic_system_options, key="nieuw_robotic_select")

        toevoegen = st.form_submit_button("✅ Vraag en antwoord toevoegen")
        if toevoegen:
            if not nieuwe_vraag.strip():
                st.warning("Voer een vraagtekst in.")
            else:
                new_fields = {
                    "Question": nieuwe_vraag.strip(),
                    "Answers": nieuw_antwoord.strip(),
                    "Company": [selected_company_id]
                }
                if nieuw_robotic_system:
                    new_fields["Robotic System"] = nieuw_robotic_system

                questions_table.create(new_fields)
                st.success("Nieuwe vraag toegevoegd ✅")
                st.rerun()

    st.markdown("---")
    st.subheader(f"📝 {selected_company_overview}: bestaande vragen en antwoorden")

    # Vragen opnieuw ophalen na evt. toevoeging
    updated_questions = questions_table.all()
    related_questions = [
        q for q in updated_questions
        if "Company" in q["fields"] and selected_company_id in q["fields"]["Company"]
    ]

    with st.form("bulk_form"):
        antwoorden = {}
        for q in related_questions:
            q_id = q["id"]
            vraag = q["fields"].get("Question", "Geen vraagtekst")
            bestaand = q["fields"].get("Answers", "")
            antwoorden[q_id] = st.text_area(vraag, value=bestaand, key=f"vraag_{q_id}")

        if st.form_submit_button("📩 Alles opslaan"):
            for vraag_id, antwoord in antwoorden.items():
                questions_table.update(vraag_id, {"Answers": antwoord})
            st.success("Antwoorden opgeslagen ✅")
            st.rerun()
