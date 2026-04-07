# --- inside your loop ---
sf_list = getattr(field, 'subfields', [])

if sf_list:
    # normal case
    for i in range(0, len(sf_list) - 1, 2):
        sf_code = str(sf_list[i]).lower()
        sf_value = str(sf_list[i + 1]).strip()

        if code and sf_code == code.lower():
            counters[sel][sf_value] += 1

else:
    # 🔥 NEW: fallback using raw field text
    raw = field.format_field()

    if code:
        import re
        pattern = rf"\${code}([^\$]+)"
        matches = re.findall(pattern, raw)

        for m in matches:
            counters[sel][m.strip()] += 1
    else:
        # no subfield requested → whole value
        counters[sel][raw.strip()] += 1
