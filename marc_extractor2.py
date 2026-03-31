import os
from pymarc import MARCReader, record_to_xml

def extract_marc_records(file_path):
    """
    Reads a MARC file and returns a list of records.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No such file: {file_path}")

    records = []
    with open(file_path, 'rb') as fh:
        reader = MARCReader(fh)
        for record in reader:
            records.append(record)
    return records

def save_records_as_xml(records, output_file):
    """
    Saves MARC records as an XML file.
    """
    with open(output_file, 'w', encoding='utf-8') as fh:
        for record in records:
            fh.write(record_to_xml(record))

def main():
    print("Welcome to MARC Extractor (Python 3.12 compatible)!")
    
    # Prompt user for MARC file path
    file_path = input("Please enter the path to your MARC file: ").strip()
    
    try:
        records = extract_marc_records(file_path)
        print(f"Successfully read {len(records)} records.")
        
        output_file = input("Enter the filename to save XML output (e.g., output.xml): ").strip()
        save_records_as_xml(records, output_file)
        print(f"Records saved to {output_file}")
    
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
