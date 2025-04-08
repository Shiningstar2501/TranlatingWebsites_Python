import os
import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Comment
from deep_translator import GoogleTranslator
from bs4 import NavigableString
import sys
import pandas as pd
import time
#-------------------------------------------------------------------------------------------------------------------#
# Ensure error.txt exists
if not os.path.exists("error.txt"):
    with open("error.txt", "w", encoding="utf-8") as error_file:
        error_file.write("Error log started.\n")
#-------------------------------------------------------------------------------------------------------------------#
# Function to process the data of a row
def process_row(website_url, class_name, php_template, domain, language):
    # Example of processing logic
    print(f"Processing data for {website_url}:")
    print(f"Class: {class_name}")
    print(f"PHP Template: {php_template}")
    print(f"Domain: {domain}")
    print(f"Language: {language}")
    # Add any other processing logic here...
#-------------------------------------------------------------------------------------------------------------------#
def fetch_and_process_data(file_path):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file_path)

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Fetch data from the row
        website_url = row['Website URL']
        class_name = row['Class']
        php_template = row['PHP Template']
        domain = row['Domain']
        language = row['Language']

        try:
            # Process the data for the current row
            process_all_page(website_url, language, php_template, class_name, domain)
        except Exception as e:
            # Log the error into the error.txt file
            with open("error.txt", "a", encoding="utf-8") as error_file:
                error_message = f"Error occurred while processing row {index + 1} (Website: {website_url}): {str(e)}\n"
                error_file.write(error_message)
            print(f"[ERROR] Error occurred while processing row {index + 1} (Website: {website_url}). Error logged to error.txt.")
#-------------------------------------------------------------------------------------------------------------------#
def is_visible(element):
    """Checks if the text node is visible on the webpage."""
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True
#-------------------------------------------------------------------------------------------------------------------#
def fetch_main_content(url, css_class):
    """Fetches the HTML content from a URL and extracts the largest 'container' div."""
    print(f"[DEBUG] Fetching content from {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Could not fetch {url}: {e}")
        return None, None, None, None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract Title, Meta Description, and First Heading
    title_tag = soup.find("title")
    title = title_tag.string.strip() if title_tag else "[No Title Found]"
    print("[DEBUG] Extracted Title:", title)

    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_tag["content"].strip() if meta_tag else "[No Meta Description Found]"

    h1_tag = soup.find("h1")
    first_heading = h1_tag.get_text(strip=True) if h1_tag else "[No H1 Found]"

    
    # Remove unwanted elements
    for tag in ["nav", "footer", "header", "aside", "script", "style", "form"]:
        for element in soup.find_all(tag):
            element.decompose()

    # Extract the largest 'container' div
    container_divs = [div for div in soup.find_all("div", class_=css_class)]
    if not container_divs:
        print("[WARNING] No '.container' div found.")
        return title, meta_desc, first_heading, "[WARNING] No 'container' div found.", None
    
    # Choose the largest container div
    main_content_div = max(container_divs, key=lambda div: len(div.get_text(strip=True)), default=None)
    raw_html_content = str(main_content_div)  # Preserve full structure for later

    # return title, meta_desc, first_heading, raw_html_content, soup  # Returning full soup for editing
    return title, meta_desc, first_heading, raw_html_content
#-------------------------------------------------------------------------------------------------------------------#
def safe_translate(text,translator):
        print("DEBUGGING : TRANSLATING THE SAFE TEXT (ONLY THE TEXT THAT WILL BE VIISBLE ON THE WEBSITE)")
        if not text:
            return ""
        try:
            translated_text = translator.translate(text)
            print(f"[DEBUG] Translated '{text[:500]}...' → '{translated_text[:500]}...'") # here if this line is marked as comment the code shows the error because in some places there can be the none string so if the print statement get that none string then it will not continue with that part and leave it and continue. this prevent the flowing the none into the other function or returning none to other part of the code and then only hte specific things (that are required) will be printed ofcourse, hence the error is saved.
            return translated_text
        except Exception as e:
            print(f"[ERROR] Error translating '{text[:200]}...': {e}")
            return text  # Return original if translation fails

#-------------------------------------------------------------------------------------------------------------------#
# def translate_p_tag(p_tag,translator):
#     # """Translates text inside a <p> tag while preserving spaces and adding space before <tags>."""
    
#         original_html = str(p_tag)  # Convert the <p> tag to a string to manipulate its content
#         print("===================================Original P Tag=======================================")
#         # print(original_html)
#         print(original_html)
       
#         tag_pattern = re.compile(r'(<[^>]+>)')  # Regex to match HTML tags
#         # Step 1: Extract text segments and tags
#         segments = tag_pattern.split(original_html)  # This separates words and tags
#         translated_segments = []
#         print("TRANSLATED SEGMENT : ",translated_segments)

