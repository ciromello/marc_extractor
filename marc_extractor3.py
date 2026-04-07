import streamlit as st
from pymarc import MARCReader, parse_xml_to_array
from collections import Counter
import pandas as pd
import re

st.set_page_config(page_title="MARC Field/Subfield CSV Counts", layout="centered")
st.title("📚 MARC Field/Subfield Value Counts (All Formats)")

uploaded_file = st.file_uploader(
    "Upload MARC file (.mrc, .iso, .xml, .mrk)",
    type=["mrc", "iso", "xml", "mrk", "txt"]
)

if uploaded_file:
    try:
        content = uploaded_file.read()
        text_sample = content[:1000].decode(errors="ignore")

        selected_fields_input = st.text_area(
            "Enter field-subfield(s), one per line (e.g., 990$a)"
        )

        if selected_fields_input:
            selected_fields = [
                line.strip() for line in selected_fields_input.splitlines() if line.strip()
            ]

            counters = {sel: Counter() for sel in selected_fields}

            # --------------------------------------------------
            # 🟢 CASE 1: TEXT MARC (MRK format)  ← YOUR FILE
            # --------------------------------------------------
            if text_sample.startswith("="):
                st.info("Detected MRK (text MARC) format")

                lines = content.decode("utf-8", errors="ignore").splitlines()

                for line in lines:
                    if not line.startswith("="):
                        continue

                    tag = line[1:4]

                    for sel in selected_fields:
                        if "$" in sel:
                            sel_tag, code = sel.split("$")
                        else:
                            sel_tag, code = sel, None

                        if tag != sel_tag:
                            continue

                        if code:
                            pattern = rf"\${code}([^\$]+)"
                            matches = re.findall(pattern, line)

                            for m in matches:
                                counters[sel][m.strip()] += 1
                        else:
                            value = line[6:].strip()
                            counters[sel][value] += 1

            # --------------------------------------------------
            # 🟡 CASE 2: BINARY MARC
            # --------------------------------------------------
            elif uploaded_file.name.endswith((".mrc", ".iso")):
                st.info("Detected binary MARC format")

                reader = MARCReader(content)

                for record in reader:
                    if record is None:
                        continue

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

            # --------------------------------------------------
            # 🔵 CASE 3: XML
            # --------------------------------------------------
            elif uploaded_file.name.endswith(".xml"):
                st.info("Detected MARCXML format")

                records = parse_xml_to_array(uploaded_file)

                for record in records:
                    if record is None:
                        continue

                    for sel in selected_fields:
                        if "$" in sel:
                            tag, code = sel.split("$")
                        else:
                            tag, code = sel, None

                        for field in record.get_fields(tag):
                            sf_list = getattr(field, 'subfields', [])

                            for i in range(0, len(sf_list) - 1, 2):
                                sf_code = str(sf_list[i]).lower()
                                sf_value = str(sf_list[i + 1]).strip()

                                if code and sf_code == code.lower():
                                    counters[sel][sf_value] += 1

            # --------------------------------------------------
            # RESULTS
            # --------------------------------------------------
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

                st.subheader("Preview")
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
