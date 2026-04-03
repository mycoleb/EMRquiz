#py -3.12 -m streamlit run app.py
import fitz  # PyMuPDF
import random
import json
import os

def extract_and_save_data(pdf_path, json_path):
    print("--- First time setup: Extracting data from PDF Thank you for using Mycole's Github ---")
    doc = fitz.open(pdf_path)
    quiz_items = []

    # skip first 30 pages
    for page_num in range(30, len(doc) - 20):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        full_text = page.get_text()
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = "".join([s["text"] for s in line["spans"]])
                    
                    for span in line["spans"]:
                        if "Bold" in span["font"]:
                            term = span["text"].strip()
                            
                            # UPDATED FILTERING LOGIC:
                            # 1.
                            # 2. Ignore short words, URLs, or metadata
                            excluded_phrases = ["THINK ABOUT IT", "Page", "http"]
                            if len(term) < 4 or any(phrase in term for phrase in excluded_phrases):
                                continue

                            # Find the term in the full page text to get better context
                            start_idx = full_text.find(line_text)
                            
                            # EXPANDED CONTEXT: Grab ~200 characters before and after for better readability
                            context_start = max(0, start_idx - 200)
                            context_end = min(len(full_text), start_idx + len(line_text) + 200)
                            surrounding_context = full_text[context_start:context_end].replace('\n', ' ')
                            
                            if term in surrounding_context:
                                question = surrounding_context.replace(term, "__________", 1)
                                quiz_items.append({"answer": term, "question": question})
                                
    with open(json_path, 'w') as f:
        json.dump(quiz_items, f)
    return quiz_items

def start_game(pdf_path):
    json_path = "quiz_data.json"
    
    # SPEED BOOST!!!: Load from JSON if it exists, otherwise read PDF
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
    else:
        data = extract_and_save_data(pdf_path, json_path)
    
    if not data:
        print("No quiz questions found.")
        return

    random.shuffle(data)
    score = 0
    total = 5

    # Get a list of all possible answers to use as decoys for Multiple Choice
    all_answers = list(set([item['answer'] for item in data]))

    for i in range(total):
        item = data[i]
        correct = item['answer']
        
        # Create Multiple Choice Options
        decoys = random.sample([a for a in all_answers if a.lower() != correct.lower()], 3)
        options = decoys + [correct]
        random.shuffle(options)
        
        print(f"\nQuestion {i+1}:")
        print(f"Context: ...{item['question']}...")
        
        mapping = {}
        for idx, label in enumerate(['A', 'B', 'C', 'D']):
            print(f"  {label}) {options[idx]}")
            mapping[label] = options[idx]
        
        choice = input("\nYour answer (A, B, C, or D): ").strip().upper()
        selected = mapping.get(choice)

        if selected == correct:
            print("✅ Correct!")
            score += 1
        else:
            print(f"❌ Not quite. The answer was: {correct}")

    print(f"\nGame Over! Your score: {score}/{total}")

if __name__ == "__main__":
    # Thanks for using Mycole's Github make sure this matches your filename exactly
    start_game("workbook.pdf")