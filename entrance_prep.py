import streamlit as st
import fitz  # PyMuPDF
import random
import json
import os

# Set the configuration
st.set_page_config(page_title="Entrance Exam Prep", page_icon="🚑")

def extract_data(pdf_path):
    doc = fitz.open(pdf_path)
    quiz_items = []
    
    # Define the page ranges for Chapters 6, 7, 12, and 26-34
    # Fitz uses 0-based indexing. Adding a small buffer for end pages.
    target_ranges = [
        (131, 160),  # Ch 6
        (161, 169),  # Ch 7
        (249, 300),  # Ch 12
        (441, 615)   # Ch 26-34
    ]
    if term in surrounding:
        # The '1' tells Python to only replace the first occurrence
        question = surrounding.replace(term, "____", 1) 
    quiz_items.append({"answer": term, "question": question})
    for start, end in target_ranges:
        # Ensure we don't exceed PDF length
        actual_end = min(end, len(doc))
        for page_num in range(start, actual_end):
            page = doc[page_num]
            full_text = page.get_text()
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = "".join([s["text"] for s in line["spans"]])
                        for span in line["spans"]:
                            if "Bold" in span["font"]:
                                term = span["text"].strip()
                                # Filtering out noise
                                if len(term) < 4 or term.isupper():
                                    continue
                                
                                start_idx = full_text.find(line_text)
                                context_start = max(0, start_idx - 250)
                                context_end = min(len(full_text), start_idx + len(line_text) + 250)
                                surrounding = full_text[context_start:context_end].replace('\n', ' ')
                                
                                if term in surrounding:
                                    question = surrounding.replace(term, "____")
                                    quiz_items.append({"answer": term, "question": question})
    return quiz_items

# --- App Logic ---
st.title("🚑 Entrance Exam Prep Quiz")
st.subheader("Targeting Chapters 6, 7, 12, and 26-34")

# Load Data (Specific to this version)
if 'entrance_data' not in st.session_state:
    if os.path.exists("entrance_prep_data.json"):
        with open("entrance_prep_data.json", "r") as f:
            st.session_state.entrance_data = json.load(f)
    else:
        if os.path.exists("workbook.pdf"):
            with st.spinner("Analyzing Exam Chapters..."):
                data = extract_data("workbook.pdf")
                if not data:
                    st.error("Extraction finished, but NO bolded terms were found in those page ranges!")
                    st.stop()
                st.session_state.entrance_data = data
                with open("entrance_prep_data.json", "w") as f:
                    json.dump(data, f)
        else:
            st.error("CRITICAL: 'workbook.pdf' not found in the current folder.")
            st.stop()

# Initialize Game State (Standard Streamlit Quiz Logic)
if 'current_q' not in st.session_state:
    st.session_state.current_q = random.choice(st.session_state.entrance_data)
    all_ans = [i['answer'] for i in st.session_state.entrance_data]
    decoys = random.sample([a for a in list(set(all_ans)) if a != st.session_state.current_q['answer']], 3)
    options = decoys + [st.session_state.current_q['answer']]
    random.shuffle(options)
    st.session_state.options = options
    st.session_state.answered = False
# --- UI Display ---
q = st.session_state.current_q
st.info(f"**Context:** ...{q['question']}...")

with st.form("quiz_form"):
    choice = st.radio("Select the correct bolded term:", st.session_state.options)
    submit = st.form_submit_button("Submit Answer")

if submit:
    st.session_state.answered = True
    if choice == q['answer']:
        st.success(f"Correct! The answer is **{q['answer']}**.")
    else:
        st.error(f"Not quite. The correct answer was **{q['answer']}**.")

if st.session_state.answered:
    if st.button("Next Question"):
        # Reset for a new question
        del st.session_state.current_q
        st.rerun()
