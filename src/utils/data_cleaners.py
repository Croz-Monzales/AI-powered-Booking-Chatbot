import pandas as pd
import re

def clean_hotel_data(df):
    # 1. Strip whitespace from column headers
    df.columns = df.columns.str.strip()

    # 2. Convert 'Marks' to float (e.g., 8.2)
    df['Marks'] = pd.to_numeric(df['Marks'], errors='coerce')

    # 3. Clean 'Reviews' -> Extract number only (7,620 reviews -> 7620)
    # We remove commas and then extract digits
    df['Reviews'] = df['Reviews'].str.replace(',', '').str.extract('(\d+)').astype(float)

    # 4. Clean 'Price' -> Extract numeric value (Price 574 zł -> 574)
    df['Price'] = df['Price'].str.extract('(\d+)').astype(float)

    # 5. Clean 'Distances' -> Extract float (0.6 km from center -> 0.6)
    df['Distances'] = df['Distances'].str.extract('(\d+\.?\d*)').astype(float)

    # 6. Clean 'Guests reviews:' -> Extract score (Location 9.4 -> 9.4)
    df['Guests reviews:'] = df['Guests reviews:'].str.extract('(\d+\.?\d*)').astype(float)

    # 7. Fill empty strings or NaN with None (for SQL NULL compatibility)
    df = df.where(pd.notnull(df), None)
    
    return df