from fastapi import FastAPI, Depends
from src.query_engine.engines import FlightQueryEngine

app = FastAPI()
engine = FlightQueryEngine('configs/DB_configs.yaml')

@app.get("/flights/search")
async def search_flights(params):
    try:
        sql, sql_params = engine.query_formatter(params)
        data = engine.query_executor(sql, sql_params)
        return {"status": "success", "data": data}
    except Exception() as e:
        print(e)

    return {"status":"Failed"}

    
