import os
import re
import json
import requests
from tqdm import tqdm
import urllib3
import hashlib
from urllib.parse import urlparse
from collections import defaultdict

# Suppress only the single InsecureRequestWarning from urllib3 needed.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Input files
ENG_LINKS = 'eng_links'
MR_LINKS = 'mr_links'

# Output files
OUT_ENG = 'data/pmc_data_en.jsonl'
OUT_MR = 'data/pmc_data_mr.jsonl'

# Regex patterns for extraction
PDF_PATTERN = re.compile(r'https?://[^\s]+\.pdf')
PHONE_PATTERN = re.compile(r'\b(\+91[-\s]?)?[0]?[6789]\d{9}\b')
MAP_PATTERN = re.compile(r'https?://(goo\.gl|maps\.google\.com|www\.google\.com/maps)[^\s]*')

class LinkProcessor:
    def __init__(self, lang):
        self.lang = lang
        self.success_links = []
        self.failed_links = []
        self.broken_links = []
        self.duplicate_links = []
        self.processed_content_hashes = set()
        self.url_content_map = defaultdict(list)
        
    def clean_obj(self, obj):
        """Recursive cleaner for null/empty values"""
        if isinstance(obj, dict):
            return {k: self.clean_obj(v) for k, v in obj.items() 
                   if v not in [None, '', [], {}] and self.clean_obj(v) not in [None, '', [], {}]}
        elif isinstance(obj, list):
            return [self.clean_obj(v) for v in obj 
                   if v not in [None, '', [], {}] and self.clean_obj(v) not in [None, '', [], {}]]
        else:
            return obj

    def extract_fields(self, obj):
        """Helper to extract fields from JSON"""
        cleaned = self.clean_obj(obj)
        text = json.dumps(cleaned, ensure_ascii=False)
        pdfs = list(set(PDF_PATTERN.findall(text)))
        phones = list(set(PHONE_PATTERN.findall(text)))
        maps = list(set(MAP_PATTERN.findall(text)))
        
        return {
            'pdf_links': pdfs,
            'phone_numbers': phones,
            'map_links': maps,
            'raw': cleaned
        }

    def get_content_hash(self, data, url):
        """Generate hash for content to detect duplicates"""
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
            # Handle nested data structure
            content_str = json.dumps(data['data'], ensure_ascii=False, sort_keys=True)
        else:
            content_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256((content_str + self.lang + url).encode('utf-8')).hexdigest()

    def is_broken_link(self, url, response):
        """Check if link is broken (404, 500, etc.)"""
        if response.status_code in [404, 410, 500, 502, 503, 504]:
            return True
        return False

    def is_duplicate_content(self, content_hash, url):
        """Check if content is duplicate"""
        if content_hash in self.processed_content_hashes:
            return True
        return False

    def process_single_url(self, url, max_retries=3):
        """Process a single URL and categorize it"""
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, timeout=15, verify=False)
                
                # Check if link is broken
                if self.is_broken_link(url, resp):
                    self.broken_links.append(url)
                    return 'broken'
                
                resp.raise_for_status()
                data = resp.json()
                
                # Generate content hash
                content_hash = self.get_content_hash(data, url)
                
                # Check for duplicates
                if self.is_duplicate_content(content_hash, url):
                    self.duplicate_links.append(url)
                    return 'duplicate'
                
                # Process successful data
                self.processed_content_hashes.add(content_hash)
                self.url_content_map[url] = data
                self.success_links.append(url)
                return 'success'
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    self.failed_links.append(url)
                    return 'failed'
                continue
            except (json.JSONDecodeError, ValueError) as e:
                # Invalid JSON response
                self.failed_links.append(url)
                return 'failed'
            except Exception as e:
                if attempt == max_retries - 1:
                    self.failed_links.append(url)
                    return 'failed'
                continue

    def process_links(self, input_file, output_file):
        """Process all links from input file"""
        print(f"\nProcessing {self.lang} links...")
        
        # Read links from file
        with open(input_file, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
        
        print(f"Total links to process: {len(links)}")
        
        # Process each link
        for url in tqdm(links, desc=f'Processing {self.lang} links'):
            result = self.process_single_url(url)
        
        # Write successful data to JSONL file
        self.write_successful_data(output_file)
        
        # Write categorized links to files
        self.write_categorized_links()
        
        # Print summary
        self.print_summary()

    def write_successful_data(self, output_file):
        """Write successful data to JSONL file"""
        with open(output_file, 'w', encoding='utf-8') as out:
            for url, data in self.url_content_map.items():
                try:
                    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                        # Handle nested data structure
                        for item in data['data']:
                            fields = self.extract_fields(item)
                            fields['source_url'] = url
                            fields['lang'] = self.lang
                            out.write(json.dumps(fields, ensure_ascii=False) + '\n')
                    else:
                        fields = self.extract_fields(data)
                        fields['source_url'] = url
                        fields['lang'] = self.lang
                        out.write(json.dumps(fields, ensure_ascii=False) + '\n')
                except Exception as e:
                    print(f"Error writing data for {url}: {e}")

    def write_categorized_links(self):
        """Write categorized links to separate files"""
        # Success links
        with open(f'success_links_{self.lang}.txt', 'w', encoding='utf-8') as f:
            for url in self.success_links:
                f.write(url + '\n')
        
        # Failed links
        with open(f'failed_links_{self.lang}.txt', 'w', encoding='utf-8') as f:
            for url in self.failed_links:
                f.write(url + '\n')
        
        # Broken links
        with open(f'broken_links_{self.lang}.txt', 'w', encoding='utf-8') as f:
            for url in self.broken_links:
                f.write(url + '\n')
        
        # Duplicate links
        with open(f'duplicate_links_{self.lang}.txt', 'w', encoding='utf-8') as f:
            for url in self.duplicate_links:
                f.write(url + '\n')

    def print_summary(self):
        """Print processing summary"""
        print(f"\n=== {self.lang.upper()} LINKS PROCESSING SUMMARY ===")
        print(f"Total links processed: {len(self.success_links) + len(self.failed_links) + len(self.broken_links) + len(self.duplicate_links)}")
        print(f"✅ Success links: {len(self.success_links)} (see success_links_{self.lang}.txt)")
        print(f"❌ Failed links: {len(self.failed_links)} (see failed_links_{self.lang}.txt)")
        print(f"🔗 Broken links: {len(self.broken_links)} (see broken_links_{self.lang}.txt)")
        print(f"🔄 Duplicate links: {len(self.duplicate_links)} (see duplicate_links_{self.lang}.txt)")
        print(f"📊 Success rate: {(len(self.success_links) / (len(self.success_links) + len(self.failed_links) + len(self.broken_links) + len(self.duplicate_links)) * 100):.1f}%")

def main():
    """Main function to process both English and Marathi links"""
    print("🚀 Starting Enhanced PMC Data Extraction...")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Process English links
    eng_processor = LinkProcessor('en')
    eng_processor.process_links(ENG_LINKS, OUT_ENG)
    
    print("\n" + "=" * 50)
    
    # Process Marathi links
    mr_processor = LinkProcessor('mr')
    mr_processor.process_links(MR_LINKS, OUT_MR)
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced PMC Data Extraction Complete!")
    print("\nGenerated files:")
    print("📁 Data files:")
    print("  - data/pmc_data_en.jsonl")
    print("  - data/pmc_data_mr.jsonl")
    print("\n📁 Link categorization files:")
    print("  - success_links_en.txt, success_links_mr.txt")
    print("  - failed_links_en.txt, failed_links_mr.txt")
    print("  - broken_links_en.txt, broken_links_mr.txt")
    print("  - duplicate_links_en.txt, duplicate_links_mr.txt")

if __name__ == '__main__':
    main() 