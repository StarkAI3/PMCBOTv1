import os
import json
import hashlib
import re
from tqdm import tqdm
from bs4 import BeautifulSoup
import html

# Enhanced type mapping for better classification
RAW_TYPE_TO_MAIN_TYPE = {
    # Circulars, Notices, Orders
    'circular': 'circular', 'Circular': 'circular', 'notice': 'circular', 'Notice': 'circular',
    'order': 'circular', 'Order': 'circular', 'notification': 'circular', 'Notification': 'circular',
    
    # Committee Decisions, Meeting Agendas
    'committee_decision': 'committee_decision', 'Committee Decisions': 'committee_decision',
    'meeting': 'committee_decision', 'Meeting': 'committee_decision', 'agenda': 'committee_decision',
    
    # Citizen Charters, Service Charters
    'citizen_charter': 'citizen_charter', 'Citizen Charter': 'citizen_charter',
    'service_charter': 'citizen_charter', 'Service Charter': 'citizen_charter',
    
    # Awards, Recognitions
    'award': 'award', 'Awards': 'award', 'Awards & Recognition': 'award',
    'recognition': 'award', 'Recognition': 'award', 'honor': 'award',
    
    # Gardens, Parks
    'garden': 'garden', 'Gardens In Pune': 'garden', 'Garden List': 'garden', 
    'Garden Rules': 'garden', 'Garden Department Sub': 'garden', 'park': 'garden',
    'Park': 'garden', 'green space': 'garden', 'recreation': 'garden',
    
    # Departments, Contacts, Officers
    'department': 'department', 'Department': 'department', 
    'Contact Numbers of Officials from the Electrical Department': 'department', 
    'PMC Officers Directory': 'department', 'contact': 'department', 'Contact': 'department',
    'officer': 'department', 'Officer': 'department', 'directory': 'department',
    
    # Projects
    'project': 'project', 'Project Documents': 'project', 'Project Glimpses': 'project', 
    'Projects': 'project', 'development': 'project', 'Development': 'project',
    'infrastructure': 'project', 'Infrastructure': 'project',
    
    # Events
    'event': 'event', 'Events': 'event', 'Competitions': 'event', 'Exhibitions': 'event',
    'competition': 'event', 'exhibition': 'event', 'program': 'event', 'Program': 'event',
    'campaign': 'event', 'Campaign': 'event',
    
    # News
    'news': 'news', 'News & Updates': 'news', 'Press Note': 'news',
    'update': 'news', 'Update': 'news', 'press': 'news', 'Press': 'news',
    'announcement': 'news', 'Announcement': 'news',
    
    # Hospitals
    'hospital': 'hospital', 'Hospital': 'hospital', 'Blood Bank': 'hospital', 
    'Eye Bank': 'hospital', 'medical': 'hospital', 'Medical': 'hospital',
    'health': 'hospital', 'Health': 'hospital', 'clinic': 'hospital',
    
    # Schools
    'school': 'school', 'School List': 'school', 'Model Schools': 'school', 
    'Primary and Technical Education School List': 'school', 'education': 'school',
    'Education': 'school', 'academy': 'school', 'Academy': 'school',
    
    # Crematoriums
    'crematorium': 'crematorium', 'Crematoriums': 'crematorium', 'List of cemeteries': 'crematorium',
    'cemetery': 'crematorium', 'Cemetery': 'crematorium', 'burial': 'crematorium',
    
    # Fire Brigade
    'fire_brigade': 'fire_brigade', 'Fire Brigade Stations': 'fire_brigade', 
    'Fire Safety': 'fire_brigade', 'fire': 'fire_brigade', 'Fire': 'fire_brigade',
    'emergency': 'fire_brigade', 'Emergency': 'fire_brigade',
    
    # Hoardings
    'hoarding': 'hoarding', 'Hoarding Rules': 'hoarding', 'Authorised Hoardings': 'hoarding',
    'advertisement': 'hoarding', 'Advertisement': 'hoarding', 'billboard': 'hoarding',
    
    # Policies, Guidelines, Acts, Regulations
    'policy': 'policy', 'Policies': 'policy', 'Guidelines': 'policy', 
    'Acts and Regulations': 'policy', 'regulation': 'policy', 'Regulation': 'policy',
    'act': 'policy', 'Act': 'policy', 'rule': 'policy', 'Rule': 'policy',
    'guideline': 'policy', 'Guideline': 'policy',
    
    # Schemes, Welfare, Subsidies
    'scheme': 'scheme', 'Schemes': 'scheme', 'Welfare': 'scheme',
    'subsidy': 'scheme', 'Subsidy': 'scheme', 'benefit': 'scheme', 'Benefit': 'scheme',
    'assistance': 'scheme', 'Assistance': 'scheme',
    
    # Ward Offices
    'ward_office': 'ward_office', 'Ward Offices': 'ward_office',
    'ward': 'ward_office', 'Ward': 'ward_office', 'regional': 'ward_office',
    
    # FAQ, Help, Grievance
    'faq': 'faq', 'FAQ': 'faq', 'Frequently Asked Questions': 'faq', 'Grievance': 'faq',
    'help': 'faq', 'Help': 'faq', 'question': 'faq', 'Question': 'faq',
    'complaint': 'faq', 'Complaint': 'faq',
    
    # Online Services, Applications
    'service': 'service', 'Online Services': 'service', 'E-Services': 'service', 
    'Applications': 'service', 'online': 'service', 'Online': 'service',
    'application': 'service', 'Application': 'service', 'portal': 'service',
    'Portal': 'service', 'digital': 'service', 'Digital': 'service',
    
    # Tax and Revenue
    'tax': 'tax', 'Tax': 'tax', 'property tax': 'tax', 'Property Tax': 'tax',
    'revenue': 'tax', 'Revenue': 'tax', 'payment': 'tax', 'Payment': 'tax',
    'bill': 'tax', 'Bill': 'bill',
    
    # Water and Utilities
    'water': 'utility', 'Water': 'utility', 'supply': 'utility', 'Supply': 'utility',
    'electricity': 'utility', 'Electricity': 'utility', 'utility': 'utility',
    'Utility': 'utility',
    
    # Waste Management
    'waste': 'waste', 'Waste': 'waste', 'garbage': 'waste', 'Garbage': 'waste',
    'sanitation': 'waste', 'Sanitation': 'waste', 'cleaning': 'waste',
    'Cleaning': 'waste', 'plastic': 'waste', 'Plastic': 'waste',
    
    # Transport and Traffic
    'transport': 'transport', 'Transport': 'transport', 'traffic': 'transport',
    'Traffic': 'transport', 'bus': 'transport', 'Bus': 'transport',
    'parking': 'transport', 'Parking': 'transport',
    
    # Building and Construction
    'building': 'construction', 'Building': 'construction', 'construction': 'construction',
    'Construction': 'construction', 'permit': 'construction', 'Permit': 'construction',
    'license': 'construction', 'License': 'construction',
}

