import os
import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Comment
from deep_translator import GoogleTranslator
from bs4 import NavigableString
import sys
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
        return None, None, None, None, None

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
    container_divs = [div for div in soup.find_all("div", class_="container")]
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
            print(f"[DEBUG] Translated '{text[:50]}...' → '{translated_text[:50]}...'") # here if this line is marked as comment the code shows the error because in some places there can be the none string so if the print statement get that none string then it will not continue with that part and leave it and continue. this prevent the flowing the none into the other function or returning none to other part of the code and then only hte specific things (that are required) will be printed ofcourse, hence the error is saved.
            return translated_text
        except Exception as e:
            print(f"[ERROR] Error translating '{text[:50]}...': {e}")
            return text  # Return original if translation fails

#-------------------------------------------------------------------------------------------------------------------#
def translate_p_tag(p_tag,translator):
    # """Translates text inside a <p> tag while preserving spaces and adding space before <tags>."""
    
        original_html = str(p_tag)  # Convert the <p> tag to a string to manipulate its content
        print("===================================Original P Tag=======================================")
        # print(original_html)
        print(original_html)
       
        tag_pattern = re.compile(r'(<[^>]+>)')  # Regex to match HTML tags
        # Step 1: Extract text segments and tags
        segments = tag_pattern.split(original_html)  # This separates words and tags
        translated_segments = []
        print("TRANSLATED SEGMENT : ",translated_segments)

        segments = [' ' if segment == '' else segment for segment in segments]     
        print("UPDATED SEGMENT: ",segments)
        for i, segment in enumerate(segments):
            if isinstance(segment, str):
                if tag_pattern.match(segment):  # If it's an HTML tag, process it
                    if segment in ['<p>', '</p>', '<li>', '</li>']:
                        translated_segments.append(segment)  # Keep the tag as is without adding spaces inside it
                    else:
                        # For other tags, add a space before
                        translated_segments.append(" " + segment)
                else:  # Otherwise, translate the text
                    words = segment.split()  # Split text into words to preserve spaces
                    translated_text = " ".join([safe_translate(word,translator) for word in words])
                    translated_segments.append(translated_text)  # Reconstruct text

        # Step 2: Reconstruct the <p> tag with the translated content and original structure
        new_content = " ".join(translated_segments).replace("  ", " ")  # Remove any double spaces
        p_tag.clear()  # Remove existing content
        p_tag.append(BeautifulSoup(new_content, "html.parser"))  # Insert corrected content
    
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
    translated_content = translated_content.replace("{main_content}", translated_main_content)

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
def translate_container_content(container_html, translator, css_class,domain):
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

    # # Translate other visible text
    # for text_node in soup.find_all(string=True):
    #     if is_visible(text_node):
    #         original_text = text_node.strip()
    #         if original_text:
    #             translated_text = safe_translate(original_text,translator)
    #             text_node.replace_with(translated_text)
    #TRANSLATE THE ALT AND THE TITLE OF THE 

    print("[DEBUG] Finished translating .container div content.")
    return clean_nested_li_tags(soup.decode(formatter=None))  # Convert back to string format  # Convert back to string format
#-------------------------------------------------------------------------------------------------------------------#
def process_all_page(website_url, dest_language, php_template, css_class, domain):
    """Processes a single page by fetching content, translating it, and saving it in PHP format."""
    print("Debugged 2 , THE PROCESSING IS STARTED")
    extracted_title, extracted_meta, extracted_heading, raw_html_content = fetch_main_content(website_url, css_class)
    if not raw_html_content:
        print("[ERROR] No content found for translation.")
        return

    translator = GoogleTranslator(source='auto', target=dest_language)

    # Translate title and meta description
    translated_title = translator.translate(extracted_title)
    translated_heading=translator.translate(extracted_heading)
    translated_meta = translator.translate(extracted_meta)

    # Translate the extracted container div
    translated_main_content = translate_container_content(raw_html_content, translator, website_url,css_class,domain)
    # print(translated_main_content)
    file_name = f"{urlparse(website_url).path.strip('/').replace('/', '_')}_{dest_language}.php"

    #### file_name with the format {file_name_lang_code} will also be updated to the php_template 
    file_name2 = f"{urlparse(website_url).path.strip('/').replace('/', '_')}"

    save_translated_page(translated_title, translated_meta,translated_heading, translated_main_content, file_name,dest_language, php_template, file_name2)