import streamlit as st
import fitz  # PyMuPDF
import random
import json
import os



st.set_page_config(page_title="EMR Quiz Suite", page_icon="🚑")

#  Combined Extraction Logic ---
def extract_quiz_data(pdf_path, mode="Full"):
    doc = fitz.open(pdf_path)
    quiz_items = []
    
    # Define ranges based on mode
    if mode == "Entrance Prep":
        target_ranges = [(131, 160), (161, 169), (249, 300), (441, 615)]
    else:
        # Default: All pages from 30 to near end
        target_ranges = [(30, len(doc) - 20)]

    for start, end in target_ranges:
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
                                # Filtering
                                excluded = ["THINK ABOUT IT", "PAGE", "HTTP"]
                                if len(term) < 4 or any(x in term.upper() for x in excluded):
                                    continue
                                if mode == "Entrance Prep" and term.isupper():
                                    continue
                                
                                start_idx = full_text.find(line_text)
                                context_start = max(0, start_idx - 250)
                                context_end = min(len(full_text), start_idx + len(line_text) + 250)
                                surrounding = full_text[context_start:context_end].replace('\n', ' ')
                                
                                if term in surrounding:
                                    # Replace only the first instance to create the blank
                                    question = surrounding.replace(term, "____", 1)
                                    quiz_items.append({"answer": term, "question": question})
    return quiz_items

# - Sidebar Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose Quiz Type:", ["Full Workbook", "Entrance Prep"])

# - Logic to handle different datasets ---
data_key = "entrance_data" if app_mode == "Entrance Prep" else "full_data"
file_cache = "entrance_prep_data.json" if app_mode == "Entrance Prep" else "quiz_data.json"

if data_key not in st.session_state:
    if os.path.exists(file_cache):
        with open(file_cache, "r") as f:
            st.session_state[data_key] = json.load(f)
    else:
        with st.spinner(f"Extracting {app_mode} terms..."):
            data = extract_quiz_data("workbook.pdf", mode=app_mode)
            st.session_state[data_key] = data
            with open(file_cache, "w") as f:
                json.dump(data, f)

#  Shared Quiz UI Logic ---
st.title(f"🚑 {app_mode} Quiz")
quiz_pool = st.session_state[data_key]

# Clear question if mode changes
if 'last_mode' in st.session_state and st.session_state.last_mode != app_mode:
    if 'current_q' in st.session_state:
        del st.session_state.current_q
st.session_state.last_mode = app_mode

if 'current_q' not in st.session_state:
    st.session_state.current_q = random.choice(quiz_pool)
    all_ans = list(set([i['answer'] for i in quiz_pool]))
    decoys = random.sample([a for a in all_ans if a != st.session_state.current_q['answer']], 3)
    options = decoys + [st.session_state.current_q['answer']]
    random.shuffle(options)
    st.session_state.options = options
    st.session_state.answered = False

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
        del st.session_state.current_q
        st.rerun()
# Set the configuration
st.set_page_config(page_title="EMR Study Quiz", page_icon="🚑")

def extract_table_quiz_data(pdf_path):
    doc = fitz.open(pdf_path)
    table_items = []
    
    # Iterate through pages likely to have medical tables
    for page in doc:
        tabs = page.find_tables()
        for tab in tabs:
            df = tab.to_pandas()
            # Clean up empty rows/cols
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty or df.size < 4:
                continue

            # Pick a random cell that isn't empty and isn't a header
            row_idx = random.randint(0, len(df) - 1)
            col_idx = random.randint(0, len(df.columns) - 1)
            correct_answer = str(df.iloc[row_idx, col_idx]).strip()

            if len(correct_answer) < 3:
                continue

            # Create a "Blanked" version of the table for display
            df_blanked = df.copy()
            df_blanked.iloc[row_idx, col_idx] = "____[MISSING]____"
            
            # Store the question as a HTML table for Streamlit to render
            table_html = df_blanked.to_html(index=False, classes='table table-striped')
            table_items.append({
                "answer": correct_answer,
                "question": table_html,
                "is_table": True
            })
    return table_items
def extract_data(pdf_path):
    doc = fitz.open(pdf_path)
    quiz_items = []
    # skipping first 30 pages
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
                            context_start = max(0, start_idx - 300)
                            context_end = min(len(full_text), start_idx + len(line_text) + 300)
                            surrounding = full_text[context_start:context_end].replace('\n', ' ')
                            
                            if term in surrounding:
                                question = surrounding.replace(term, "____", 1)
                                quiz_items.append({"answer": term, "question": question})
    return quiz_items

# -- App Logic ---
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