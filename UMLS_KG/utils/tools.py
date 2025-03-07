import os
import pandas as pd
import math

def split_csv(filepath, num_parts):

    df = pd.read_csv(filepath)

    total_rows = len(df)
    rows_per_part = math.ceil(total_rows / num_parts)
    
    dir_path, filename = os.path.split(filepath)
    file_name, ext = os.path.splitext(filename)
    
    # Split the dataframe and save the parts
    for i in range(num_parts):
        start_row = i * rows_per_part
        end_row = min((i + 1) * rows_per_part, total_rows)
        
        part_df = df.iloc[start_row:end_row]

        part_filename = f"{file_name}_part_{i + 1}{ext}"
        part_filepath = os.path.join(dir_path, part_filename)

        part_df.to_csv(part_filepath, index=False)
        
    print(f"CSV file has been split into {num_parts} parts.")