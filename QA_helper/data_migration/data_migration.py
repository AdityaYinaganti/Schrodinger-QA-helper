import pandas as pd
import sys

def flatten_source(input_file, output_file, sheet_name):
    # 1. Load file based on type
    if input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file, sheet_name=sheet_name, skiprows=4)
    else:
        # CSVs don't have sheet names, so we ignore the argument
        df = pd.read_csv(input_file, skiprows=4)

    # 2. Standardize columns (Feature, SubFeature, TestCase)
    df = df.iloc[:, :3] 
    df.columns = ['Feature', 'SubFeature', 'TestCase']

    # 3. Fill merged cells
    df['Feature'] = df['Feature'].ffill()
    df['SubFeature'] = df['SubFeature'].ffill()
    
    # 4. Filter junk (PASS, FAIL, NOT TESTED, etc.)
    junk_patterns = [
        'LD 2026-1', 'BLANK', 'Total Cases', 'testers', 'color keys',
        'PASS', 'FAIL', 'NOT TESTED', 'MS Edge', 'Firefox', 'Chrome'
    ]
    pattern = '|'.join(junk_patterns)
    
    df = df[~df['Feature'].str.contains(pattern, case=False, na=False)]
    df = df[~df['TestCase'].str.contains(pattern, case=False, na=False)]
    
    # 5. Final cleanup
    df = df.dropna(subset=['TestCase'])
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    df.to_csv(output_file, index=False)
    print(f"Created {output_file} from sheet '{sheet_name}'")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python 1_flatten_data.py <input_file> <output_file.csv> <sheet_name>")
    else:
        flatten_source(sys.argv[1], sys.argv[2], sys.argv[3])
