from typing import Optional, Dict, Literal, Union
from pydantic import BaseModel, Field
from typing import Optional, Union
from pydantic import BaseModel, Field


FlightCols = Literal[
    "STATE_NAME", "YEAR", "APT_NAME", "FLT_DATE", 
    "FLT_TOT_1", "MONTH_MON", "APT_ICAO", "DISTANCE"
]

NumericCols = Literal["FLT_TOT_1", "DISTANCE", "YEAR"]
DateCols = Literal["FLT_DATE"]
CategoricalCols = Literal["STATE_NAME", "APT_NAME", "MONTH_MON", "APT_ICAO"]

#-----------------------------------------------------------
# Sub-Models with Column Restrictions

class RangeModel(BaseModel):
    min: Optional[float] = Field(None, description="Min value for numeric columns")
    max: Optional[float] = Field(None, description="Max value for numeric columns")
    start: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

class AggregateModel(BaseModel):
    column: NumericCols = Field(..., description="The numeric column to aggregate")
    function: Literal["SUM", "AVG", "COUNT", "MIN", "MAX"] = Field(...)
    group_by: Optional[CategoricalCols] = Field(None, description="Column to group by")

class SortModel(BaseModel):
    columns: FlightCols = Field(..., description="Column to sort by")
    descending: bool = True
    limit: int = Field(12, ge=1, le=100)
    offset: int = 0



#-----------------------------------------------------------
# Consolidated flight params
class FlightQueryEngineParams(BaseModel):          # this is connected with the tool
                                                   # the JSON schema is used to call the DB from API
    filters: Dict[CategoricalCols, str] = Field(
        default_factory=dict, 
        description="Exact matches for categories like State or ICAO."
    )
    ranges: Dict[Union[NumericCols, DateCols], RangeModel] = Field(
        default_factory=dict, 
        description="Ranges for dates or numbers."
    )
    search: Dict[CategoricalCols, str] = Field(
        default_factory=dict, 
        description="Fuzzy matches for text fields like State name, APT_name"
    )
    aggregate: Optional[AggregateModel] = None
    sort_by: SortModel = Field(default_factory=lambda: SortModel(columns="FLT_DATE"))

class FlightAgentResponse(BaseModel):
    """The final response from the Flight Agent."""
    
    agent_response: str = Field(
        ..., 
        description="The data that is to be returned to the question asked. It can be data from tool or actual thought answer"
    )
    
    params: Optional[FlightQueryEngineParams] = Field(
        None, 
        description="The structured SQL parameters for the database call."
    )
