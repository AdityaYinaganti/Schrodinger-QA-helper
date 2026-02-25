import pandas as pd
import sys
import os

def flatten_source(input_file, output_file="1_cleaned_test_cases.csv"):
    # 1. Determine if it's Excel or CSV
    if input_file.endswith('.xlsx'):
        # Skip 4 metadata rows; use the "LiveDesign File Import" sheet
        df = pd.read_excel(input_file, sheet_name="LiveDesign File Import", skiprows=4)
    else:
        # For the original CSV, also skip the first 4 metadata rows
        df = pd.read_csv(input_file, skiprows=4)

    # 2. Standardize columns: Keep only Feature, SubFeature, and Test Case
    df = df.iloc[:, :3] 
    df.columns = ['Feature', 'SubFeature', 'TestCase']

    # 3. Handle Merged Cells: Fill Feature and SubFeature names down
    df['Feature'] = df['Feature'].ffill()
    df['SubFeature'] = df['SubFeature'].ffill()

    # 4. Filter out specific junk data
    # Remove rows where Feature or TestCase contain these strings (case-insensitive)
    junk_patterns = ['LD 2026-1', 'BLANK', 'Total Cases']
    pattern = '|'.join(junk_patterns)
    
    # Apply filters
    df = df[~df['Feature'].str.contains(pattern, case=False, na=False)]
    df = df[~df['TestCase'].str.contains(pattern, case=False, na=False)]

    # Remove standard legend/metadata labels
    junk_labels = ['testers', 'color keys', 'pass', 'fail', 'not tested', 'status', 'feature']
    df = df[~df['Feature'].str.lower().isin(junk_labels)]
    
    # 5. Drop any remaining empty Test Cases
    df = df.dropna(subset=['TestCase'])
    
    # 6. Final cleanup of whitespace
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # 7. Save the cleaned file
    df.to_csv(output_file, index=False)
    print(f"✅ Step 1 Complete: Created {output_file}")
    print(f"   (Removed rows matching: {', '.join(junk_patterns)})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 1_flatten_data.py <file.xlsx or file.csv>")
    else:
        flatten_source(sys.argv[1])