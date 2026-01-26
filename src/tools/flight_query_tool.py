# this is a flights tool funciton that calls the hotel database that dynamically forms the query and result
import requests
from langchain_core.tools import tool
from ..output_parsers import FlightQueryEngineParams

@tool
def flight_api_tool(params_class: FlightQueryEngineParams):
    # conversion of params_class to  fit into JSON
    json_params = params_class.model_dump(exclude_none=True)

    params = {
        "flight_query_engine_params": json_params
    }

    # The agent calls this Python function...
    url = "http://localhost:8000/flights/search"
    
    # ...and the function calls your API
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: API returned {response.status_code}"

