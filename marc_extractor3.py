import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from io import BytesIO
import pandas as pd
from collections import Counter

st.set_page_config(page_title="MARC Custom CSV with Counts", layout="centered")
st.title("📚 MARC Custom CSV Exporter with Counts")

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
                records.append(record)
        elif file_ext == "xml":
            uploaded_file.seek(0)
            records = parse_xml_to_array(uploaded_file)

        st.success(f"Successfully read {len(records)} records!")

        # --- Collect all available fields/subfields ---
        field_options = set()
        for record in records:
            for field in record.get_fields():
                if field.is_control_field():
                    field_options.add(field.tag)
                else:
                    for code in field:
                        field_options.add(f"{field.tag}${code}")

        field_options = sorted(list(field_options))
        st.subheader("Select fields/subfields for CSV with counts")
        selected_fields = st.multiselect(
            "Choose the fields/subfields to include",
            options=field_options,
            default=field_options[:5]
        )

        if selected_fields:
            st.subheader("Counts Preview")
            count_tables = {}

            # Compute counts
            for sel in selected_fields:
                values = []
                for record in records:
                    if "$" in sel:
                        tag, code = sel.split("$")
                        for field in record.get_fields(tag):
                            if code in field:
                                values.append(field[code])
                    else:
                        for field in record.get_fields(sel):
                            values.append(field.value())
                counter = Counter(values)
                if counter:
                    df_count = pd.DataFrame(counter.items(), columns=[sel, "Count"]).sort_values("Count", ascending=False)
                    count_tables[sel] = df_count
                    st.write(f"**Field: {sel}**")
                    st.dataframe(df_count.head(10))  # show top 10 in preview

            # Prepare CSV for download
            csv_buffer = BytesIO()
            with pd.ExcelWriter(csv_buffer, engine="xlsxwriter") as writer:
                for field, df_count in count_tables.items():
                    # Replace $ with _ for sheet names
                    sheet_name = field.replace("$", "_")
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
