# this is a hotel tool funciton that calls the hotel database that dynamically forms the query and result
import requests

def hotel_api_tool(city: str, min_stars: int = 3, max_price: float = None):

    # The agent interprets the user's intent and populates these params
    url = "http://localhost:8000/hotels/search"
    params = {
        "city": city,
        "min_stars": min_stars,
        "max_price": max_price
    }
    
    try:
        # The function executes the network call to your FastAPI/Flask server
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: Hotel API returned status code {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"Connection Error: Could not reach the Hotel Service. {str(e)}"

