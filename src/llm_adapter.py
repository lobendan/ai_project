import os
import google.genai as genai
from dotenv import load_dotenv
from networkx import config
from plate_checker_dummy import PlateGetter 
import time 
from google.genai import types

class PlateFinder:
    def __init__(self, api_key=None, model_name='gemini-2.5-flash', base_prompt=None, ):
        load_dotenv()  # Load environment variables from .env file
        
        if api_key is None: 
            self.api_key = os.getenv('GEMINI_API_KEY')
        else:  
            self.api_key = api_key

        if self.api_key is None:
            raise ValueError("API key not found. Either define 'GEMINI_API_KEY' in .env or use the api_key parameter. Here is some information about me: ")

        self.model_name = model_name
        
        self.client = genai.Client(api_key=self.api_key)
        
        if base_prompt is None:
            self.base_prompt = "Help me find ideas of words that I could use for my vanity license plate. "
        
        else:
            self.base_prompt = base_prompt


    def generate_plate_ideas(self, prompt, min_len, max_len, amount_of_ideas=10, rarity=5, checked=None):
        
        full_prompt = (f"{self.base_prompt}"
                       f"user input: f{prompt}" 
                       f"\nThe rarity index is {str(rarity)} out of 10. 1 meaning be super creative, all common words are already taken and 10 being a lot of vanity plates are still available ONLY go for common words that look very clean and look amazing or are short. Avoid mixing numbers and letters for higher rarities as this is considered unclean."
                       f"\nThe length of the vanity plate should be between {str(min_len)} and {str(max_len)} characters."
                       f"\n following plates have been checked: {checked}, find different plates"
        )
        
        model_config = types.GenerateContentConfig(
                        max_output_tokens=amount_of_ideas * 100,  
                        temperature=0.8,
                    )
        start_time = time.perf_counter()
        response = self.client.models.generate_content(
            model = self.model_name,
            contents=full_prompt, 
            config=model_config
        )
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"The code took {execution_time:.4f} seconds to run. Response: {response.text} \n Prompt was: {full_prompt}")
        
        return response.text.split(", ")
    
    def find_available_plates(self, prompt, min_len, max_len, amount_available_plates=3, starting_rarity=10, max_tries = 10, amount_of_ideas_multiplier = 3):
        
        available = []
        not_available = []
        rarity = starting_rarity
        tries = 0
        amount_of_ideas = amount_available_plates * amount_of_ideas_multiplier #generate the specified multiple of ideas, which then get checked


        while len(available) < amount_available_plates and tries < max_tries:
            checked = available + not_available
            plates = self.generate_plate_ideas(prompt, min_len, max_len, amount_of_ideas, rarity, checked=checked)
            
            plate_checker = PlateGetter("California")

            available_batch, not_available_batch = plate_checker.check_dummy_availability(plates)

            available.extend(available_batch)
            not_available.extend(not_available_batch)          
            
            if rarity > 1:
                rarity -= 1

            tries += 1

        if len(available) < amount_available_plates:
            print(f"Only found {len(available)} available plates after {tries} tries.")

        


        return available    