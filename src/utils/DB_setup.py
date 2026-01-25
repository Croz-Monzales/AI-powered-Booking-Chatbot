import os
os.chdir(".")
print(f"📂 Execution path set to: {os.getcwd()}")

import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
import yaml
from box import ConfigBox
from pathlib import Path
from .all_readers import read_yaml
from time import time
from .data_cleaners import clean_hotel_data
import numpy as np
import math

def get_db_connection(db_configs):
    """Establishes connection to MySQL"""
    try:
        conn = mysql.connector.connect(**db_configs)
        print("CONNECTION SUCCESSFUL !")
        return conn
    except Error as e:
        print(f"❌ Connection Failed: {e}")
        return None

# ==========================================
# 1. FLIGHTS IMPORTER
# ==========================================
def import_flights(csv_file_path,db_configs):
    print(f"\n✈️  Processing Flights from: {csv_file_path}")
    
    # Load CSV
    # ensure columns match your CSV headers exactly
    df = pd.read_csv(csv_file_path)
    df['FLT_DATE'] = pd.to_datetime(df['FLT_DATE']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection(db_configs)
    if not conn: return
    cursor = conn.cursor()

    records_added = 0
    records_skipped = 0
    print("df columns: ",df.columns)
    df.fillna(-1,inplace=True)
    curr_batch = 1
    batch_size = 10000
    no_of_batches = len(df)/batch_size

    print("no of batches: ",no_of_batches)
    input()
    
    for index, row in df.iterrows():
        while curr_batch <= 4:
            if index<(curr_batch)*batch_size:

                # handling nan values
                # 1. Define Unique Identity 
                # (How do we know this flight is already there? Using 'Pivot Label' + 'FLT_DATE')
                check_query = "SELECT COUNT(*) FROM flight_data WHERE `Pivot_Label` = %s AND FLT_DATE = %s"
                cursor.execute(check_query, (row['Pivot_Label'], row['FLT_DATE']))
                exists = cursor.fetchone()[0]

                if exists > 0:
                    print("Record already exists")
                    records_skipped += 1
                    continue

                # 2. Insert Query
                insert_query = """
                INSERT INTO flight_data (
                    YEAR, MONTH_NUM, MONTH_MON, FLT_DATE, APT_ICAO, APT_NAME, STATE_NAME, 
                    FLT_DEP_1, FLT_ARR_1, FLT_TOT_1, FLT_DEP_IFR_2, FLT_ARR_IFR_2, FLT_TOT_IFR_2, `Pivot_Label`
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                #print("row values: ",row)

                # Tuple of values matching the order above
                values = (
                    row['YEAR'], row['MONTH_NUM'], row['MONTH_MON'], row['FLT_DATE'], 
                    row['APT_ICAO'], row['APT_NAME'], row['STATE_NAME'], 
                    row['FLT_DEP_1'], row['FLT_ARR_1'], row['FLT_TOT_1'], 
                    row['FLT_DEP_IFR_2'], row['FLT_ARR_IFR_2'], row['FLT_TOT_IFR_2'], row['Pivot_Label']
                )
                try:
                    cursor.execute(insert_query, values)
                    records_added += 1
                except Error as e:
                    print(f"⚠️ Error inserting row {index}: {e}")
                print(index)
            else:
                curr_batch += 1
                conn.commit()
                print(f"Batch {curr_batch} is inserted into the DB")

    cursor.close()
    conn.close()
    print(f"✅ Flights Done: {records_added} added, {records_skipped} skipped.")



# ==========================================
# 2. HOTELS IMPORTER
# ==========================================
def import_hotels(csv_file_path, db_configs):
    print(f"\n🏨 Processing Hotels from: {csv_file_path}")
    
    # Load CSV
    # The first column in your sample is unnamed (the index), so we treat it as 'id'
    df = pd.read_csv(csv_file_path)
    df = df.where(pd.notnull(df), None)
    df.columns = df.columns.str.strip()
    df = df.replace({np.nan: None, pd.NA: None, 'nan': None, 'NaN': None})
    print(df.isnull().sum())

    #print(df.loc[998])
    #print(type(df.loc[998,"Guests reviews:"]))

    df = clean_hotel_data(df)

    print("colusmn: ",df.columns)
    
    conn = get_db_connection(db_configs)
    if not conn: 
        return
    
    try:
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO european_hotels (
                id, hotel_name, marks, region_city, performance, 
                reviews_raw, price_raw, distance_raw, description, 
                stars, breakfast, guest_reviews
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE hotel_name=VALUES(hotel_name);
        """
        print("insert query framed")

        print("df.head(): ",df.head())

        batch_size = 5000
        no_of_batches = int(len(df)/batch_size)
        curr_batch = 1

        for ind,row in df.iterrows():
            #print("ind = ",ind)
            if (ind >= (curr_batch-1)*batch_size) and (ind<curr_batch*batch_size):
                row_data =  []
                for col in range(len(df.columns)):
                    row_data.append(row.iloc[col])
                print("row data: ",row_data)
                cleaned_row_data = [
                tuple(None if (isinstance(val, float) and math.isnan(val)) else val for val in row_data)
                ]

                print("cleaned data: ",cleaned_row_data)
                # insert data
                cursor.execute(insert_query, cleaned_row_data[0])
                print(f"records query formed: {ind}")
            else:
                conn.commit()
                curr_batch += 1
                print(f"Batch :{curr_batch-1} is inserted into the DB")
                
        cursor.close()
        conn.close()
        
        print(f"🚀 Import Completed")

    except Exception as e:
        print(f"❌ Error during import: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Note: This assumes you have a helper function 'get_db_connection' defined elsewhere.

if __name__ == "__main__":

    # load data configs
    data_configs = read_yaml("configs/data_configs.yaml")
    print("data configs laoded: ",data_configs)
    print("--------------------------------------------------------\n")
    # load the DB configs
    db_configs = read_yaml("configs/DB_configs.yaml")
    print("dbC-configs loaded successfully: ",db_configs)
    DB_CONFIG = db_configs.flights
    print("FLight configs: \n",DB_CONFIG)

    # import flight data into DB
    #import_flights("data/flights.csv",db_configs=DB_CONFIG)

    # connect to hotels DB
    DB_CONFIG = db_configs.hotels
    print("Hotel configs: \n",DB_CONFIG)
    # import data into hotels DB
    print("hotels csv file path : ",data_configs.ingestion_data_path.hotels_csv_file_path)
    import_hotels(data_configs.ingestion_data_path.hotels_csv_file_path,db_configs=DB_CONFIG)
