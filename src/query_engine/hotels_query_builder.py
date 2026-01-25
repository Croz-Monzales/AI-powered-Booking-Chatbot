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

    def query_formatter(self, params: dict):
        """
        Takes a dict of parameters from the Agent and returns (SQL, Params)
        """
        query = f"SELECT * FROM {self.table_name} WHERE 1=1"
        query_params = []

        # 1. Dynamic Filtering based on filterable_fields
        for field in self.filterable_fields:
            if field in params and params[field] is not None:
                query += f" AND {field} = %s"
                query_params.append(params[field])

        # 2. Dynamic Sorting
        if "sort_by" in params and params["sort_by"] in self.columns:
            direction = "DESC" if params.get("descending") else "ASC"
            query += f" ORDER BY {params['sort_by']} {direction}"

        # 3. Limit to protect Agent context window
        limit = params.get("limit", 5)
        query += " LIMIT %s"
        query_params.append(limit)
        return query, query_params

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


engine = HotelQueryEngine('configs/DB_configs.yaml')
sql, params = engine.query_formatter({"region_city": "Bergen", "limit": 2})
#print("sql: ",sql)
#print("params: ",params)
data = engine.query_executor(sql, params)
print("data: ",data)

