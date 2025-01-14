import os 
import pandas as pd
import json
import time
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Define LLM
llm = ChatOllama(model="llama3.2", temperature=0, format="json")

TEMP_FILE_PATH = os.path.join("temp", "processed_temp.xlsx")

def create_temp_folder():
    """
    Creates a temporary folder named 'temp' if it doesn't exist.
    """
    if not os.path.exists("temp"):
        os.makedirs("temp")

def load_existing_data():
    """
    Loads existing data from the temporary file, if it exists. Ensures data is sorted by 'id'.
    """
    if os.path.exists(TEMP_FILE_PATH):
        data = pd.read_excel(TEMP_FILE_PATH)
        # Ensure 'id' is converted to integer before sorting
        data["id"] = data["id"].astype(int)  # Convert 'id' to integer type
        return data.sort_values(by="id").reset_index(drop=True)
    else:
        return pd.DataFrame(columns=["id", "word", "part_of_speech", "definition", "example_usage", "etymology"])

def save_temp_excel(processed_data):
    """
    Saves the processed rows to a temporary Excel file in the 'temp' folder.
    Appends new data to existing rows and ensures the final data is sorted by 'id'.
    """
    create_temp_folder()
    existing_data = load_existing_data()
    combined_data = pd.concat([existing_data, processed_data]).drop_duplicates(subset="id")
    # Ensure 'id' is converted to integer before sorting
    combined_data["id"] = combined_data["id"].astype(int)  # Convert 'id' to integer type
    sorted_data = combined_data.sort_values(by="id").reset_index(drop=True)
    sorted_data.to_excel(TEMP_FILE_PATH, index=False)
    print(f"Temporary file updated: {TEMP_FILE_PATH}")

def retry_until_success(func, delay=2, retries=3):
    """
    Retries a function call up to 'retries' times until it succeeds, with a specified delay between retries.
    """
    attempt = 1
    while attempt <= retries:
        try:
            return func()
        except Exception as e:
            print(f"Error occurred: {e}. Retry attempt {attempt} in {delay} seconds...")
            time.sleep(delay)
            attempt += 1
    raise Exception(f"Function failed after {retries} retries.")

