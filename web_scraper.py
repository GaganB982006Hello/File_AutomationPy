import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_data(url):
    import tempfile
    
    # Validation already mostly handled, but we can check if URL is valid-ish
    if not url.startswith('http'):
        return None, "Error: Invalid URL. Please include http:// or https://"

    try:
        # Add headers to mimic a browser, often helps with scraping
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = []
            
            # Original Logic: Specific to a site with 'product-item' class
            items = soup.find_all('div', class_='product-item')
            
            # If original specific logic fails (no items found), try a more generic approach
            if items:
                for item in items:
                    name_tag = item.find('h2', class_='title')
                    price_tag = item.find('span', class_='price')
                    
                    name = name_tag.text.strip() if name_tag else "Unknown"
                    price = price_tag.text.strip() if price_tag else "0"
                    products.append({"Name": name, "Price": price})
            else:
                # Fallback: Scrape all links provided they have text
                # This makes the tool usable for other sites even if the original logic doesn't match
                links = soup.find_all('a')
                for link in links:
                    text = link.text.strip()
                    href = link.get('href')
                    if text and href:
                         products.append({"Text": text, "Link": href})
                         
            if not products:
                return None, "No structured data or links found on the page."

            # Convert to DataFrame and save to Excel in /tmp
            df = pd.DataFrame(products)
            
            output_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
            output_path = os.path.join(output_dir, "Scraped_Data.xlsx")
            
            df.to_excel(output_path, index=False)
            return output_path, f"Data scraped ({len(products)} items)."
        else:
            return None, f"Failed to retrieve website. Status code: {response.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == "__main__":
    pass
