import os
import sys
# dir changing to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
os.chdir(project_root)
print(f"📂 Execution path anchored to: {os.getcwd()}")

from src.utils.all_readers import read_yaml

class EngineSchemaLoader:
    def __init__(self,db_config_path):
        self.config_path = db_config_path

    def read_flights_engine_schema(self):
        db_schemas = read_yaml(self.config_path)
        print(db_schemas)
        #print("flight DB schema: ",db_schemas.flights.schema)
        #print("flights queryable params: ",db_schemas.flights.query_capabilities)
        return ((db_schemas.flights.host,db_schemas.flights.user,db_schemas.flights.database,db_schemas.flights.password), db_schemas.flights.schema,db_schemas.flights.query_capabilities)
        
    def read_hotels_engine_schema(self):
        db_schemas = read_yaml(self.config_path)
        print(db_schemas)
        #print("hotels DB schema: ",db_schemas.hotels.schema)
        #print("hotels queryable params: ",db_schemas.hotels.query_capabilities)
        return ((db_schemas.hotels.host,db_schemas.hotels.user,db_schemas.hotels.database,db_schemas.hotels.password), db_schemas.hotels.schema,db_schemas.hotels.query_capabilities)


# usage
if __name__ ==  "__main__":
    schema_loader = EngineSchemaLoader(db_config_path='configs/DB_configs.yaml')
    print(schema_loader.read_hotels_engine_schema())
