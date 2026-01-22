from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import Field,BaseModel
from langgraph.graph import START,END,StateGraph
from langgraph.graph.message import add_messages,BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated,Literal,List
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig
import operator
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# building a travel assistant chatbot without external dependencies

# base llm
llm = ChatOllama(
    model = "llama3.1:8b",
    temperature =  0
)

class FlightDetails(BaseModel):
    origin: str = Field(
        description="The three-letter IATA airport code for the departure city (e.g., 'JFK', 'LHR')."
    )
    destination: str = Field(
        description="The three-letter IATA airport code for the arrival city (e.g., 'LAX', 'DXB')."
    )
    departure_date: date = Field(
        description="The date of departure in YYYY-MM-DD format."
    )
    return_date: Optional[date] = Field(
        default=None, 
        description="The return date for round trips in YYYY-MM-DD format. Leave empty for one-way."
    )
    cabin_class: str = Field(
        default="economy",
        description="The preferred cabin class: 'economy', 'premium_economy', 'business', or 'first'."
    )
    passengers: int = Field(
        default=1,
        ge=1,
        description="Number of adult passengers."
    )
    max_price: Optional[float] = Field(
        default=None,
        description="The maximum budget for the flight in USD."
    )

class HotelDetails(BaseModel):
    location: str = Field(
        description="The city or specific area where the user wants to stay (e.g., 'Manhattan, NY' or 'Tokyo')."
    )
    checkin_date: date = Field(
        description="The date the user arrives at the hotel in YYYY-MM-DD format."
    )
    checkout_date: date = Field(
        description="The date the user leaves the hotel in YYYY-MM-DD format."
    )
    guests: int = Field(
        default=1,
        ge=1,
        description="Total number of guests staying in the room."
    )
    room_type: Optional[str] = Field(
        default="Standard",
        description="Type of room requested (e.g., 'Suite', 'Deluxe', 'Twin', 'King')."
    )
    max_budget: Optional[float] = Field(
        default=None,
        description="Maximum price the user is willing to pay per night."
    )
    amenities: list[str] = Field(
        default_factory=list,
        description="A list of required amenities like ['WiFi', 'Pool', 'Breakfast', 'Gym']."
    )
    star_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="The minimum star rating for the hotel (1 to 5)."
    )



# state definition

class state(TypedDict) :
    messages : Annotated[list,add_messages]
    checklist : Literal["enquiry","travel country","travel destination","iternary","flight booking","hotel booking"]
    travel_country: Annotated[List[str],operator.add]
    travel_destination : Annotated[List[str],operator.add]
    itinerary_status: Literal["Not Started", "Drafted", "Confirmed"]
    flight_booking_status: Literal["Not Asked", "Searching", "Booked"]
    hotel_booking_status: Literal["Not Asked", "Searching", "Booked"]
    flight_details: FlightDetails
    hotel_details: HotelDetails

# nodes definition

# main node - takes care of the general flow, re-iterates and thinks of the questions to ask depending on the status

# flight details - uses APIs from flight database and communictes regarding the dates and processes

# hotel details - uses APIs to interact with hotel database and communication

# iternary finalizer - plans the itenary with things to do

# Human-in-loop for further refinement of details