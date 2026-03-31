import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="Custom MARC CSV Exporter", layout="centered")
st.title("📚 Custom MARC CSV Exporter with Counts")

# Upload MARC file
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
            st.warning("No valid MARC records found in the file.")
        else:
            # --- Collect all available fields/subfields ---
            field_options = set()
            for record in records:
                for field in record.get_fields():
                    if field is None:
                        continue
                    if field.is_control_field():
                        field_options.add(field.tag)
                    else:
                        for code in field:
                            field_options.add(f"{field.tag}${code}")

            field_options = sorted(list(field_options))
            st.subheader("Select fields/subfields for CSV export")
            selected_fields = st.multiselect(
                "Choose the fields/subfields to include",
                options=field_options,
                default=field_options[:5]
            )

            if selected_fields:
                st.subheader("Preview top values for selected fields")
                csv_data = []
                for record in records:
                    row = {}
                    for sel in selected_fields:
                        if "$" in sel:
                            tag, code = sel.split("$")
                            values = [f[code] for f in record.get_fields(tag) if f is not None and code in f]
                            row[sel] = "; ".join(values)
                        else:
                            values = [f.value() for f in record.get_fields(sel) if f is not None]
                            row[sel] = "; ".join(values)
                    csv_data.append(row)

                df = pd.DataFrame(csv_data)
                st.dataframe(df.head(10))  # preview first 10 rows

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Selected Fields as CSV",
                    data=csv_bytes,
                    file_name="marc_selected_fields.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"An error occurred: {e}")
