import os
import json
import requests
from bs4 import BeautifulSoup

# Base URLs
base_url = "http://en.childrenslibrary.org/library/lang74.html"
book_base_url = "http://en.childrenslibrary.org/library/"

# Parent directory for all downloaded books
parent_folder = "books"

# JSON file to store book metadata
metadata_file = "books_metadata.json"

# 1. Bring the book lists
def get_book_links():
    response = requests.get(base_url)
    response.encoding = 'utf-8'  # Handle Persian text
    soup = BeautifulSoup(response.text, 'html.parser')

    books = []
    for link in soup.select('ol li a'):  # Select all links within the list items
        book_title = link.text.strip()  # Extract the book title
        href = link.get('href', '')  # Extract the href value
        if href.startswith('books/'):
            # Modify the href to point to the book's "book/index.html"
            book_url = href.replace("index.html", "book/index.html")
            full_book_url = f"{book_base_url}{book_url}"  # Complete the URL
            books.append((book_title, full_book_url))
    return books

# 2. Extract metadata from book page
import re

def extract_metadata(book_title, book_url, book_number):
    # Extract book ID using regex
    match = re.search(r"books/./([^/]+)/book/index.html", book_url)
    book_id = match.group(1) if match else None  # Extract matched book ID

    book_meta_url = book_url.replace("/book/index.html", "/index.html")
    response = requests.get(book_meta_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # # Normalize the book title for consistent naming
    # normalized_title = re.sub(r'[^a-zA-Z0-9_\u0600-\u06FF\s]', '', book_title)  # Allow English, Persian, numbers, spaces
    # normalized_title = re.sub(r'\s+', '_', normalized_title).strip()  # Replace spaces with underscores

    metadata = {
        "index": book_number,
        "folder_name": f"b{book_number:03d}_{book_title}_{book_id}",  # Add folder name to metadata
        "bookId": book_id,  # Include book ID (e.g., khareds_00500145)
        "title": book_title,
        "language": None,
        "type": None,
        "author": [],
        "illustrator": [],
        "abstract": None,
        "publisher": None,
        "published": None,
        "published_in": None,
        "ISBN": None,
        "contributed_by": None
    }

    content = soup.find('div', id='body')
    if content:
        def extract_text(label):
            item = next((s for s in content.stripped_strings if label in s), None)
            return item.split(":", 1)[-1].strip() if item else None

        metadata["language"] = extract_text("Language:")
        metadata["type"] = extract_text("Type:")
        metadata["abstract"] = extract_text("Abstract:")
        metadata["publisher"] = extract_text("Publisher:")
        metadata["published"] = extract_text("Published:")
        metadata["published_in"] = extract_text("Published in:")
        metadata["ISBN"] = extract_text("ISBN:")
        metadata["contributed_by"] = extract_text("Contributed by:")

        # Regular expression to capture names between <li> and (Role)
        matches = re.findall(r"(?<=<li>)(.*?)(?=\s*\()", response.text)

        # Regular expression to classify roles (Author or Illustrator)
        roles = re.findall(r"\((.*?)\)", response.text)

        authors = []
        illustrators = []

        # Assign names to the correct category
        for i, name in enumerate(matches):
            if i < len(roles):
                role = roles[i].strip()
                if role == "Author":
                    authors.append(name.strip())
                elif role == "Illustrator":
                    illustrators.append(name.strip())

        # Remove duplicates
        metadata["author"] = authors
        metadata["illustrator"] = illustrators

        return metadata

    return metadata
# 3. Save book metadata to JSON file
def save_metadata_to_file(metadata):
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(metadata)

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Metadata saved for book: {metadata['title']}")

# 4. Download images from the book URL
import re

def download_book_images(metadata, book_url):
    folder_name = metadata["folder_name"]  # Use the folder name from metadata
    bookId = metadata["bookId"]
    print(folder_name)
    full_path = os.path.join(parent_folder, folder_name)
    os.makedirs(full_path, exist_ok=True)

    response = requests.get(book_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # Collect image links
    images = soup.select('div[dir="rtl"] a img')  # Get all image tags
    for index, img in enumerate(images, start=1):
        img_src = img.get('src')
        if not img_src:
            continue  # Skip if img['src'] is missing

        # Remove thumbnail-specific suffix
        img_src = img_src.replace('-mini', '')

        # Construct dynamic image URL
        if img_src.startswith("images/"):
            first_letter = img_src.split('/')[1][0]  # First character of the second part
            book_folder = img_src.split('/')[1].split('-')[0]  # Extract folder name
            img_url = f"{book_base_url}books/{first_letter}/{book_folder}/book/{img_src}"
        else:
            img_url = f"{book_base_url}/{img_src}"  # Fallback for full URLs

        # Skip irrelevant images
        if not img_url.endswith('.jpg'):
            continue  # Skip non-relevant images

        try:
            # Download the image
            img_response = requests.get(img_url)
            if img_response.status_code == 200:
                img_name = f"{bookId}_{index:04d}.jpg"
                with open(os.path.join(full_path, img_name), 'wb') as f:
                    f.write(img_response.content)
                    print(f"Downloaded {img_url} as  {img_name} in {full_path}")
            else:
                print(f"Image not found: {img_url}")
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")
# 5. Execute
if __name__ == "__main__":
    # Create parent folder if it doesn't exist
    os.makedirs(parent_folder, exist_ok=True)

    books = get_book_links()

    print("books")
    print(books)
    for book_number, (book_title, book_url) in enumerate(books, start=1):
        print(f"Processing book: {book_title}")
        metadata = extract_metadata(book_title, book_url, book_number)
        save_metadata_to_file(metadata)
        download_book_images(metadata, book_url)