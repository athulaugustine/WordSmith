# WordSmith

**WordSmith** is an AI-powered tool designed to complete and enrich linguistic datasets by providing definitions, parts of speech, etymologies, and usage examples for words. With the power of large language models (LLMs) like **GPT** and **Ollama**, WordSmith ensures efficient and precise filling of missing data, making it an ideal tool for language researchers, lexicographers, and anyone working with linguistic data.

## Features

- **Fill Missing Word Information**: Automatically generate the missing linguistic details for a list of words, including:
  - **Part of Speech**: Noun, verb, adjective, etc.
  - **Definition**: A clear and concise explanation of the word's meaning.
  - **Example Usage**: An example sentence that demonstrates how the word is used in context.
  - **Etymology**: A historical account of the word's origin and evolution.
  
- **Two LLM Options**: Choose between two powerful language models:
  - **GPT**: Powered by OpenAI’s GPT model.
  - **Ollama**: Powered by Ollama, a versatile alternative for word processing.

- **Efficient Processing**: Process large datasets efficiently by handling multiple rows and providing real-time progress updates.

- **Download Processed Data**: Once the missing data is filled, you can download the enriched dataset in Excel format for further use.

## Ideal For

- **Language Researchers**: Quickly enrich and complete linguistic datasets.
- **Lexicographers**: Automatically generate detailed word entries for dictionaries.
- **Data Scientists**: Automate the process of enhancing word datasets for analysis.

## Technologies Used

- **Streamlit**: For building the web interface and interacting with users.
- **LangChain**: For integrating with LLMs (GPT or Ollama).
- **Pandas**: For reading, processing, and manipulating Excel files.
- **OpenAI GPT**: For generating language data via GPT-4.
- **Ollama**: For enriching word data through Ollama’s LLM.
  
## Installation

### Prerequisites

- Python 3.x
- Streamlit
- Pandas
- LangChain
- OpenAI or Ollama API keys

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/wordsmith.git
   cd wordsmith

2. **Create and activate a virtual environment (optional but recommended):**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. **Install required dependencies:**:
   ```bash
   pip install -r requirements.txt

4. **Set up environment variables:**:
   OPENAI_API_KEY=your_openai_api_key


Usage
Run the Streamlit app:
  ```bash
  streamlit run app.py


Open the app in your browser at http://localhost:8501.

Upload your Excel file containing words with missing fields.

Select the LLM you want to use (either GPT or Ollama).

Click "Process" to start filling in the missing data.

Once the process is complete, download the processed Excel file with the filled-in word information.

Code Overview
Main Components
Streamlit UI: The web interface that allows users to upload files, select LLM options, and download processed data.
LLM Processing:
process_file_gpt: Uses OpenAI GPT to process and fill missing word information.
process_file_ollama: Uses Ollama to process and fill missing word information.
Helper Functions:
retry_until_success: Retries processing steps in case of failure.
save_temp_excel: Saves processed data to a temporary file, ensuring progress is preserved.
File Handling
The application processes Excel files row by row, filling missing values for parts of speech, definitions, example usage, and etymology.
Processed data is saved incrementally, preventing data loss and enabling the application to resume if interrupted.
Notes
Ensure that you have a valid API key for either GPT or Ollama.
The application supports large datasets, processing the information efficiently and saving progress along the way.