#         segments = [' ' if segment == '' else segment for segment in segments]     
#         print("UPDATED SEGMENT: ",segments)
#         for i, segment in enumerate(segments):
#             if isinstance(segment, str):
#                 if tag_pattern.match(segment):  # If it's an HTML tag, process it
#                     if segment in ['<p>', '</p>', '<li>', '</li>']:
#                         translated_segments.append(segment)  # Keep the tag as is without adding spaces inside it
#                     else:
#                         # For other tags, add a space before
#                         translated_segments.append(" " + segment)
#                 else:  # Otherwise, translate the text
#                     words = segment.split()  # Split text into words to preserve spaces
#                     # translated_text = " ".join([safe_translate(word,translator) for word in words])
#                     translated_segments.append(translated_text)
#                     translated_segments.append(translated_text)  # Reconstruct text

#         # Step 2: Reconstruct the <p> tag with the translated content and original structure
#         new_content = " ".join(translated_segments).replace("  ", " ")  # Remove any double spaces
#         p_tag.clear()  # Remove existing content
#         p_tag.append(BeautifulSoup(new_content, "html.parser"))  # Insert corrected content
#------------------------------------------------------------------------------------------------------------------#
def translate_p_tag(p_tag, translator, translated_texts=None):
    """Translates text inside a <p> tag, but skips translation if it's already translated."""

    # Convert the <p> tag to a string to manipulate its content
    original_html = str(p_tag)
    print("===================================Original P Tag=======================================")
    print(original_html)

    # Initialize the dictionary if not passed
    if translated_texts is None:
        translated_texts = {}

    tag_pattern = re.compile(r'(<[^>]+>)')  # Regex to match HTML tags
    segments = tag_pattern.split(original_html)  # This separates words and tags
    translated_segments = []

    # Process each segment in the tag
    for segment in segments:
        if isinstance(segment, str):
            if tag_pattern.match(segment):  # If it's an HTML tag, leave it unchanged
                translated_segments.append(segment)
            else:  # Otherwise, process the text
                # Check if the segment has already been translated
                if segment.strip() in translated_texts:
                    translated_segments.append(translated_texts[segment.strip()])  # Use already translated text
                    print(f"[INFO] Using cached translation for: {segment[:50]}...")
                else:
                    # If not, translate and store it
                    translated_text = safe_translate(segment, translator)
                    translated_segments.append(translated_text)
                    translated_texts[segment.strip()] = translated_text  # Store in cache for future

    # Reconstruct the <p> tag with the translated content and original structure
    new_content = " ".join(translated_segments).replace("  ", " ")  # Remove any double spaces
    p_tag.clear()  # Remove existing content
    p_tag.append(BeautifulSoup(new_content, "html.parser"))  # Insert translated content    
#------------------------------------------------------------------------------------------------------------------#
def clean_nested_li_tags(tag): ### where to put this function is left...............
        original_html = str(tag)
        
        # Detect if there are nested <li> tags
        if '<p> <p>' in original_html and '</p> </p>' in original_html:
            original_html = original_html.replace('<p> <p>', '<p>').replace('</p> </p>','</p>')
        if '<li> <li>' in original_html and '</li> </li>' in original_html:
            # Remove the outer <li> if nested
            original_html = original_html.replace('<li> <li>', '<li>').replace('</li> </li>', '</li>')

        return original_html      

# --- Save Translated Content into PHP Format ---
#-------------------------------------------------------------------------------------------------------------------#
def save_translated_page(translated_title, translated_meta, translated_heading, translated_main_content, output_filename,lang_code, page_template, file_name):
    """Saves translated content into a PHP file."""

    translated_content = page_template.replace("{meta_title}", translated_title)
    translated_content = translated_content.replace ("{file_name}", file_name)
    translated_content = translated_content.replace("{lang_code}", lang_code) 
    translated_content = translated_content.replace("{meta_desc}", translated_meta)
    translated_content = translated_content.replace("{meta_heading}", translated_heading)
    translated_content = translated_content.replace("{main_content}", str(translated_main_content))

    output_dir = "translated_pages"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_content)

    
    print(f"[DEBUG] Translated file saved: {output_path}")
    print("========================================================================================================================================================================")
