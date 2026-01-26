# dynamic query building engine
import os
import sys
# dir changing to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
os.chdir(project_root)
print(f"📂 Execution path anchored to: {os.getcwd()}")

from src.query_engine.query_schema_loader import EngineSchemaLoader
import mysql.connector
from mysql.connector import Error

class HotelQueryEngine(EngineSchemaLoader):
    def __init__(self,db_config_path):
        super().__init__(db_config_path)
        ((host,user,database,password),schema,query_capabilities) = self.read_hotels_engine_schema()
        self.filterable_fields = query_capabilities.filterable_fields
        self.sortable_fields = query_capabilities.sortable_fields
        self.table_name = schema.table_name
        self.table_descripton = schema.description
        self.columns = schema.columns
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def hotel_query_formatter(self, input_params: dict):
        params = input_params.get("hotel_query_engine_params", {})
        agg = params.get("aggregate", {})
        sql_args = []

        # 1. SELECT Clause
        if agg and agg.get("function") and agg.get("column"):
            func, col = agg["function"], agg["column"]
            grp = agg.get("group_by")
            query = f"SELECT {grp}, {func}({col}) AS result FROM european_hotels" if grp else f"SELECT {func}({col}) AS result FROM european_hotels"
        else:
            query = "SELECT * FROM european_hotels"

        query += " WHERE 1=1"

        # 2. Filters & Ranges & Search (Logic identical to Flight Engine)
        # 2. FILTERS (Exact Matches - e.g., region_city, stars, performance)
        filters = params.get("filters", {})
        for field, value in filters.items():
            if value is not None:
                query += f" AND {field} = %s"
                sql_args.append(value)
        # 3. RANGES (Numeric Matches - e.g., marks 8.0-9.0, stars 3-5)
        ranges = params.get("ranges", {})
        for field, bounds in ranges.items():
            if "min" in bounds:
                query += f" AND {field} >= %s"
                sql_args.append(bounds["min"])
            if "max" in bounds:
                query += f" AND {field} <= %s"
                sql_args.append(bounds["max"])
            # Dates (if you add a booking_date later)
            if "start" in bounds:
                query += f" AND {field} >= %s"
                sql_args.append(bounds["start"])
            if "end" in bounds:
                query += f" AND {field} <= %s"
                sql_args.append(bounds["end"])

        # 4. SEARCH (Fuzzy Text - e.g., hotel_name, description, distance_raw)
        search = params.get("search", {})
        for field, value in search.items():
            if value:
                query += f" AND {field} LIKE %s"
                sql_args.append(f"%{value}%")

        # 3. GROUP BY
        if agg and agg.get("group_by"):
            query += f" GROUP BY {agg['group_by']}"

        # 4. Smart ORDER BY
        sort = params.get("sort_by", {})
        sort_col = sort.get("columns")
        if sort_col:
            direction = "DESC" if str(sort.get("descending")).lower() == "true" else "ASC"
            # Use alias 'result' if sorting by the same column we are aggregating
            if agg and sort_col == agg.get("column"):
                query += f" ORDER BY result {direction}"
            else:
                query += f" ORDER BY {sort_col} {direction}"

        query += " LIMIT %s OFFSET %s"
        sql_args.extend([sort.get("limit", 5), sort.get("offset", 0)])

        print("\n\nquery: ",query)
        print("\n\sql args: ",sql_args)
        

        return query, sql_args


    def query_executor(self, query, query_params):
        """Connects to DB, executes query, and returns results as a list of dicts."""
        connection = None
        results = []
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )

            if connection.is_connected():
                # dictionary=True returns rows as {'col': 'val'} instead of tuples
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, query_params)
                results = cursor.fetchall()
                cursor.close()

        except Error as e:
            print(f"❌ Error while connecting to MySQL: {e}")
            return {"error": str(e)}
        
        finally:
            if connection and connection.is_connected():
                connection.close()
                # print("🔌 MySQL connection is closed")
        
        return results



if __name__ == "__main__":

    engine = HotelQueryEngine('configs/DB_configs.yaml')
    params = {
        "hotel_query_engine_params": {
            "filters": {
                "region_city": "Bergenhus, Bergen"
            },
            "ranges": {
                "stars": {
                    "min": 1,
                    "max": 5
                },
                "marks": {
                    "min": 4.0,
                    "max": 10.0
                },
                "distance_raw" :{
                    "min" : 0.5,
                    "max" : 3
                }
            },
            "search": {
                "description": "Standard Room",
                "performance": "Very Good"
            },
            "aggregate": {
                "column": "marks",
                "function": "AVG",
                "group_by": "stars"
            },
            "sort_by": {
                "columns": "marks",
                "descending": True,
                "limit": 10,
                "offset": 0
            }
        }
    }


    sql, params = engine.hotel_query_formatter(params)
    #print("sql: ",sql) 
    #print("params: ",params)
    data = engine.query_executor(sql, params)
    print("data: ",data)

