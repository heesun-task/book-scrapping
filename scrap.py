import os
import requests
from bs4 import BeautifulSoup

# Base URLs
base_url = "http://en.childrenslibrary.org/library/lang74.html"
book_base_url = "http://en.childrenslibrary.org/library/"

# Parent directory for all downloaded books
parent_folder = "books"

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


# 2. Save books list to a text file
def save_books_to_file(books, filename="books_list.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for book_title, book_url in books:
            f.write(f"{book_title}\t{book_url}\n")
    print(f"Books list saved to {filename}")

# 3 . Download images from the book URL
def download_book_images(book_title, book_url):
    response = requests.get(book_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # Create folder for the book
    folder_name = "".join(c if c.isalnum() or c.isspace() else "_" for c in book_title).strip()
    full_path = os.path.join(parent_folder, folder_name)
    os.makedirs(full_path, exist_ok=True)

    # Collect image links
    images = soup.select('div[dir="rtl"] a img')  # Get all image tags
    for img in images:
        img_src = img.get('src')
        if not img_src:
            continue  # Skip if img['src'] is missing

        # Remove thumbnail-specific suffix
        img_src = img_src.replace('-mini', '')
        print(f"Original src: {img_src}")

        # Construct dynamic image URL
        if img_src.startswith("images/"):
            # Parse and adjust the URL based on the rule
            first_letter = img_src.split('/')[1][0]  # First character of the second part
            book_folder = img_src.split('/')[1].split('-')[0]  # Extract folder name
            img_url = f"{book_base_url}books/{first_letter}/{book_folder}/book/{img_src}"
        else:
            img_url = f"{book_base_url}/{img_src}"  # Fallback for full URLs

        # Skip irrelevant images
        if not img_url.endswith('.jpg'):
            continue  # Skip non-relevant images

        print(f"Final img_url: {img_url}")

        try:
            # Download the image
            img_response = requests.get(img_url)
            if img_response.status_code == 200:  # Check if the image is available
                img_name = os.path.basename(img_src)
                with open(os.path.join(full_path, img_name), 'wb') as f:
                    f.write(img_response.content)
                    print(f"Downloaded {img_name} in {full_path}")
            else:
                print(f"Image not found: {img_url}")
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")


# 4. Execute
if __name__ == "__main__":
    # Create parent folder if it doesn't exist
    os.makedirs(parent_folder, exist_ok=True)

    # TODO: remove this when download all
    # Get the first 10 books (This is for test)
    books = get_book_links()[:10]

    # Save books list to a file
    save_books_to_file(books)

    # Download images for each book
    for book_title, book_url in books:
        print(f"Downloading images for book: {book_title}")
        download_book_images(book_title, book_url)