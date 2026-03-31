import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from collections import Counter
import pandas as pd

st.set_page_config(page_title="MARC Field/Subfield CSV Counts", layout="centered")
st.title("📚 MARC Field/Subfield Value Counts")

uploaded_file = st.file_uploader(
    "Upload MARC file (.mrc, .iso, .xml)", type=["mrc", "iso", "xml"]
)

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
            # --- Build all field-subfield options ---
            field_options = set()
            field_subfields_map = dict()  # field -> list of subfields detected
            for record in records:
                for field in record.get_fields():
                    if field.is_control_field():
                        field_options.add(field.tag)
                        field_subfields_map.setdefault(field.tag, [])
                    else:
                        sf_list = getattr(field, 'subfields', [])
                        codes_in_field = set()
                        for i in range(0, len(sf_list)-1, 2):
                            code = str(sf_list[i])
                            codes_in_field.add(code)
                            field_options.add(f"{field.tag}${code}")
                        field_subfields_map.setdefault(field.tag, set()).update(codes_in_field)

            field_options = sorted(list(field_options))

            st.subheader("Select field-subfield(s) to count values")
            st.info(
                "Select from the list or type a field-subfield manually (e.g., 990$a)."
            )

            selected_fields = st.multiselect(
                "Choose field-subfield",
                options=field_options,
                default=[]
            )

            # Optional manual input
            manual_field = st.text_input("Or type a field-subfield manually (e.g., 990$a)")
            if manual_field:
                selected_fields.append(manual_field.strip())

            # --- Preview subfield codes in the file ---
            for field_tag in set(f.split("$")[0] for f in selected_fields if "$" in f):
                detected_codes = sorted(list(field_subfields_map.get(field_tag, [])))
                st.text(f"Detected subfields for {field_tag}: {', '.join(detected_codes) if detected_codes else 'None'}")

            # --- Count values ---
            if selected_fields:
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
                                sf_list = getattr(field, 'subfields', [])
                                for i in range(0, len(sf_list)-1, 2):
                                    sf_code = str(sf_list[i]).lower()
                                    sf_value = str(sf_list[i+1]).strip()
                                    if sf_code == code.lower():
                                        values.append(sf_value)
                            else:  # control field
                                values.append(field.value().strip())

                    if not values:
                        st.warning(f"No values found for {sel}. Please check the subfield code.")
                    counter = Counter(values)
                    for val, cnt in counter.items():
                        all_rows.append({
                            "Field-Subfield": sel,
                            "Value": val,
                            "Count": cnt
                        })

                if all_rows:
                    df = pd.DataFrame(all_rows)
                    st.subheader("Preview of value counts (top 20 rows)")
                    st.dataframe(df.head(20))

                    csv_bytes = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Counts as CSV",
                        data=csv_bytes,
                        file_name="marc_field_counts.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No values found for the selected field-subfields.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