# --- Translation ---
#-------------------------------------------------------------------------------------------------------------------#
# --- Translate Container Content --
def translate_container_content(container_html, translator, domain,css_class):
    """Translates only the text inside the extracted '.container' div while keeping the structure."""
    print("[DEBUG] Translating content inside the largest .container div.")

    soup = BeautifulSoup(container_html, "html.parser")  # Convert container HTML into a BeautifulSoup object
    # print("SOUP: ",soup)
   
    #-------------------------------------------------------------------------------------------------------------------#
    #------------------------------------------------HERE THE LINK PRESENT IN THE ANCHOR TAG, IMAGE TAG OR THE SOURCE TAG STARTS WITH "WEBSITE_URL" WILL BE RELACED WITH "<?=$site_url?>" TO FETCH IT FROM OUTSIDE--------------------------------------
            # Extract the links 
    extracted_links = {
        "anchor_links":[],
        "image_links":[],
        "source_links":[]
    }   
    print ("Anchor links")
    for a_tag in soup.find_all("a", href= True):
        extracted_links["anchor_links"].append(a_tag["href"])
        # print("Anchor Link: ",a_tag["href"])
        if a_tag.has_attr("href") and a_tag["href"].startswith("https://"):
            a_tag["href"] = a_tag["href"].replace(domain, "<?=$site_url?>", 1)  # Replace only the first occurrence
            # print ("Replaced: ",a_tag["href"])

    print("Image Links")
    for i_tag in soup.find_all("img", src= True):
        extracted_links["image_links"].append(i_tag["src"])
        # print("Image Link:", i_tag["src"])
        if i_tag.has_attr("src") and i_tag["src"].startswith("https://"):
            i_tag["src"] = i_tag["src"].replace(domain, "<?=$site_url?>", 1)  # Replace only the first occurrence
            # print ("Replaced: ",i_tag["src"])

    print("Source Links")
    for s_tag in soup.find_all("img", src= True):
        extracted_links["source_links"].append(s_tag["src"])
        # print("Source Link:",s_tag)
        # print("Source Link (srcset):",s_tag["srcset"])
        if s_tag.has_attr("src") and s_tag["src"].startswith("https://"):
            s_tag["src"] = s_tag["src"].replace(domain, "<?=$site_url?>", 1)  # Replace only the first occurrence
            # print ("Replaced: ",s_tag["src"])
        if s_tag.has_attr("srcset") and s_tag["srcset"].startswith("https://"):
            s_tag["srcset"] = s_tag["srcset"].replace(domain, "<?=$site_url?>",1)


    for img_tag in soup.find_all("img"):
    # Translate `alt` attribute if present
        if img_tag.has_attr("alt") and img_tag["alt"].strip():
            original_alt = img_tag["alt"]
            translated_alt = safe_translate(original_alt,translator)
            img_tag["alt"] = translated_alt
            print(f"[DEBUG] Translated `alt`: '{original_alt}' → '{translated_alt}'")

    # Translate `title` attribute if present
        if img_tag.has_attr("title") and img_tag["title"].strip():
            original_title = img_tag["title"]
            translated_title = safe_translate(original_title,translator)
            img_tag["title"] = translated_title
            print(f"[DEBUG] Translated `title`: '{original_title}' → '{translated_title}'")
    

    # Translate other visible text
    for text_node in soup.find_all(string=True):
        if is_visible(text_node):
            original_text = text_node.strip()
            if original_text:
                translated_text = safe_translate(original_text,translator)
                if translated_text:  # Ensure it's not None
                    text_node.replace_with(NavigableString(translated_text))

    container_divs = soup.find_all("div", class_=css_class)
    if not container_divs:
        print("[WARNING] No '.container' div found for translation.")
        return soup

    largest_container = max(container_divs, key=lambda div: len(div.get_text(strip=True)), default=None)
    if not largest_container:
        print("[WARNING] No valid '.container' div found for translation.")
        return soup

    # Translate all <p> tag content inside this div
    for tag in largest_container.find_all(["p","li"]):
        translate_p_tag(tag,translator)
    print("[DEBUG] Finished translating .container div content.")
    return clean_nested_li_tags((soup.decode(formatter=None)))  # Convert back to string format  # Convert back to string format
#-------------------------------------------------------------------------------------------------------------------#
def process_all_page(website_url, dest_language, php_template, css_class, domain):
    start_time = time.time()
    """Processes a single page by fetching content, translating it, and saving it in PHP format."""
    try:
        print("Debugged 2 , THE PROCESSING IS STARTED")
        extracted_title, extracted_meta, extracted_heading, raw_html_content = fetch_main_content(website_url, css_class)
        if not raw_html_content:
            print("[ERROR] No content found for translation.")
            return

        translator = GoogleTranslator(source='auto', target=dest_language)

        # Translate title and meta description
        translated_title = translator.translate(extracted_title)
        translated_heading = translator.translate(extracted_heading)
        translated_meta = translator.translate(extracted_meta)

        # Translate the extracted container div
        translated_main_content = translate_container_content(raw_html_content, translator, domain, css_class)

        file_name = f"{dest_language}_{urlparse(website_url).path.strip('/').replace('/', '_')}.php"
        file_name2 = f"{urlparse(website_url).path.strip('/').replace('/', '_')}"

        save_translated_page(translated_title, translated_meta, translated_heading, translated_main_content, file_name, dest_language, php_template, file_name2)

        end_time = time.time()  # Record end time

        # Calculate the total time taken and print
        total_time = end_time - start_time
        print(total_time)

    except Exception as e:
        # Log the error into the error.txt file
        with open(r"C:\Users\Intel\Desktop\ANUSHKA\Python Projects\Translation\Full Websites\Multiple_url\error.txt", "a", encoding="utf-8") as error_file:
            error_message = f"Error occurred while processing {website_url}: {str(e)}\n"
            error_file.write(error_message)
        print(f"[ERROR] Error occurred while processing {website_url}. Error logged to error.txt.")
#-------------------------------------------------------------------------------------------------------------------#   
if __name__ == "__main__":
    # Specify the path to your Excel file
    file_path = "tril.xlsx"  # Update this with your Excel file's path

    # Call the function to fetch and process data
    fetch_and_process_data(file_path)