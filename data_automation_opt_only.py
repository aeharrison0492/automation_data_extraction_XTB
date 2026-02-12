import os
import re
import pandas as pd
import unicodedata

def read_log_text(filepath):
    """Read .xtb.log text, handling UTF-8 and UTF-16 encodings automatically."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        # UTF-16 files decoded as UTF-8 contain lots of null bytes
        if "\x00" in text:
            raise UnicodeError
    except UnicodeError:
        with open(filepath, "r", encoding="utf-16", errors="ignore") as f:
            text = f.read()
        print(f"UTF-16 encoding detected: {filepath}")
    return text


# Input the root folder
base_root = input("Enter the root folder before the extraction folder: ").strip()
input_folder = input("Enter the extraction folder name: ").strip()
root_folder = os.path.join(base_root, input_folder)

# Check that the folder has been typed correctly
if not os.path.isdir(root_folder):
    print(f"Folder not found: {input_folder}")
    exit(1)

print(f"Searching in {root_folder}\n")

# Regex patterns
patterns = {
    "Total Energy (Eh)": r"TOTAL\s+ENERGY\s+(-?\d+\.\d+)\s*Eh",
    "Gradient Norm (Eh/α)": r"GRADIENT\s+NORM\s+(\d+\.\d+)\s*Eh/α",
    "HOMO-LUMO Gap (eV)": r"HOMO-LUMO\s+GAP\s+(\d+\.\d+)\s*eV",
}

data = []

# Recursively find all valid log files
all_files = []
for dirpath, dirnames, filenames in os.walk(root_folder):
    for filename in filenames:
        if (
            filename.endswith(".xtb.log")
            and ".err.log" not in filename
            and filename != "xtbopt.log"):
            all_files.append(os.path.join(dirpath, filename))

total_files = len(all_files)
print(f"Found {total_files} valid .log files to process.\n")
for f in filenames:
    if f.endswith(".xtb.log") and ".err.log" not in f:
        print("Found log:", os.path.join(dirpath, f))

# Process each file with progress display
for idx, filepath in enumerate(all_files, start=1):
    filename = os.path.basename(filepath)
    rel_path = os.path.relpath(filepath, root_folder)

    # Display progress
    print(f"[{idx}/{total_files}] Processing: {rel_path}")

    try:
       text = read_log_text(filepath)
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
        continue
# !!!!! This section is focused on how I used this for my own research. How your folders are laid out may be different !!!!!
# !!!!! My folders were laid out in the form: Macrocycle/Up_or_down_orientation/DNA_Tetramer/xTB_optimisation_results/ !!!!!
    # Extract folder info - change for 
    parts = rel_path.split(os.sep)
    top_folder = parts[0] if len(parts) > 0 else None
    tetramer = parts[1] if len(parts) > 1 else None
    subfolder = parts[-2] if len(parts) > 1 else None

    # Extract data
    extracted = {
        "File": filename,
        "Relative Path": rel_path,
        "Top Folder": top_folder,
        "Tetramer": tetramer,
        "Optimization Folder": subfolder,
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        extracted[key] = float(match.group(1)) if match else None

    data.append(extracted)

# Save results
df = pd.DataFrame(data)

cols = [
    "Top Folder",
    "Tetramer",
    "Optimization Folder",
    "File",
    "Relative Path",
    "Total Energy (Eh)",
    "Gradient Norm (Eh/α)",
    "HOMO-LUMO Gap (eV)",
]

# Reorder safely only using existing columns
existing_cols = [c for c in cols if c in df.columns]
df = df[existing_cols]

if df.empty:
    print("\n No data extracted. Check that your .log files contain the expected energy block format.")
else:
    output_path = os.path.join(base_root, f"xtb_summary_{input_folder}.csv")
    df.to_csv(output_path, index=False)
    print("\n Extraction complete!")
    print(f"Results saved to: {output_path}")
    print(f"Total files processed: {len(df)}")
