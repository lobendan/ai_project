from llm_adapter import PlateFinder
from plate_checker_dummy import PlateGetter
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

# get information from config file 
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "california_config.json"))
with open(config_path, 'r') as f:
    config = json.load(f)

# initialize FastAPI app and PlateFinder class
app = FastAPI(title="Vanity License Plate Finder API")
plate_finder = PlateFinder()

#expected data structure and default values
class PlateRequest(BaseModel):
    description: str
    amount_available_plates: int = 3
    min_len: int = config["plate_checker"]["min_len_state"]
    max_len: int = config["plate_checker"]["max_len_state"]

@app.post("/find-plates")
async def find_plates(request: PlateRequest):
    """REST API POST Endpoint, using underlying modules to find matching available plate ideas based on a given prompt.

    Args: 
        request (PlateRequest Class): includes the following parameters:
            description (str): A prompt describing a theme of the expected vanity plate ideas.
            min_len (int): minimum length of the generated vanity plate ideas
            max_len (int): maximum length of the generated vanity plate ideas
            amount_of_available_plates (int): amount of available plates being returned.

    Returns:
        status (str): wether or not the process has been successful or not
        available_plates (list):  List of available vanity plate ideas.
    """

    if request.amount_available_plates > config["plate_checker"]["max_amount_plates"]:
        raise HTTPException(status_code=400, detail=f"amount_available_plates cannot be greater than {config['plate_checker']['max_amount_plates']}")
    
    if request.min_len < config["plate_checker"]["min_len_state"] or request.max_len > config["plate_checker"]["max_len_state"]:
        raise HTTPException(status_code=400, detail=f"min_len must be at least {config['plate_checker']['min_len_state']} and max_len must be at most {config['plate_checker']['max_len_state']}")

    # find available plate ideas matching the description of the user
    plates = plate_finder.find_available_plates(
        prompt=request.description,
        min_len=request.min_len,
        max_len=request.max_len,
        amount_available_plates=request.amount_available_plates,
        starting_rarity=config["plate_checker"]["starting_rarity"],
        max_tries=config["plate_checker"]["max_tries"],
        amount_of_ideas_multiplier = config["plate_checker"]["amount_of_ideas_multiplier"]
    )

    return {"status": "success", "available_plates": plates}    