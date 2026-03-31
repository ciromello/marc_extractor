import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from collections import Counter
import pandas as pd

st.set_page_config(page_title="MARC Field/Subfield CSV Counts", layout="centered")
st.title("📚 MARC Field/Subfield Value Counts")

# --- Upload MARC file ---
uploaded_file = st.file_uploader("Upload MARC file (.mrc, .iso, .xml)", type=["mrc", "iso", "xml"])

if uploaded_file:
    try:
        # --- Read MARC records ---
        file_ext = uploaded_file.name.split(".")[-1].lower()
        records = []

        if file_ext in ["mrc", "iso"]:
            reader = MARCReader(uploaded_file.read())
            for record in reader:
                if record is not None:
                    records.append(record)
        elif file_ext == "xml":
            uploaded_file.seek(0)
            records = parse_xml_to_array(uploaded_file)

        st.success(f"Successfully read {len(records)} valid records!")

        if not records:
            st.warning("No valid MARC records found.")
        else:
            # --- Build field-subfield options ---
            field_options = set()
            for record in records:
                for field in record.get_fields():
                    if field.is_control_field():
                        field_options.add(field.tag)
                    else:
                        sf_list = field.subfields
                        for i in range(0, len(sf_list)-1, 2):
                            code = sf_list[i]
                            if isinstance(code, str):
                                field_options.add(f"{field.tag}${code}")

            field_options = sorted(list(field_options))

            st.subheader("Select field-subfield(s) to count values")
            selected_fields = st.multiselect(
                "Choose field-subfield (e.g., 245$a, 100$a, 990$a)",
                options=field_options
            )

            if selected_fields:
                st.subheader("Preview of value counts")
                all_rows = []

                for sel in selected_fields:
                    if "$" in sel:
                        tag, code = sel.split("$")
                    else:
                        tag, code = sel, None

                    values = []
                    for record in records:
                        for field in record.get_fields(tag):
                            if field is None:
                                continue
                            if code:  # data field
                                sf_list = field.subfields
                                for i in range(0, len(sf_list)-1, 2):
                                    sf_code = sf_list[i].lower()
                                    sf_value = sf_list[i+1].strip()
                                    if sf_code == code.lower():
                                        values.append(sf_value)
                            else:  # control field
                                values.append(field.value().strip())

                    counter = Counter(values)
                    for val, cnt in counter.items():
                        all_rows.append({
                            "Field-Subfield": sel,
                            "Value": val,
                            "Count": cnt
                        })

                df = pd.DataFrame(all_rows)
                st.dataframe(df.head(20))  # preview top 20 rows

                # --- Download CSV ---
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Counts as CSV",
                    data=csv_bytes,
                    file_name="marc_field_counts.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"An error occurred: {e}")
