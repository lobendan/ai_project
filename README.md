# ai_project
Project repository for ECE570.

This project generates vanity plate ideas with an LLM, checks which ones are available, and returns a curated list through a FastAPI endpoint.

## Environment Setup and Quick Start

### 1) Create and activate a virtual environment

From the project root:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install all Python dependencies

From the project root:

```bash
pip install -r requirements.txt
```

Dependency list file:

- [requirements.txt](./requirements.txt)

### 3) Configure the API key

Create a `.env` file in the project root and add (get your API key in the [Google AI Studio](https://aistudio.google.com/)):

```bash
GEMINI_API_KEY=your_api_key_here
```


### Starting the backend

```bash
cd src
uvicorn api:app --reload
```
An overall UI can be accessed in the browser using this URL: http://127.0.0.1:8000/docs.
An example Rest API Call can be run, with a custom vanity plate prompt. This can be accessed by POST /find-plates>Try it out>Edit value: adjust the value of the "description" key and then click "Execute". After a few seconds the response body, with the vanity plate ideas can be seen below. 

#### Demo UI

The Demo UI, that is described in the paper, is much more complicated to get running on another device and wasn't built to be shipped. The retool UI can be imported using the [VanityPlateFinderDemo.json](retool\VanityPlateFinderDemo.json) file. For further instructions or a personal demo, please reach out to the developer: dlobenst@purdue.edu.


## Architecture Diagram

The overall design is shown below:

![AI Plate Getter Architecture](docs/AIPlateGetter.drawio.png)

How to read the diagram from left to right:

1. UI sends `POST /find-plates` to the API Server.
2. API Server enters a loop that tries to find enough available candidates:
3. API Server requests a batch of plate ideas from the LLM API (`generate_plate_ideas()`).
4. API Server sends that batch to the plate checker (`check_plates()` in concept, implemented as `check_dummy_availability()` in the current code).
5. The checker returns available/unavailable batches.
6. API Server repeats the loop until it has enough available plates or reaches retry limits.
7. API Server returns `List<AvailablePlates>` to the UI.

## Code Walkthrough

### 1) API layer: request validation and orchestration

File: [src/api.py](./src/api.py)

Responsibilities:
- Defines FastAPI app and endpoint: `POST /find-plates`.
- Defines request schema with `PlateRequest` (description, desired count, min/max lengths).
- Loads state-specific constraints and retry settings from `config/california_config.json`.
- Validates user input before calling the generation/check pipeline.
- Returns final available plate list as JSON.

Key behavior:
- Rejects `amount_available_plates` above configured max.
- Rejects length bounds outside state limits.
- Calls `PlateFinder.find_available_plates(...)` with config-driven parameters.

### 2) LLM adapter: idea generation and iterative search

File: [src/llm_adapter.py](./src/llm_adapter.py)

Responsibilities:
- Wraps Gemini client setup (`PlateFinder`).
- Generates plate candidate batches with prompt instructions.
- Runs retry loop to accumulate enough available plates.
- Decreases rarity over time to broaden candidate search.

Main methods:

- `find_available_plates(...)`
	- Computes batch size (`amount_available_plates * amount_of_ideas_multiplier`).
	- Tracks `available` and `not_available` to reduce repeats.
	- For each iteration:
		- generate candidate ideas from LLM,
		- check availability via `PlateGetter`,
		- merge results,
		- reduce rarity,
		- stop on success or max tries.
		- method corresponds directly to the loop shown in the diagram


-  `generate_plate_ideas(...)`
   -  called inside of `find_available_plates` method
	- Builds a full prompt from base prompt + user description + constraints.
	- Calls Gemini model and parses comma-separated results.
	- Retries on timeout-like failures.


### 3) Plate availability checker

File: [src/plate_checker_dummy.py](./src/plate_checker_dummy.py)

Responsibilities:
- Provides the dummy availability-checking interface used by `PlateFinder`.
- Contains two implementations:
	- `check_dummy_availability(...)`: simulated checker (currently active path).
	- `check_plate_availability(...)`: DB-assisted path for real/background updates. (not active right now - see comments in the code)
  

Current runtime path:
- `check_dummy_availability(...)` simulates availability using randomness and length filtering.

Intended production path:
- In architecture terms, this is the placeholder for the DMV Vanity Plate Availability API lane.
- method can be replaced with minimal effort to actual production API lane, with having to adjust minimal amounts of code in the rest of the project.

### 4) Configuration as control plane

File: [config/california_config.json](./config/california_config.json)

The API and loop behavior are tuned through config values:

- `min_len_state`, `max_len_state`: legal character bounds.
- `starting_rarity`: first-pass strictness/creativity setting for generation.
- `max_amount_plates`: upper limit accepted from API callers.
- `max_tries`: loop safeguard to stop searching after N iterations.
- `amount_of_ideas_multiplier`: batch size scale per iteration.

This lets you tune quality, speed, and API cost without changing code.

## End-to-End Flow (Connected View)

1. User provides a description (for example: "clean, sporty, short", length: 3-5 characters long, 5 different options).
2. UI calls `POST /find-plates`.
3. `api.py` validates request using state config limits.
4. `PlateFinder` asks Gemini for a candidate batch.
5. Candidate batch is checked for availability.
6. Available candidates are accumulated; checked candidates are tracked to avoid repeats.
7. If not enough are available, rarity is adjusted and the loop repeats.
8. Final list of available plates is returned to the UI.

## Notes

- Environment variable required by `PlateFinder`: `GEMINI_API_KEY`.
- The current checker path is simulated; replacing or wiring `check_plate_availability(...)` to a live DMV source completes the rightmost part of the diagram.


## Disclaimer:
Text in this README file has been improved using an LLM.