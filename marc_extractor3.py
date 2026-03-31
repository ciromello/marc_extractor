import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from collections import Counter
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="MARC Field-Subfield Counts", layout="centered")
st.title("📚 MARC Field/Subfield Frequency Counter")

# --- Upload MARC file ---
uploaded_file = st.file_uploader("Upload MARC file (.mrc, .iso, .xml)", type=["mrc", "iso", "xml"])

if uploaded_file:
    try:
        # --- Read records ---
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
            # --- Collect available field-subfield combinations ---
            field_options = set()
            for record in records:
                for field in record.get_fields():
                    if field.is_control_field():
                        field_options.add(field.tag)
                    else:
                        for code in field:
                            field_options.add(f"{field.tag}${code}")

            field_options = sorted(list(field_options))
            st.subheader("Select field-subfield(s) to count values")
            selected_fields = st.multiselect(
                "Choose field-subfield (e.g., 245$a, 100$a, 650$a)",
                options=field_options
            )

            if selected_fields:
                st.subheader("Value Counts Preview")
                all_counts = {}

                for sel in selected_fields:
                    tag, code = sel.split("$")
                    values = []
                    for record in records:
                        for field in record.get_fields(tag):
                            if code in field:
                                values.append(field[code])
                    counter = Counter(values)
                    df_count = pd.DataFrame(counter.items(), columns=["Value", "Count"]).sort_values("Count", ascending=False)
                    all_counts[sel] = df_count
                    st.write(f"**Field-Subfield: {sel}**")
                    st.dataframe(df_count.head(10))  # top 10 preview

                # --- Prepare CSV download (multi-sheet Excel) ---
                csv_buffer = BytesIO()
                with pd.ExcelWriter(csv_buffer, engine="xlsxwriter") as writer:
                    for field_sub, df_count in all_counts.items():
                        sheet_name = field_sub.replace("$", "_")
                        df_count.to_excel(writer, sheet_name=sheet_name, index=False)
                    writer.save()

                st.download_button(
                    label="Download Counts as Excel",
                    data=csv_buffer.getvalue(),
                    file_name="marc_field_counts.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"An error occurred: {e}")