def clean_html_text(text):
    """Clean HTML content and extract meaningful text."""
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_all_text_content(record):
    """Extract all available text content from a record."""
    text_parts = []
    
    # Extract title
    title = record.get('title') or record.get('name') or record.get('subject')
    if title:
        text_parts.append(f"Title: {title}")
    
    # Extract description
    description = record.get('description') or record.get('desc') or record.get('short_description')
    if description:
        text_parts.append(f"Description: {description}")
    
    # Extract long description
    long_desc = record.get('long_description')
    if long_desc:
        text_parts.append(f"Details: {long_desc}")
    
    # Extract summary (often contains rich HTML content)
    summary = record.get('summary')
    if summary:
        if isinstance(summary, list):
            for item in summary:
                cleaned = clean_html_text(item)
                if cleaned:
                    text_parts.append(f"Summary: {cleaned}")
        else:
            cleaned = clean_html_text(summary)
            if cleaned:
                text_parts.append(f"Summary: {cleaned}")
    
    # Extract other text fields
    for field in ['content', 'body', 'text', 'details', 'information']:
        value = record.get(field)
        if value:
            cleaned = clean_html_text(value) if isinstance(value, str) else str(value)
            if cleaned:
                text_parts.append(f"{field.title()}: {cleaned}")
    
    # Extract department and ward information
    department = record.get('department')
    if department:
        text_parts.append(f"Department: {department}")
    
    ward_name = record.get('ward_name')
    if ward_name:
        text_parts.append(f"Ward: {ward_name}")
    
    # Extract contact information
    operator_name = record.get('operator_name')
    operator_contact = record.get('operator_contact')
    if operator_name or operator_contact:
        contact_info = []
        if operator_name:
            contact_info.append(f"Contact Person: {operator_name}")
        if operator_contact:
            contact_info.append(f"Contact: {operator_contact}")
        text_parts.append(" ".join(contact_info))
    
    # Extract address
    address = record.get('address')
    if address:
        text_parts.append(f"Address: {address}")
    
    # Extract status and other details
    status = record.get('status')
    if status:
        text_parts.append(f"Status: {status}")
    
    other_details = record.get('other_details')
    if other_details:
        text_parts.append(f"Other Details: {other_details}")
    
    return "\n".join(text_parts)

