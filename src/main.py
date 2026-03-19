from llm_adapter import PlateFinder
from plate_checker_dummy import PlateGetter

if __name__ == "__main__":
    plate_finder = PlateFinder(min_len=1, max_len=7)
    plate_getter = PlateGetter("California")
    
    example_description = "Green 911 GTRS, born in Europe, soccer lover"

    # get plate ideas
    plates = plate_finder.find_available_plates(example_description, amount_of_ideas=5, amount_available_plates=3, starting_rarity=5, max_tries=10)

    print("response: ", plates)
    




