import streamlit as st
import fitz  # PyMuPDF
import random
import json
import os

# Set the configuration
st.set_page_config(page_title="EMR Study Quiz", page_icon="🚑")

def extract_data(pdf_path):
    doc = fitz.open(pdf_path)
    quiz_items = []
    # Using your preference: skipping first 30 pages
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
                            excluded = ["THINK ABOUT IT", "PAGE", "HTTP"]
                            if len(term) < 4 or any(x in term.upper() for x in excluded):
                                continue
                            
                            start_idx = full_text.find(line_text)
                            context_start = max(0, start_idx - 250)
                            context_end = min(len(full_text), start_idx + len(line_text) + 250)
                            surrounding = full_text[context_start:context_end].replace('\n', ' ')
                            
                            if term in surrounding:
                                question = surrounding.replace(term, "____", 1)
                                quiz_items.append({"answer": term, "question": question})
    return quiz_items

# --- App Logic ---
st.title("🚑 EMR Workbook Quiz")
st.write("Test your knowledge based on the bolded terms in your manual.")

# Load Data
if 'quiz_data' not in st.session_state:
    if os.path.exists("quiz_data.json"):
        with open("quiz_data.json", "r") as f:
            st.session_state.quiz_data = json.load(f)
    else:
        with st.spinner("Extracting terms from PDF..."):
            data = extract_data("workbook.pdf")
            st.session_state.quiz_data = data
            with open("quiz_data.json", "w") as f:
                json.dump(data, f)

# Initialize Game State
if 'current_q' not in st.session_state:
    st.session_state.current_q = random.choice(st.session_state.quiz_data)
    # Generate multiple choice options
    all_ans = [i['answer'] for i in st.session_state.quiz_data]
    decoys = random.sample([a for a in all_ans if a != st.session_state.current_q['answer']], 3)
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