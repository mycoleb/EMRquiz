import fitz  # PyMuPDF

def get_bold_words(pdf_path):
    doc = fitz.open(pdf_path)
    quiz_data = []

    for page in doc:
        # 'dict' format includes font style information
        text_instances = page.get_text("dict")
        for block in text_instances["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Check if 'Bold' is in the font name metadata
                        if "Bold" in span["font"]:
                            bold_word = span["text"].strip()
                            
                            # Clean up: ignore empty strings or very short characters
                            if len(bold_word) > 2:
                                quiz_data.append(bold_word)
    return quiz_data

# --
# 1. Define the filename (make sure this matches your file in the folder)
filename = "workbook.pdf" 

# 2. Call the function and store the results
results = get_bold_words(filename)

# 3. Print the results 
print(f"Found {len(results)} bolded words:")
for word in results[:10]: # Just showing the first 10 for now
    print(f"- {word}")