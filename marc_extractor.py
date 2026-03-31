import os
import csv
from pymarc import MARCReader
import xml.etree.ElementTree as ET


def extract_from_marc_binary(file_path, field_tag, subfield_code):
    results = []

    with open(file_path, 'rb') as fh:
        reader = MARCReader(fh, to_unicode=True, force_utf8=True)

        for record in reader:
            record_id = record['001'].value() if record['001'] else "NO_ID"

            fields = record.get_fields(field_tag)
            for field in fields:
                if field.is_control_field():
                    continue
                values = field.get_subfields(subfield_code)
                for v in values:
                    results.append((record_id, v))

    return results


def extract_from_marcxml(file_path, field_tag, subfield_code):
    results = []

    ns = {'marc': 'http://www.loc.gov/MARC21/slim'}
    tree = ET.parse(file_path)
    root = tree.getroot()

    for record in root.findall('marc:record', ns):
        record_id = "NO_ID"
        cf = record.find('marc:controlfield[@tag="001"]', ns)
        if cf is not None:
            record_id = cf.text

        for datafield in record.findall('marc:datafield', ns):
            if datafield.attrib.get('tag') == field_tag:
                for subfield in datafield.findall('marc:subfield', ns):
                    if subfield.attrib.get('code') == subfield_code:
                        results.append((record_id, subfield.text))

    return results


def save_to_csv(results, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Record_ID", "Value"])
        writer.writerows(results)


def main():
    print("=== MARC Field Extractor ===")

    file_path = input("Enter file path: ").strip()
    field_tag = input("Enter field tag (e.g., 995): ").strip()
    subfield_code = input("Enter subfield code (e.g., b): ").strip()

    if not os.path.exists(file_path):
        print("❌ File not found.")
        return

    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.mrc', '.iso', '.txt']:
        print("📂 Processing as binary MARC...")
        results = extract_from_marc_binary(file_path, field_tag, subfield_code)

    elif ext == '.xml':
        print("📂 Processing as MARCXML...")
        results = extract_from_marcxml(file_path, field_tag, subfield_code)

    else:
        print("❌ Unsupported file type.")
        return

    print("\n=== RESULTS ===")
    for record_id, value in results:
        print(f"{record_id} -> {value}")

    print(f"\n✅ Total values found: {len(results)}")

    save = input("\nSave results to CSV? (y/n): ").lower()
    if save == 'y':
        output_file = "output.csv"
        save_to_csv(results, output_file)
        print(f"💾 Saved to {output_file}")


if __name__ == "__main__":
    main()