def map_to_main_type(record, source_url=None):
    """Enhanced type mapping with better pattern matching."""
    # Try to use explicit record_type/content_type/content_type_name
    for key in ['record_type', 'content_type', 'content_type_name', 'type']:
        val = record.get(key)
        if val and val in RAW_TYPE_TO_MAIN_TYPE:
            return RAW_TYPE_TO_MAIN_TYPE[val]
    
    # Try to use title/section with more comprehensive matching
    title = record.get('title', '')
    title_lower = title.lower()
    
    # Check for exact matches first
    for raw, main in RAW_TYPE_TO_MAIN_TYPE.items():
        if raw.lower() in title_lower:
            return main
    
    # Check for partial matches and keywords
    keywords_mapping = {
        'circular': ['circular', 'notice', 'order', 'notification'],
        'department': ['department', 'contact', 'officer', 'directory'],
        'project': ['project', 'development', 'infrastructure', 'construction'],
        'event': ['event', 'competition', 'exhibition', 'program', 'campaign'],
        'news': ['news', 'update', 'press', 'announcement'],
        'hospital': ['hospital', 'medical', 'health', 'clinic', 'blood bank'],
        'school': ['school', 'education', 'academy', 'college'],
        'service': ['service', 'online', 'application', 'portal', 'digital'],
        'tax': ['tax', 'property tax', 'revenue', 'payment', 'bill'],
        'utility': ['water', 'electricity', 'supply', 'utility'],
        'waste': ['waste', 'garbage', 'sanitation', 'cleaning', 'plastic'],
        'transport': ['transport', 'traffic', 'bus', 'parking'],
        'construction': ['building', 'construction', 'permit', 'license'],
    }
    
    for main_type, keywords in keywords_mapping.items():
        for keyword in keywords:
            if keyword in title_lower:
                return main_type
    
    # Try to use source_url
    if source_url:
        url_lower = source_url.lower()
        for raw, main in RAW_TYPE_TO_MAIN_TYPE.items():
            if raw.lower() in url_lower:
                return main
    
    # Fallback based on content analysis
    all_text = extract_all_text_content(record).lower()
    for main_type, keywords in keywords_mapping.items():
        for keyword in keywords:
            if keyword in all_text:
                return main_type
    
    return 'other'

def get_id(fields):
    """Generate a unique hash for a record based on key fields."""
    concat = '|'.join([str(fields.get(k, '')) for k in ['title', 'date', 'department', 'pdf_url', 'source_url']])
    return hashlib.sha256(concat.encode('utf-8')).hexdigest()

def clean_dict(d):
    """Clean dictionary by removing empty values."""
    return {k: v for k, v in d.items() if v not in [None, '', [], {}]}

