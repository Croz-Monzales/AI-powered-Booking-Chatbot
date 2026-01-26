from fastapi import FastAPI, Depends
from src.query_engine.flights_query_builder import FlightQueryEngine
from src.query_engine.hotels_query_builder import HotelQueryEngine

app = FastAPI()
engine = FlightQueryEngine('configs/DB_configs.yaml')

@app.get("/hotels/search")
async def search_hotels(params):
    try:
        sql, sql_params = engine.query_formatter(params)
        data = engine.query_executor(sql, sql_params)
        return {"status": "success", "data": data}
    except Exception() as e:
        print(e)
    return {"status":"query error"}
    
    