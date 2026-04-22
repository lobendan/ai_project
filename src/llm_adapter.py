import os
import google.genai as genai
from dotenv import load_dotenv
from plate_checker_dummy import PlateGetter 
from google.genai import types

class PlateFinder:
    "Main class orchestrating the whole vanity plate process, using LLMs to generate vanity plate ideas and directly checking for their availability in one"
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
        """Generates plate ideas based on a prompt and some other parameters.

        Args:
            prompt (str): A prompt describing a theme of the expected vanity plate ideas
            min_len (int): minimum length of the generated vanity plate ideas
            max_len (int): maximum length of the generated vanity plate ideas
            (optional) amount_of_ideas (int): amount of ideas being generated. Defaults to 10.
            (optional) rarity (int): rarity index from 1 to 10, 1 representing a very creative idea, which is most likely not taken already and 10 describing the most clean and desirable vanity plates. Defaults to 5.
            (optional) checked (list): list  of vanity plates, which have been checked already. Defaults to None.

        Returns: 
            List of vanity plate ideas.


        """   
        full_prompt = (f"{self.base_prompt}"
                       f"user input: f{prompt}" 
                       f"\nThe rarity index is {str(rarity)} out of 10. 1 meaning be super creative, all common words are already taken and 10 being a lot of vanity plates are still available ONLY go for common words that look very clean and look amazing or are short. Avoid mixing numbers and letters for higher rarities as this is considered unclean."
                       f"\nThe length of the vanity plate should be between {str(min_len)} and {str(max_len)} characters."
                       f"\n Generate {amount_of_ideas} ideas and return them as a comma-separated list."
                       f"\n following plates have been checked: {checked}, find different plates"
        )
        
        # limiting output tokens to reduce token spending. 30 output tokens are available per idea.
        model_config = types.GenerateContentConfig(
                        max_output_tokens=amount_of_ideas * 30,  
                        temperature=0.8,
                    )
        
        done = False
        # get response from the LLM
        while done == False:
            try:
                response = self.client.models.generate_content(
                    model = self.model_name,
                    contents=full_prompt, 
                    config=model_config
                )
                done = True

            except Exception as e:
                if e.code == 504:
                    print("Request timed out. Retrying...")
                else:
                    print(f"An error occurred: {e}")
                    raise e


        return response.text.split(", ")
    

    def find_available_plates(self, prompt, min_len, max_len, amount_available_plates=3, starting_rarity=10, max_tries = 10, amount_of_ideas_multiplier = 3):
        """ Generates plate ideas based on a prompt and then checks for their availability. It repeats this process until the desired amount of ideas is found, or the maximum amount of loop iterations is reached.

        Args: 
            prompt (str): A prompt describing a theme of the expected vanity plate ideas
            min_len (int): minimum length of the generated vanity plate ideas
            max_len (int): maximum length of the generated vanity plate ideas
            (optional) amount_of_available_plates (int): amount of available plates being returned. Defaults to 3.
            (optional) starting_rarity (int): starting rarity index from 1 to 10, 1 representing a very creative idea, which is most likely not taken already and 10 describing the most clean and desirable vanity plates. Defaults to 10.
            (optional) max_tries (int): maximum amount of loop iterations, where the minimum amount of available plates was not found until loop breaks. Defaults to 10.
            (optional) amount_of_ideas_multiplier (int): multiplier of the amount of ideas being generated by the LLM, which then get checked for availabity (multiplies with amount_of_available_plates).  Defaults to 3.      
        
        Returns: 
            List of available vanity plate ideas.
        """
        available = []
        not_available = []
        rarity = starting_rarity
        tries = 0
        amount_of_ideas = amount_available_plates * amount_of_ideas_multiplier #generate the specified multiple of ideas, which then gets checked

        while len(available) < amount_available_plates and tries < max_tries:
            checked = available + not_available # used to not let the LLM generate these ideas again
            plates = self.generate_plate_ideas(prompt, min_len, max_len, amount_of_ideas, rarity, checked=checked) # generate ideas
            
            # check availability of the ideas (currently using a dummy - no actual information is used.)
            plate_checker = PlateGetter("California")
            available_batch, not_available_batch = plate_checker.check_dummy_availability(plates)

            available.extend(available_batch)
            not_available.extend(not_available_batch)          
            
            # reducing rarity index, to increase the chance of finding available vanity plate ideas
            if rarity > 1:
                rarity -= 1

            tries += 1

        # print a warning, if less than the desired amount of plates was found
        if len(available) < amount_available_plates:
            print(f"Only found {len(available)} available plates after {tries} tries.")

        return available    