import os
import google.genai as genai
from dotenv import load_dotenv
from plate_checker_dummy import PlateGetter  

class PlateFinder:
    def __init__(self, api_key=None, model_name='gemini-2.5-flash', base_prompt=None, min_len=1, max_len=6,):
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

        self.min_len = min_len
        self.max_len = max_len

    def generate_plate_ideas(self, prompt, amount_of_ideas=10, rarity=5, not_available=None):
        
        full_prompt = (f"{self.base_prompt}"
                       f"user input: f{prompt}" 
                       f"\nThe rarity index is {str(rarity)} out of 10. 1 meaning be super creative, all common words are already taken and 10 being a lot of vanity plates are still available ONLY go for common words that look very clean and look amazing or are short. Avoid mixing numbers and letters for higher rarities as this is considered unclean."
                       f"\nThe length of the vanity plate should be between {str(self.min_len)} and {str(self.max_len)} characters."
                       f" \n Generate {amount_of_ideas} ideas and return them as a comma-separated list."
                       f" \n following plates have been checked and are not available: {not_available}, find different plates"
        )
        
        response = self.client.models.generate_content(
            model = self.model_name,
            contents=full_prompt
        )
        
        return response.text.split(", ")
    
    def find_available_plates(self, prompt, amount_of_ideas=10, amount_available_plates=3, starting_rarity=10, max_tries = 10):
        
        available = []
        not_available = []
        rarity = starting_rarity
        tries = 0


        while len(available) < amount_available_plates and tries < max_tries:
            plates = self.generate_plate_ideas(prompt, amount_of_ideas, rarity, not_available=not_available)
            
            plate_checker = PlateGetter("California")

            available_batch, not_available_batch = plate_checker.check_plate_availability(plates)

            available.extend(available_batch)
            not_available.extend(not_available_batch)          
            
            if rarity > 1:
                rarity -= 1

            tries += 1

        if len(available) < amount_available_plates:
            print(f"Only found {len(available)} available plates after {tries} tries.")

        


        return available    