import json
import PyPDF2
import re
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def get_unique_words_from_text(text):
    """Extract unique words from text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and split into words
    # Keep words with apostrophes (like don't, couldn't) and hyphens
    words = re.findall(r'\b[a-z\'-]+\b', text)
    
    # Get unique words
    unique_words = set(words)
    
    return unique_words

def filter_lemma_dict(lemma_dict_path, constitution_words):
    """Filter lemma dictionary to keep only words present in constitution"""
    try:
        with open(lemma_dict_path, 'r', encoding='utf-8') as file:
            lemma_dict = json.load(file)
        
        filtered_dict = {}
        
        for word, lemma in lemma_dict.items():
            # Check if the word or its lemma form is in constitution words
            if word.lower() in constitution_words or lemma.lower() in constitution_words:
                filtered_dict[word] = lemma
        
        return filtered_dict
        
    except Exception as e:
        print(f"Error reading lemma dictionary: {e}")
        return {}

def save_filtered_dict(filtered_dict, output_path):
    """Save filtered dictionary to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(filtered_dict, file, indent=2, ensure_ascii=False)
        print(f"Successfully saved filtered dictionary to {output_path}")
        print(f"Original dictionary size: {len(filtered_dict) if 'filtered_dict' in locals() else 'Unknown'}")
    except Exception as e:
        print(f"Error saving filtered dictionary: {e}")

def main():
    # File paths
    constitution_pdf = "data/Constitution-of-Nepal_2072.pdf"
    lemma_dict_file = "data/lemma_dict_v1.json"
    output_file = "data/lemma_dict_v2.json"
    
    # Check if files exist
    if not Path(constitution_pdf).exists():
        print(f"Error: {constitution_pdf} not found!")
        return
    
    if not Path(lemma_dict_file).exists():
        print(f"Error: {lemma_dict_file} not found!")
        return
    
    print("Extracting text from constitution PDF...")
    constitution_text = extract_text_from_pdf(constitution_pdf)
    
    if not constitution_text:
        print("Failed to extract text from PDF!")
        return
    
    print("Extracting unique words from constitution...")
    constitution_words = get_unique_words_from_text(constitution_text)
    print(f"Found {len(constitution_words)} unique words in constitution")
    
    print("Filtering lemma dictionary...")
    filtered_dict = filter_lemma_dict(lemma_dict_file, constitution_words)
    
    if filtered_dict:
        print(f"Filtered dictionary contains {len(filtered_dict)} entries")
        save_filtered_dict(filtered_dict, output_file)
        
        # Print some statistics
        original_size = 0
        try:
            with open(lemma_dict_file, 'r', encoding='utf-8') as f:
                original_dict = json.load(f)
                original_size = len(original_dict)
                print(f"\nStatistics:")
                print(f"Original entries: {original_size}")
                print(f"Filtered entries: {len(filtered_dict)}")
                print(f"Removed entries: {original_size - len(filtered_dict)}")
                print(f"Retention rate: {(len(filtered_dict)/original_size)*100:.2f}%")
        except:
            pass
    else:
        print("No matching words found in lemma dictionary!")

if __name__ == "__main__":
    main()