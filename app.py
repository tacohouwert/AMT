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

# Company- en robotnamen mappen
company_names = [c["fields"]["Name"] for c in companies]
robot_names = [r["fields"].get("Robotic System", "Onbekend") for r in robots]
robotic_system_options = sorted(list(set(robot_names)))  # dynamisch uit robot-tabel

# Tabs
tab1, tab2 = st.tabs(["🧩 Individueel", "🗂️ Per bedrijf"])

# === TAB 1: INDIVIDUEEL FORMULIER ===
with tab1:
    unanswered = [q for q in all_questions if not q["fields"].get("Answers")]
    if not unanswered:
        st.success("Alle vragen zijn al beantwoord ✅")
    else:
        q_index = st.session_state.get("q_index", 0)
        if q_index >= len(unanswered):
            st.success("Je hebt alle vragen behandeld.")
            st.stop()

        q = unanswered[q_index]
        q_id = q["id"]
        q_text = q["fields"].get("Question", "Geen vraagtekst")

        st.header("Beantwoord de volgende vraag:")
        st.write(f"**{q_text}**")

        answer = st.text_area("Antwoord", key="answer")

        # Company
        company_id = q["fields"].get("Company", [None])[0]
        selected_company_name = get_name_by_id(companies, company_id) if company_id else ""
        selected_company = st.selectbox(
            "Selecteer bedrijf",
            [""] + company_names,
            index=([""] + company_names).index(selected_company_name) if selected_company_name in company_names else 0
        )

        # Robot
        robot_id = q["fields"].get("Robot", [None])[0]
        selected_robot_name = get_name_by_id(robots, robot_id, name_field="Robotic System") if robot_id else ""
        selected_robot = st.selectbox(
            "Selecteer robot",
            [""] + robot_names,
            index=([""] + robot_names).index(selected_robot_name) if selected_robot_name in robot_names else 0
        )

        # Robotic System
        current_system = q["fields"].get("Robotic System", "")
        robotic_system = st.selectbox(
            "Robotic System",
            [""] + robotic_system_options,
            index=([""] + robotic_system_options).index(current_system) if current_system in robotic_system_options else 0
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Skip"):
                st.session_state.q_index = q_index + 1
                st.rerun()
        with col2:
            if st.button("Opslaan"):
                update = {
                    "Answers": answer,
                    "Robotic System": robotic_system
                }
                if selected_company:
                    match = [c for c in companies if c["fields"]["Name"] == selected_company]
                    if match:
                        update["Company"] = [match[0]["id"]]
                if selected_robot:
                    match = [r for r in robots if r["fields"].get("Robotic System") == selected_robot]
                    if match:
                        update["Robot"] = [match[0]["id"]]

                questions_table.update(q_id, update)
                st.success("Opgeslagen!")
                st.session_state.q_index = q_index + 1
                st.rerun()

# === TAB 2: OVERZICHT PER BEDRIJF ===
with tab2:
    st.header("Antwoorden per bedrijf invullen")

    # Verzamel unieke company ID's uit vragen
    company_ids_in_questions = set()
    for q in all_questions:
        if "Company" in q["fields"]:
            company_ids_in_questions.update(q["fields"]["Company"])

    # Filter bedrijven met gekoppelde vragen
    companies_with_questions = [c for c in companies if c["id"] in company_ids_in_questions]
    company_names_with_questions = [c["fields"]["Name"] for c in companies_with_questions]

    if not company_names_with_questions:
        st.info("Er zijn geen bedrijven met gekoppelde vragen.")
    else:
        selected_company_overview = st.selectbox("Kies een bedrijf", company_names_with_questions, key="company_overview")
        selected_company_id = next(
            (c["id"] for c in companies_with_questions if c["fields"]["Name"] == selected_company_overview), None
        )

        # ➕ Nieuwe vraag toevoegen (eerste zodat st.rerun() werkt)
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
                    st.rerun()  # herlaadt alles incl. overzicht

        st.markdown("---")
        st.subheader(f"📝 {selected_company_overview}: bestaande vragen en antwoorden")

        # Toon vragen voor geselecteerd bedrijf
        updated_questions = questions_table.all()  # opnieuw ophalen na toevoeging
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