def fill_missing_values_for_row(doc, llm, status):
    """
    Uses the LLM to fill missing values in rows while supporting resume functionality.
    Displays status updates with the id and word being processed and the number of rows remaining.
    """
    processed_data = load_existing_data()
    processed_ids = set(processed_data["id"])  # Set of IDs already processed
    rows_to_process = doc[~doc["id"].isin(processed_ids)]  # Filter rows not yet processed

    # Ensure 'id' is converted to integer before sorting
    rows_to_process["id"] = rows_to_process["id"].astype(int)  # Convert 'id' to integer type
    rows_to_process = rows_to_process.sort_values(by="id").reset_index(drop=True)

    total_rows = len(doc)  # Total number of rows in the input file
    pending_rows = len(rows_to_process)  # Rows left to process

    print(f"Resuming from the last state. {pending_rows}/{total_rows} rows left to process.")

    filled_rows_list = []

    prompt_template = """ 
    You are an expert language assistant specializing in completing missing information in a dataset. Your task is to generate accurate details for a word based on the provided input. You will receive "id" and "word" columns, and your job is to fill in the missing columns: "part_of_speech", "definition", "example_usage", and "etymology". These fields will never be empty as all words are standard English words.

    ### Input Format:
    "id: <id>, word: <word>, part_of_speech: nan, definition: nan, example_usage: nan, etymology: nan"

    ### Output Format:
    - Return the result as a valid **JSON dictionary** in string format.
    - The output should follow this structure strictly, where the keys and values are enclosed in double quotes and no extra characters or comments should be included:
    "\"id\": \"<id>\", \"word\": \"<word>\", \"part_of_speech\": \"<part_of_speech>\", \"definition\": \"<definition>\", \"example_usage\": \"<example_usage>\", \"etymology\": \"<etymology>\""

    ### Column Descriptions:
    1. **id**: The unique identifier for the word (given in the input).
    2. **word**: The word to process (given in the input).
    3. **part_of_speech**: The grammatical category of the word (e.g., noun, verb, adjective).
    4. **definition**: A clear and concise explanation of the word's meaning in its most common usage.
    5. **example_usage**: A grammatically correct sentence that demonstrates how the word is used in context. The sentence must **strictly use the original word** and accurately reflect the word’s meaning and part of speech. **Do not use synonyms, related words, or homophones**. The example should be directly relevant to the word’s most common usage and should not be misinterpreted or misleading.
    6. **etymology**: A historical account of the word's origin, including its root languages and how its meaning has evolved over time.

    ### Guidelines:
    - **Accuracy**: Ensure that the information is linguistically correct and derived from reliable sources. Definitions must align precisely with the word's most common usage.
    - **Clarity**: Definitions and examples should be brief, unambiguous, and easy to understand. The example sentence must be grammatically correct and demonstrate the word’s precise meaning and part of speech, and should **strictly use the original word** as it is.
    - **Example Usage**: The example sentence should be grammatically correct and demonstrate the word’s precise meaning and part of speech. It must **strictly** use the word in question, not a synonym or related term. For example, if the word is "abeam," the example sentence should use "abeam" and reflect its correct definition (positioned at right angles to the ship’s course) and not any variation or misinterpretation.
    - **Etymology**: Provide accurate historical details, including the language of origin, evolution, and any notable shifts in meaning. Ensure that etymological details are relevant to the word provided.
    - **Tone**: Maintain a formal, educational tone, appropriate for a dictionary or language-learning resource.

    ### Example:

    **Input:**  
    "id: 10, word: abbess, part_of_speech: nan, definition: nan, example_usage: nan, etymology: nan"

    **Output:**  
    "\"id\": \"10\", \"word\": \"abbess\", \"part_of_speech\": \"noun\", \"definition\": \"A woman who is the head of an abbey of nuns.\", \"example_usage\": \"The abbess greeted the visitors with warmth and grace.\", \"etymology\": \"From Late Latin 'abbatissa', feminine form of 'abbas' (abbot).\""
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_template),
            ("human", "Here's a row of data with missing values: {row_data}"),
        ]
    )
    chain = prompt | llm

    for index, row in rows_to_process.iterrows():
        # Check if **all** the required fields (part_of_speech, definition, example_usage, etymology) are already filled (non-NaN, non-empty, or non-"Na")
        if row[['part_of_speech', 'definition', 'example_usage', 'etymology']].notna().all() and (row[['part_of_speech', 'definition', 'example_usage', 'etymology']] != "").all() and not (row[['part_of_speech', 'definition', 'example_usage', 'etymology']] == "Na").any():
            # Skip rows where all these columns have valid (non-NaN, non-empty, non-"Na") values
            print(f"Skipping row ID={row['id']} (Word: '{row['word']}') as it has all values filled.")
            filled_rows_list.append(row.to_dict())
            continue

        # Update the status to display ID, word, and pending rows
        current_progress = f"Processing: ID={row['id']}, Word='{row['word']}' | Pending: {pending_rows}/{total_rows}"
        status.update(label=current_progress)
        print(current_progress)

        row_data = {
            "id": str(row["id"]),
            "word": row["word"],
            "part_of_speech": "nan",
            "definition": "nan",
            "example_usage": "nan",
            "etymology": "nan",
        }

        def process_row():
            """
            Process a single row using the LLM chain.
            """
            response = chain.invoke({"row_data": json.dumps(row_data)}).content
            print(response)
            try:
                if isinstance(response, str):
                    response = json.loads(response)  # Parse the JSON response
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response: {response}") from e
            
            # Check if any required field is missing and retry if needed
            missing_fields = [key for key in ["part_of_speech", "definition", "example_usage", "etymology"] if not response.get(key)]
            if missing_fields:
                raise ValueError(f"Missing fields: {', '.join(missing_fields)}")
            
            return {
                "id": response.get("id", ""),
                "word": response.get("word", ""),
                "part_of_speech": response.get("part_of_speech", ""),
                "definition": response.get("definition", ""),
                "example_usage": response.get("example_usage", ""),
                "etymology": response.get("etymology", ""),
            }

        # Call process_row with retries
        filled_row = retry_until_success(process_row)
        filled_rows_list.append(filled_row)

        # Save progress after every 100 rows
        if (len(filled_rows_list) % 10) == 0:
            temp_df = pd.DataFrame(filled_rows_list)
            save_temp_excel(temp_df)
            filled_rows_list.clear()  # Clear the batch to save memory

        pending_rows -= 1  # Update the count of pending rows

    # Save remaining rows
    if filled_rows_list:
        temp_df = pd.DataFrame(filled_rows_list)
        save_temp_excel(temp_df)

def process_file_ollama(file, status):
    """
    Processes an Excel file row by row and fills missing values using the LLM.
    """
    doc = pd.read_excel(file)
    fill_missing_values_for_row(doc, llm, status)

    # Save the final processed document
    final_data = load_existing_data()
    final_data.to_excel("processed_final.xlsx", index=False)
    print("Final file saved as 'processed_final.xlsx'")
    return final_data
