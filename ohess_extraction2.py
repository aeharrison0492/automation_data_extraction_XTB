import os
import re
import pandas as pd
from chardet import detect

# Root folder input
root_folder = input("Enter the root path (e.g., AuMacroPr_d): ").strip()

# Regex patterns for all thermo & energy data
patterns = {
    "Total Energy (Eh)": re.compile(r"TOTAL ENERGY\s+(-?\d+\.\d+)\s+Eh"),
    "Total Enthalpy (Eh)": re.compile(r"TOTAL ENTHALPY\s+(-?\d+\.\d+)\s+Eh"),
    "Total Free Energy (Eh)": re.compile(r"TOTAL FREE ENERGY\s+(-?\d+\.\d+)\s+Eh"),
    "Gradient Norm (Eh/α)": re.compile(r"GRADIENT NORM\s+(-?\d+\.\d+)\s+Eh/α"),
    "HOMO-LUMO Gap (eV)": re.compile(r"HOMO-LUMO GAP\s+(-?\d+\.\d+)\s+eV"),
    "Zero Point Energy (Eh)": re.compile(r"zero point energy\s+(-?\d+\.\d+)\s+Eh", re.IGNORECASE),
    "G(RRHO) w/o ZPVE (Eh)": re.compile(r"G\(RRHO\)\s+w/o\s+ZPVE\s+(-?\d+\.\d+)\s+Eh", re.IGNORECASE),
    "G(RRHO) contrib. (Eh)": re.compile(r"G\(RRHO\)\s+contrib\.\s+(-?\d+\.\d+)\s+Eh", re.IGNORECASE),
}

records = []

def read_file_safely(filepath):
    with open(filepath, "rb") as f:
        raw = f.read(100000)
    encoding = detect(raw)["encoding"] or "utf-8"
    with open(filepath, "r", encoding=encoding, errors="ignore") as f:
        return f.read()

# Functions that extract metadata from PATH
def extract_macrocycle(parts):
    return next((p for p in parts if p.startswith("Au")), None)

def extract_tetramer(parts):
    return next((p for p in parts if len(p) == 4 and p.isalpha()), None)

def extract_conformation(parts):
    return next((p for p in parts if p.lower() in ["up", "down"]), None)

def extract_binding(parts):
    return next((p for p in parts if p.lower() in ["bound", "unbound"]), None)

# Walk through folders recursively
for root, _, files in os.walk(root_folder):
    for filename in files:

        # Only process xtbopt.xtb.log
        if not filename.endswith("xtbopt.xtb.log"):
            continue

        filepath = os.path.join(root, filename)
        content = read_file_safely(filepath)

        data = {"File": filename}

        # Extract numeric thermo data
        for key, pattern in patterns.items():
            match = pattern.search(content)
            data[key] = float(match.group(1)) if match else None

        # Extract metadata from full path
        parts = root.split(os.sep)

        data["Macrocycle"] = extract_macrocycle(parts)
        data["Tetramer"] = extract_tetramer(parts)
        data["Conformation"] = extract_conformation(parts)
        data["Binding"] = extract_binding(parts)

        data["Relative Path"] = os.path.relpath(filepath, root_folder)

        records.append(data)

# Combine results into a DataFrame
df = pd.DataFrame(records)

print(f"\nExtracted data from {len(df)} files.")
print(df.head())

# Save output
give_filename = input("Enter the name you want to save the file as: ")
out_file = os.path.join(root_folder, f"{give_filename}.csv")
df.to_csv(out_file, index=False)
print(f"\nSaved results to: {out_file}")
