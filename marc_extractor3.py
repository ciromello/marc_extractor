import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from collections import Counter
import pandas as pd
import re

st.set_page_config(page_title="MARC Field/Subfield CSV Counts", layout="centered")
st.title("📚 MARC Field/Subfield Value Counts (Large Files Optimized)")

uploaded_file = st.file_uploader(
    "Upload MARC file (.mrc, .iso, .xml)",
    type=["mrc", "iso", "xml"]
)

if uploaded_file:
    try:
        file_ext = uploaded_file.name.split(".")[-1].lower()

        st.info("Processing file in streaming mode...")

        selected_fields_input = st.text_area(
            "Enter field-subfield(s), one per line (e.g., 990$a)"
        )

        if selected_fields_input:
            selected_fields = [
                line.strip() for line in selected_fields_input.splitlines() if line.strip()
            ]

            counters = {sel: Counter() for sel in selected_fields}
            total_records = 0
            skipped_records = 0

            # --- PROCESS MRC / ISO ---
            if file_ext in ["mrc", "iso"]:
                uploaded_file.seek(0)
                reader = MARCReader(uploaded_file.read())

                for record in reader:
                    if record is None:
                        skipped_records += 1
                        continue

                    total_records += 1

                    for sel in selected_fields:
                        if "$" in sel:
                            tag, code = sel.split("$")
                        else:
                            tag, code = sel, None

                        for field in record.get_fields(tag):

                            # ✅ NOW field is defined correctly
                            sf_list = getattr(field, 'subfields', [])

                            if sf_list:
                                # normal case
                                for i in range(0, len(sf_list) - 1, 2):
                                    sf_code = str(sf_list[i]).lower()
                                    sf_value = str(sf_list[i + 1]).strip()

                                    if code and sf_code == code.lower():
                                        counters[sel][sf_value] += 1
                            else:
                                # 🔥 fallback for broken pymarc parsing
                                raw = field.format_field()

                                if code:
                                    pattern = rf"\${code}([^\$]+)"
                                    matches = re.findall(pattern, raw)

                                    for m in matches:
                                        counters[sel][m.strip()] += 1
                                else:
                                    counters[sel][raw.strip()] += 1

            # --- PROCESS XML ---
            elif file_ext == "xml":
                uploaded_file.seek(0)
                records = parse_xml_to_array(uploaded_file)

                for record in records:
                    if record is None:
                        skipped_records += 1
                        continue

                    total_records += 1

                    for sel in selected_fields:
                        if "$" in sel:
                            tag, code = sel.split("$")
                        else:
                            tag, code = sel, None

                        for field in record.get_fields(tag):

                            sf_list = getattr(field, 'subfields', [])

                            if sf_list:
                                for i in range(0, len(sf_list) - 1, 2):
                                    sf_code = str(sf_list[i]).lower()
                                    sf_value = str(sf_list[i + 1]).strip()

                                    if code and sf_code == code.lower():
                                        counters[sel][sf_value] += 1
                            else:
                                raw = field.format_field()

                                if code:
                                    pattern = rf"\${code}([^\$]+)"
                                    matches = re.findall(pattern, raw)

                                    for m in matches:
                                        counters[sel][m.strip()] += 1
                                else:
                                    counters[sel][raw.strip()] += 1

            # --- RESULTS ---
            st.success(f"Processed {total_records} records")

            if skipped_records:
                st.warning(f"Skipped {skipped_records} invalid records")

            all_rows = []
            for sel, counter in counters.items():
                if not counter:
                    st.warning(f"No values found for {sel}")

                for val, cnt in counter.items():
                    all_rows.append({
                        "Field-Subfield": sel,
                        "Value": val,
                        "Count": cnt
                    })

            if all_rows:
                df = pd.DataFrame(all_rows)

                st.subheader("Preview (top 20 rows)")
                st.dataframe(df.head(20))

                csv_bytes = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download CSV",
                    data=csv_bytes,
                    file_name="marc_counts.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No values found.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