def extract_from_node(node, source_url, lang):
    """Enhanced extraction with better content processing."""
    # Try to extract key fields for a single item
    title = node.get('title') or node.get('name') or node.get('subject')
    
    # Only include if at least a title/name/subject is present
    if not title:
        return None
    
    # Extract all available text content
    full_content = extract_all_text_content(node)
    
    # Extract as many fields as possible
    record = {
        'title': title,
        'date': node.get('date') or node.get('display_date') or node.get('publish_date') or node.get('changed'),
        'department': node.get('department'),
        'ward_name': node.get('ward_name'),
        'crematorium_type': node.get('crematorium_type'),
        'address': node.get('address'),
        'image': node.get('image'),
        'alt': node.get('alt'),
        'pdf_url': node.get('file') or node.get('pdf_url'),
        'external_link': node.get('external_link'),
        'link': node.get('link'),
        'url': node.get('url'),
        'description': node.get('description') or node.get('desc') or node.get('short_description'),
        'long_description': node.get('long_description'),
        'summary': node.get('summary'),
        'operator_contact': node.get('operator_contact'),
        'operator_name': node.get('operator_name'),
        'tag': node.get('tag'),
        'status': node.get('status'),
        'other_details': node.get('other_details'),
        'source_url': source_url,
        'lang': lang,
        'raw': node,  # Retain the full node for fallback
        'full_content': full_content  # Add the full extracted content
    }
    
    # Add type assignment using enhanced mapping
    main_type = map_to_main_type(node, source_url)
    record['record_type'] = main_type
    record['type'] = main_type  # Alias for clarity
    
    # Clean the record
    record = clean_dict(record)
    record['id'] = get_id(record)
    
    return record

def process_file(input_path, lang):
    """Process a single file with enhanced error handling."""
    output = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc=f'Processing {input_path}'):
            try:
                entry = json.loads(line)
                source_url = entry.get('source_url') if isinstance(entry, dict) else None
                nodes = []
                
                # If the entry is a list, treat each item as a node
                if isinstance(entry, list):
                    nodes = entry
                elif 'raw' in entry:
                    raw = entry['raw']
                    if isinstance(raw, dict):
                        if 'data' in raw and 'nodes' in raw['data']:
                            nodes = raw['data']['nodes']
                        elif 'budgets' in raw:
                            nodes = raw['budgets']
                        elif 'election_level1' in raw:
                            nodes = raw['election_level1']
                        else:
                            nodes = [raw]
                    elif isinstance(raw, list):
                        nodes = raw
                    else:
                        nodes = [raw]
                else:
                    nodes = [entry]
                
                for node in nodes:
                    record = extract_from_node(node, source_url, lang)
                    if record:
                        output.append(record)
                        
            except Exception as e:
                print(f'Error processing line: {e}')
                continue
    
    return output

def main():
    """Main function to process all data files."""
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.jsonl') and not f.endswith('normalized.jsonl')]
    
    if not files:
        print("No input files found in data directory")
        return
    
    all_records = []
    
    for fname in files:
        lang = 'en' if 'en' in fname else 'mr' if 'mr' in fname else 'unknown'
        print(f"\nProcessing {fname} (language: {lang})")
        records = process_file(os.path.join(data_dir, fname), lang)
        all_records.extend(records)
        print(f"Extracted {len(records)} records from {fname}")
    
    # Write normalized output
    out_path = os.path.join(data_dir, 'pmc_data_normalized.jsonl')
    with open(out_path, 'w', encoding='utf-8') as out:
        for rec in all_records:
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    
    print(f'\nNormalization complete!')
    print(f'Total records processed: {len(all_records)}')
    print(f'Output written to: {out_path}')
    
    # Print some statistics
    type_counts = {}
    for rec in all_records:
        rec_type = rec.get('record_type', 'unknown')
        type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
    
    print(f'\nRecord type distribution:')
    for rec_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {rec_type}: {count}')

if __name__ == '__main__':
    main() 