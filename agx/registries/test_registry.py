"""
test_registry.py

This is a test registry for use in development.
Make sure the dictionary stays updated!
"""

registry = {
    "log_message": log_message,
    "add_numbers": add_numbers,
    "div_numbers": div_numbers,
    "fetch_webpage": fetch_webpage,
    "summarize_text": summarize_text,
    "load_pdf": load_pdf,
    "extract_field": extract_field,
    "update_sheet": update_sheet,
}

def log_message(message, memory=None, final_messages=None):
    # Replace {var} with its value from memory, if available
    if isinstance(message, str):
        try:
            message = message.format(**memory)
        except KeyError as e:
            print(f"[AGX WARN] Variable '{e.args[0]}' not found in memory.")

    if final_messages is not None:
        final_messages.append(message)

    print(f"[AGX LOG] {message}")
    return None

def add_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError(f"add_numbers expected integers, got a={a} ({type(a)}), b={b} ({type(b)})")
    return a + b

def div_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError(f"div_numbers expected integers, got a={a} ({type(a)}), b={b} ({type(b)})")
    return a / b

def fetch_webpage(url):
    from langchain.document_loaders import WebBaseLoader
    loader = WebBaseLoader(url)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])

def summarize_text(text: str) -> str:
    from langchain_community.llms import OpenAI
    from langchain.chains.summarize import load_summarize_chain
    from langchain.docstore.document import Document

    # Wrap input into a LangChain Document
    docs = [Document(page_content=text)]

    # Load summarization chain
    llm = OpenAI(temperature=0)
    chain = load_summarize_chain(llm, chain_type="stuff")

    # Run the chain
    result = chain.run(docs)

    return result

def load_pdf(path: str) -> str:
    from langchain_community.document_loaders import PyMuPDFLoader

    loader = PyMuPDFLoader(path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])

def extract_field(text: str, field: str) -> str:
    # Naive implementation – can upgrade later with regex or rule templates
    import re

    patterns = {
        "Vat Number": r"VAT\s*Number[:\s]*([A-Z0-9\-]+)",
        "Company Name": r"Company\s*Name[:\s]*([^\n]+)"
    }

    pattern = patterns.get(field.title())
    if not pattern:
        raise ValueError(f"Unknown field: {field}")

    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "NOT_FOUND"

def update_sheet(data: dict):
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    try:
        print(f"[DEBUG] update_sheet received data: {data}")

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # Try to open and write to sheet
        sheet = client.open_by_key('1KTF1TOPL_vPmppiph5_C9NTzEd1shFAPH9CYjBTd2_E').sheet1

        # Normalize flexible key names
        name = data.get("Company Name") or data.get("company_name") or "UNKNOWN"
        vat = data.get("VAT Number") or data.get("vat_number") or "UNKNOWN"

        print(f"[DEBUG] Writing row: {name}, {vat}")
        sheet.append_row([name, vat])

    except Exception as e:
        import traceback
        print(f"[AGX ERROR] update_sheet failed: {e}")
        traceback.print_exc()
        raise
