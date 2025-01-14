import os  
import pandas as pd
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_community.callbacks.manager import get_openai_callback

# Load environment variables
load_dotenv(override=True)

# Define LLM (choose between Ollama and OpenAI)
llm = ChatOpenAI(model="gpt-4o",temperature=0)

TEMP_FILE_PATH = os.path.join("temp", "processed_temp.xlsx")

class WordInfo(BaseModel):
    id: int = Field(..., description="The unique identifier for the word, typically used to reference the word in a database or lexicon.")
    word: str = Field(..., description="The word to process, a valid string representing a lexical unit.")
    part_of_speech: str = Field(..., description="The grammatical category of the word (e.g., noun, verb, adjective, etc.).")
    definition: str = Field(..., description="A clear and concise explanation of the word's meaning.")
    example_usage: str = Field(..., description="A grammatically correct sentence demonstrating the word's usage in context.")
    etymology: str = Field(..., description="A historical account of the word's origin and its evolution over time, including language of origin, transformations, and key influences.")

def create_temp_folder():
    """Create a temporary folder if it doesn't exist."""
    os.makedirs("temp", exist_ok=True)

def load_existing_data() -> pd.DataFrame:
    """Load existing data from the temporary file."""
    if os.path.exists(TEMP_FILE_PATH):
        return pd.read_excel(TEMP_FILE_PATH)
    return pd.DataFrame(columns=["id", "word", "part_of_speech", "definition", "example_usage", "etymology"])

def save_temp_excel(processed_data: pd.DataFrame):
    """Save processed rows to a temporary Excel file, appending new data."""
    create_temp_folder()
    existing_data = load_existing_data()
    combined_data = pd.concat([existing_data, processed_data]).drop_duplicates(subset="id")
    
    # Convert 'id' column to integer before sorting
    combined_data['id'] = combined_data['id'].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    combined_data = combined_data.sort_values(by="id")  # Ensure rows are sorted by 'id'
    combined_data.to_excel(TEMP_FILE_PATH, index=False)
    print(f"Temporary file updated: {TEMP_FILE_PATH}")

def retry_until_success(func, delay=2, max_retries=5):
    """Retries a function call until it succeeds, with a delay between retries."""
    attempt = 1
    while attempt <= max_retries:
        try:
            return func()
        except Exception as e:
            print(f"Error: {e}. Retry attempt {attempt} in {delay} seconds...")
            time.sleep(delay)
            attempt += 1
    raise Exception(f"Failed after {max_retries} attempts")

def process_batch(batch_input_list, structured_llm_with_prompt):
    """Process a batch of rows using the LLM and return the filled rows."""
    with get_openai_callback() as cb:
        responses = structured_llm_with_prompt.batch(batch_input_list)
        print(str(cb))
        
    filled_rows = []
    for response in responses:
        if isinstance(response, WordInfo):
            data = {
                "id": response.id,
                "word": response.word,
                "part_of_speech": response.part_of_speech,
                "definition": response.definition,
                "example_usage": response.example_usage,
                "etymology": response.etymology,
            }
            filled_rows.append(data)
        else:
            raise ValueError(f"Invalid response type: {type(response)}")
    
    return filled_rows

def fill_missing_values_for_row(doc, llm, status):
    """
    Uses the LLM to fill missing values in rows while supporting resume functionality.
    Processes rows in batches of 1000.
    """
    processed_data = load_existing_data()
    processed_ids = set(processed_data["id"])  # Set of IDs already processed
    rows_to_process = doc[~doc["id"].isin(processed_ids)]  # Filter rows not yet processed

    total_rows = len(doc)  # Total number of rows in the input file
    pending_rows = len(rows_to_process)  # Rows left to process

    print(f"Resuming from the last state. {pending_rows}/{total_rows} rows left to process.")

    batch_input_list = []
    filled_rows_list = []

    structured_llm = llm.with_structured_output(schema=WordInfo)
    for index, row in rows_to_process.iterrows():
        # Skip the row if all columns have valid values (no NaN, empty strings, or "Na")
        if all(pd.notna(row[["part_of_speech", "definition", "example_usage", "etymology"]]) & 
               (row[["part_of_speech", "definition", "example_usage", "etymology"]] != '') & 
               (row[["part_of_speech", "definition", "example_usage", "etymology"]] != 'Na')):
            #print(f"Skipping row ID={row['id']} as it has no missing values.")
            filled_rows_list.append(row.to_dict())
            continue  # Skip this row

        # Update the status to display ID, word, and pending rows
        current_progress = f"Processing: ID={row['id']}, Word='{row['word']}' | Pending: {pending_rows}/{total_rows}"
        status.update(label=current_progress)
        print(current_progress)

        row_data = {
            "id": str(row["id"]),
            "word": row["word"],
            "part_of_speech": "Na",
            "definition": "Na",
            "example_usage": "Na",
            "etymology": "Na",
        }
        batch_input_list.append(str(row_data))
        pending_rows -= 1

        # Process the batch if we've accumulated 1000 rows
        if len(batch_input_list) == 1:
            filled_rows = retry_until_success(lambda: process_batch(batch_input_list, structured_llm))
            print(filled_rows)
            filled_rows_list.extend(filled_rows)
            batch_input_list.clear()  # Clear the batch after processing

            # Save the filled rows temporarily to avoid memory overflow
            temp_df = pd.DataFrame(filled_rows_list)
            save_temp_excel(temp_df)
            filled_rows_list.clear()

    # Process any remaining rows (less than 1000)
    if batch_input_list:
        filled_rows = retry_until_success(lambda: process_batch(batch_input_list, structured_llm))
        filled_rows_list.extend(filled_rows)
        batch_input_list.clear()

    # Save the remaining rows
    if filled_rows_list:
        temp_df = pd.DataFrame(filled_rows_list)
        save_temp_excel(temp_df)

def process_file_gpt(file, status):
    """
    Processes an Excel file row by row and fills missing values using the LLM.
    """
    doc = pd.read_excel(file)
    fill_missing_values_for_row(doc, llm, status)

    # Save the final processed document, ensuring it's sorted by 'id'
    final_data = load_existing_data()
    
    # Convert 'id' column to integer before sorting
    final_data['id'] = final_data['id'].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    final_data = final_data.sort_values(by="id")  # Ensure final data is sorted by 'id'
    final_data.to_excel("processed_final.xlsx", index=False)
    print("Final file saved as 'processed_final.xlsx'")
    return final_data
