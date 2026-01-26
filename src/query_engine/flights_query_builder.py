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

class FlightQueryEngine(EngineSchemaLoader):
    def __init__(self,db_config_path):
        super().__init__(db_config_path)
        ((host,user,database,password),schema,query_capabilities) = self.read_flights_engine_schema()
        self.filterable_fields = query_capabilities.filterable_fields
        self.aggregatable_fields = query_capabilities.aggregatable_fields
        self. traffic_volume = query_capabilities.logical_groups.traffic_volume
        self.ifr_metrics = query_capabilities.logical_groups.ifr_metrics
        self.table_name = schema.table_name
        self.table_descripton = schema.description
        self.columns = schema.columns
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def query_formatter(self, input_params: dict):

        params = input_params.get("flight_query_engine_params", {})
        agg = params.get("aggregate", {})
        sql_args = []

        # 1. SELECT Clause (Dynamic Aggregation)
        # If an aggregate function is provided, we change the SELECT behavior
        if agg and agg.get("function") and agg.get("column"):
            func = agg.get("function")
            col = agg.get("column")
            group_field = agg.get("group_by")
            
            if group_field:
                query = f"SELECT {group_field}, {func}({col}) AS result FROM {self.table_name}"
            else:
                query = f"SELECT {func}({col}) AS result FROM {self.table_name}"
        else:
            query = f"SELECT * FROM {self.table_name}"

        query += " WHERE 1=1"

        # 2. FILTERS (Exact Matches)
        filters = params.get("filters", {})
        for field, value in filters.items():
            if value is not None:
                query += f" AND {field} = %s"
                sql_args.append(value)

        # 3. RANGES (Min/Max and Start/End)
        ranges = params.get("ranges", {})
        for field, bounds in ranges.items():
            # Handle Numeric Ranges
            if "min" in bounds:
                query += f" AND {field} >= %s"
                sql_args.append(bounds["min"])
            if "max" in bounds:
                query += f" AND {field} <= %s"
                sql_args.append(bounds["max"])
            # Handle Date/Time Ranges
            if "start" in bounds:
                query += f" AND {field} >= %s"
                sql_args.append(bounds["start"])
            if "end" in bounds:
                query += f" AND {field} <= %s"
                sql_args.append(bounds["end"])

        # 4. SEARCH (Fuzzy Text)
        search = params.get("search", {})
        for field, value in search.items():
            if value:
                query += f" AND {field} LIKE %s"
                sql_args.append(f"%{value}%")

        # 5. GROUP BY Clause
        if agg and agg.get("group_by"):
            query += f" GROUP BY {agg.get('group_by')}"

        # 6. ORDER BY & PAGINATION
        sort = params.get("sort_by", {})
        sort_col = sort.get("columns")

        if sort_col:
            is_desc = str(sort.get("descending")).lower() == "true"
            direction = "DESC" if is_desc else "ASC"
    
            if agg and agg.get("function") and sort_col == agg.get("column"):
                query += f" ORDER BY result {direction}"
            else:
                query += f" ORDER BY {sort_col} {direction}"

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

# usage
if __name__ == "__main__":
    engine = FlightQueryEngine('configs/DB_configs.yaml')
    params = {
        "flight_query_engine_params": {
            "filters": {
                "STATE_NAME": "Texas",
                "YEAR": 2024
            },
            "ranges": {
                "FLT_TOT_1": {
                    "min": 500,
                    "max": 5000
                },
                "FLT_DATE": {
                    "start": "2024-01-01",
                    "end": "2024-03-31"
                }
            },
            "search": {
                "APT_NAME": "International"
            },
            "aggregate": {
                "column": "FLT_TOT_1",
                "function": "SUM",
                "group_by": "MONTH_MON"
            },
            "sort_by": {
                "columns": "FLT_TOT_1",
                "descending": True,
                "limit": 12,
                "offset": 0
            }
        }
    }

    sql, params = engine.query_formatter(params)
    #print("sql: ",sql)
    #print("params: ",params)
    data = engine.query_executor(sql, params)
    print("data: ",data)

