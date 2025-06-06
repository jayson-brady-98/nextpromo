import json
import csv
import re
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta

def load_raw_data(filename: str) -> Dict:
    with open(filename, 'r') as f:
        return json.load(f)

def filter_non_promotional(data: Dict) -> Dict:
    """Filter out entries where promotion is False"""
    return {k: v for k, v in data.items() if v['promotion']}

def filter_single_context(data: Dict) -> Dict:
    """Filter out entries with only one keyword in promo_contexts"""
    return {k: v for k, v in data.items() if len(v['promo_contexts']) > 1}

def filter_promotional_patterns(context: str) -> bool:
    """Return False if context contains unwanted promotional patterns"""
    
    # Check for navigation menu items
    nav_keywords = [
        'gift card', 'e-gift card', 'products', 'accessories', 'all sale', 'best sellers',
        'gifts for him', 'gifts for her', 'trending', 'products under', 'tops', 'bottoms',
        'dresses', 'skirts', 'pants', 'jeans', 'shorts', 'leggings', 'activewear',
        'outerwear', 'coats', 'jackets', 'blazers', 'sweaters', 'sweatshirts', 'hoodies',
        'cardigans', 'shirts', 'blouses', 't-shirts', 'tank tops', 'camisoles', 'bodysuits',
        'jumpsuits', 'rompers', 'swimwear', 'bikinis', 'one-pieces', 'cover-ups', 'lingerie',
        'bras', 'underwear', 'sleepwear', 'pajamas', 'robes', 'socks', 'tights', 'stockings',
        'suits', 'vests', 'knitwear', 'denim', 'athleisure', 'sportswear', 'workout clothes',
        'gym wear', 'yoga clothes', 'running gear', 'loungewear', 'casual wear', 'formal wear',
        'business wear', 'evening wear', 'party wear', 'beachwear', 'resort wear', 'winter wear',
        'summer clothes', 'spring collection', 'fall collection', 'seasonal wear', 'basics',
        'essentials', 'coordinates', 'matching sets', 'two-piece sets', 'three-piece sets',
        'tunics', 'ponchos', 'shawls', 'scarves', 'belts', 'gloves', 'mittens', 'hats', 'caps',
        'beanies', 'headwear', 'footwear', 'shoes', 'boots', 'sandals', 'sneakers', 'slippers',
        'heels', 'flats', 'loafers', 'oxfords', 'mules', 'espadrilles', 'socks', 'gear',
        'hats', 'singlets'
    ]
    
    # Separate gender keywords with their prefixes
    gender_base_keywords = ['womens', "women's", 'mens', "men's", 'baby', 'kids', 'teens']
    gender_prefixes = ['shop', 'sale', 'new', 'all']
    
    # Generate full list of gender keywords including prefixed versions
    gender_keywords = []
    for keyword in gender_base_keywords:
        gender_keywords.append(keyword)  # Add base keyword
        # Add prefixed versions
        for prefix in gender_prefixes:
            gender_keywords.append(f"{prefix} {keyword}")
    
    context_lower = context.lower()
    
    # Count navigation keywords (excluding gender)
    nav_keyword_count = sum(1 for keyword in nav_keywords if keyword in context_lower)
    
    # Count gender keywords
    gender_keyword_count = sum(1 for keyword in gender_keywords if keyword in context_lower)
    
    # Filter out if we have at least 3 total keywords AND at least 1 non-gender keyword
    if (nav_keyword_count + gender_keyword_count) >= 3 and nav_keyword_count >= 1:
        return False
    
    # Existing promotional patterns check
    patterns = [
        # Update existing buy-get patterns to be more comprehensive
        r'buy\s*\d+[^.]*get\s*\d+',  # Original pattern
        r'buy\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?[^.]*get\s*\d+%?\s*off',  # New pattern
        r'buy\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?[^.]*and\s*(?:get|receive)\s*\d+%?\s*off',  # Another variation
        
        # Make sure we catch product-specific offers
        r'buy\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?\s*(?:of|pieces?|items?|[a-zA-Z\s]+(?:leggings?|shorts?|tops?))[^.]*get\s*\d+%?\s*off',
        
        # Existing patterns
        r'buy\s*\d+[^.]*\d+%\s*off',
        r'buy\s*one[^.]*get\s*one',
        r'b[uy]{2}g[o]{2}',
        r'\d+\s*for\s*\d+',
        r'sign\s*up[^.]*\d+%\s*off',
        r'join[^.]*\d+%\s*off',
        r'subscribe[^.]*\d+%\s*off',
        r'newsletter.*(?:discount|deal|offer|saving)',  # Newsletter mentions with promotional terms
        r'(?:discount|deal|offer|saving).*newsletter',  # Same as above but reversed order
        r'(?:exclusive|special)\s+(?:discount|deal|offer|saving).*(?:member|membership)',  # Membership-related offers
        r'(?:member|membership).*(?:exclusive|special)\s+(?:discount|deal|offer|saving)',  # Same as above but reversed
        r'download.*(?:discount|deal|offer|saving)',  # Download-related promotions
        r'(?:discount|deal|offer|saving).*download',  # Same as above but reversed
        
        # New patterns for filtering additional cases
        r'\d+%\s*off.*(?:next|first)\s*(?:order|purchase)',  # Matches "10% off your next order"
        r'(?:sign|signed)\s*(?:up|me up).*(?:discount|off|news)',  # Matches "sign up for discounts", "sign me up"
        r'(?:free|complimentary)\s*shipping.*(?:orders?\s*(?:over|above)?\s*[\$£€]?\d+)',  # Matches shipping threshold offers
        r'\d+%\s*off\s*[+&]\s*free\s*shipping',  # Matches combined discount + shipping offers
        r'(?:exclusive|latest)\s*(?:discounts?|news|offers?).*(?:sign|email)',  # Newsletter/signup related
        r'(?:want|get)\s*(?:emails|news|updates).*(?:\d+%\s*off)',  # Email signup incentives
        r'(?:sign|subscribe).*(?:emails?|newsletter).*(?:read|updates?)',  # Newsletter engagement text
        
        # Updated threshold-based offers with 20 char limit
        r'(?:orders?|purchases?|spend).{0,20}(?:over|above)?\s*[\$£€]?\d+',  # Matches spending threshold offers
        r'\d+%\s*off.{0,20}(?:orders?|purchases?).*(?:over|above)?\s*[\$£€]?\d+',  # Combined threshold discounts
        
        # Add new grab-related patterns
        r'grab\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?[^.]*get\s*\d+%?\s*off',
        r'grab\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?[^.]*and\s*(?:get|receive)\s*\d+%?\s*off',
        r'grab\s*(?:\d+|two|three|four|five)\s*(?:or\s*more)?\s*(?:of|pieces?|items?|[a-zA-Z\s]+(?:leggings?|shorts?|tops?))[^.]*get\s*\d+%?\s*off',
    ]
    
    return not any(re.search(pattern, context.lower()) for pattern in patterns)

def clean_promo_contexts(data: Dict) -> Dict:
    """Filter out unwanted promotional contexts while preserving entries"""
    cleaned_data = {}
    
    for timestamp, entry in data.items():
        cleaned_entry = entry.copy()
        cleaned_contexts = {}
        
        # Filter contexts for each keyword
        for keyword, contexts in entry['promo_contexts'].items():
            filtered_contexts = [ctx for ctx in contexts if filter_promotional_patterns(ctx)]
            if filtered_contexts:  # Only keep keywords with remaining contexts
                cleaned_contexts[keyword] = filtered_contexts
        
        # Keep entry if it has any valid contexts remaining
        if cleaned_contexts:  # Changed from len(cleaned_contexts) > 1
            cleaned_entry['promo_contexts'] = cleaned_contexts
            cleaned_data[timestamp] = cleaned_entry
            
    return cleaned_data

def determine_event(promo_contexts: Dict, brand: str = '') -> str:
    # First check the actual keywords used
    keywords_used = set(k.lower() for k in promo_contexts.keys())
    
    # Priority keywords to check first
    priority_keywords = {
        "black friday": "Black Friday",
        "cyber monday": "Cyber Monday",
        "boxing day": "Boxing Day",
    }
    
    # Check if any priority keywords were used
    for keyword, event_name in priority_keywords.items():
        if keyword in keywords_used:
            return event_name
    
    # Get all contexts for pattern matching
    all_contexts = []
    for context_list in promo_contexts.values():
        all_contexts.extend(context_list)
    
    # Convert to lowercase and join for pattern matching
    full_context = ' '.join(all_contexts).lower()
    brand = brand.lower()
    
    # Check for major sale keywords first
    major_sale_keywords = [
        "afterpay day", "boxing day", "flash sale", "singles day",
        "international womens day", "end of season", "mid season",
        "mid season sale", "stocktake sale",
        "eofy", "end of financial year", "birthday sale", "blackout",
        "labour day", "labor day", "4th of july", "fourth of july", 'hauliday',
        "friends and family", "outlet", "outlet sale", "men's outlet", "women's outlet"
    ]
    
    # Check major keywords first
    for keyword in major_sale_keywords:
        if keyword in full_context:
            return keyword.title()
    
    # Special case for summer/winter sale
    if "summer sale" in full_context or "winter sale" in full_context:
        return "Summer/Winter Sale"
    
    # Last priority: Check for brand-specific sale
    if brand and f"{brand} sale" in full_context:
        return "Generic Sale"
    
    return ""  # Return empty string if no keywords found

def determine_discount(promo_contexts: Dict) -> str:
    """Extract discount information from promotional contexts"""
    # Combine all contexts
    all_contexts = []
    for context_list in promo_contexts.values():
        all_contexts.extend(context_list)
    
    full_context = ' '.join(all_contexts).lower()
    
    # First check for "up to" patterns
    up_to_pattern = r'up\s+to\s+(\d+)%\s+off'
    up_to_matches = re.findall(up_to_pattern, full_context)
    if up_to_matches:
        return f"up to {max(map(int, up_to_matches))}% off"
    
    # Then look for standard percentage discounts
    percentage_pattern = r'(\d+)%\s+off'
    matches = re.findall(percentage_pattern, full_context)
    
    if matches:
        # Convert matches to integers and count frequencies
        discounts = list(map(int, matches))
        from collections import Counter
        discount_counts = Counter(discounts)
        
        # Get the most frequent discount
        most_common_discount = discount_counts.most_common(1)[0][0]
        return f"{most_common_discount}% off"
    
    return ""  # Return empty string if no discount found

class DataPaths:
    def __init__(self, folder_name: str, file_name: str, display_name: str = None):
        self.folder_name = folder_name  # e.g. "whiteFox"
        self.file_name = file_name      # e.g. "whitefoxboutique"
        self.display_name = display_name or file_name  # Name to use in output data
        
        # Input files
        self.brand_dir = f"newData/{self.folder_name}"
        self.raw_data = f"{self.brand_dir}/{self.file_name}Raw.json"
        
        # Output files
        self.sales_data = f"{self.brand_dir}/{self.file_name}PrevSales.csv"
        self.prophet_data = f"{self.brand_dir}/p_{self.file_name}.csv"
        self.validation_data = f"{self.brand_dir}/{self.file_name}Review.json"

def clean_data(paths: DataPaths, brand: str):
    # Load and clean data
    raw_data = load_raw_data(paths.raw_data)
    
    # Apply filters sequentially for promotional data
    promo_only = filter_non_promotional(raw_data)
    multi_context = filter_single_context(promo_only)
    cleaned_data = clean_promo_contexts(multi_context)
    
    # Create initial rows
    temp_rows = []  # For regular output file (sales only)
    prophet_rows = []  # For prophet file (including non-sales)
    
    # Get all timestamps that ended up as valid sales
    sale_timestamps = set()
    for timestamp, entry in cleaned_data.items():
        if determine_y_value(entry) == 1:
            sale_timestamps.add(timestamp)
    
    # Process all timestamps from raw data
    for timestamp, entry in raw_data.items():
        if timestamp in sale_timestamps:
            # This is a confirmed sale event
            event = determine_event(cleaned_data[timestamp]['promo_contexts'], brand)
            sitewide = 1 if cleaned_data[timestamp].get('sitewide', False) else 0
            discount = determine_discount(cleaned_data[timestamp]['promo_contexts'])
            
            # Convert timestamp to formatted date
            dt = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            formatted_date = dt.strftime('%d/%m/%Y')
            
            # Add to temp_rows (sales only)
            temp_rows.append({
                'brand': brand,
                'y': 1,
                'sitewide': sitewide,
                'start_date': formatted_date,
                'end_date': formatted_date,
                'event': event,
                'discount': discount,
                'snapshot': timestamp
            })
            
            # Add to prophet_rows
            prophet_rows.append({
                'y': 1,
                'snapshot': timestamp,
                'event': event,
                'sitewide': sitewide,
                'discount': discount
            })
        else:
            # This is a non-sale event (either non-promotional or filtered out)
            prophet_rows.append({
                'y': 0,
                'snapshot': timestamp,
                'event': '',
                'sitewide': 0,
                'discount': ''
            })
    
    # Create DataFrames
    df = pd.DataFrame(temp_rows)
    prophet_df = pd.DataFrame(prophet_rows)
    
    # Save prophet data with reordered columns
    prophet_columns = ['y', 'snapshot', 'event', 'sitewide', 'discount']
    prophet_df = prophet_df[prophet_columns]
    prophet_df = prophet_df.sort_values('snapshot')  # Sort by timestamp
    prophet_df.to_csv(paths.prophet_data, index=False)
    
    # Create and save aggregated version
    aggregated_df = aggregate_sales(df)
    columns = ['brand', 'y', 'event', 'sitewide', 'discount', 'start_date', 'end_date', 'snapshot']
    aggregated_df = aggregated_df[columns]
    aggregated_df.to_csv(paths.sales_data, index=False)
    
    # Save filtered entries for validation
    save_filtered_entries(raw_data, cleaned_data, paths.validation_data)

def save_filtered_entries(original_data: Dict, cleaned_data: Dict, output_file: str):
    """Save filtered entries to JSON for validation, excluding non-promotional entries"""
    # First get only promotional entries
    promo_entries = {k: v for k, v in original_data.items() if v['promotion']}
    
    # Find entries that were in promotional data but not in final cleaned data
    filtered_timestamps = set(promo_entries.keys()) - set(cleaned_data.keys())
    
    # Create list of filtered entries with reason
    filtered_entries = []
    for timestamp in filtered_timestamps:
        entry = promo_entries[timestamp]
        
        # Determine reason for filtering
        if len(entry['promo_contexts']) <= 1:
            reason = 'Single context'
        else:
            # Check if filtered due to buy-x-get-y patterns
            has_valid_contexts = False
            for contexts in entry['promo_contexts'].values():
                if any(not filter_promotional_patterns(ctx) for ctx in contexts):
                    reason = 'Contains buy-x-get-y pattern'
                    break
        
        filtered_entries.append({
            'timestamp': timestamp,
            'url': entry['url'],
            'reason_filtered': reason,
            'promo_contexts': entry['promo_contexts']
        })
    
    # Sort entries by timestamp
    filtered_entries.sort(key=lambda x: x['timestamp'])
    
    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(filtered_entries, f, indent=2)

def determine_y_value(row):
    # 1. Check sitewide with additional context validation
    if row.get('sitewide', False):
        # Get all contexts for analysis
        all_contexts = []
        for context_list in row.get('promo_contexts', {}).values():
            all_contexts.extend(context_list)
        
        # Convert to lowercase and join for pattern matching
        full_context = ' '.join(all_contexts).lower()
        
        # Check if contexts only contain basic sale keywords
        basic_sale_patterns = [
            r'sale',
            r'\d+%\s+off'
        ]
        
        # Remove basic sale patterns from the context
        cleaned_context = full_context
        for pattern in basic_sale_patterns:
            cleaned_context = re.sub(pattern, '', cleaned_context)
        
        # If there's meaningful content left after removing basic patterns,
        # or if it matches our other promotional patterns, mark as sale
        cleaned_context = cleaned_context.strip()
        if cleaned_context:  # If there's additional context beyond basic sale keywords
            return 1
    
    # 2. Check for major sale keywords in promo_contexts
    major_sale_keywords = [
        "black friday", "cyber monday", "afterpay day", "boxing day", 
        "flash sale", "summer sale", "winter sale", "singles day",
        "international womens day", "end of season", "mid season",
        "mid season sale", "stocktake sale",
        "eofy", "end of financial year", "birthday sale", "blackout",
        "labour day", "labor day", "4th of july", "fourth of july", 'hauliday',
        "friends and family", "outlet", "outlet sale", "men's outlet", "women's outlet"
    ]
    
    # Remove brand-specific sale keyword check
    
    # Combine all promo contexts for easier searching
    all_contexts = []
    for context_list in row.get('promo_contexts', {}).values():
        all_contexts.extend(context_list)
    
    # Convert to lowercase and join for pattern matching
    full_context = ' '.join(all_contexts).lower()
    
    # First check for major sale keywords
    if any(keyword in full_context for keyword in major_sale_keywords):
        return 1
    
    # Add new patterns for selected/sale items
    selected_patterns = [
        r"(?:up\s+to\s+)?\d+%\s+off\s+(?:selected|sale)\s+(?:lines|items|styles)",
        r"(?:selected|sale)\s+(?:lines|items|styles).*\d+%\s+off",
        r"save\s+(?:up\s+to\s+)?\d+%\s+on\s+(?:selected|sale)",
        r"extra\s+\d+%\s+off\s+(?:selected|sale)",
    ]
    
    # Add seasonal sale patterns
    seasonal_patterns = [
        r"(?:spring|summer|autumn|fall|winter)\s+(?:fits|essentials)",
        r"\d+%\s+off\s+(?:spring|summer|autumn|fall|winter)\s+(?:fits|essentials|collection|styles)",
        r"(?:spring|summer|autumn|fall|winter)\s+(?:collection|styles).*\d+%\s+off",
    ]
    
    # Check for selected/sale patterns first
    if any(re.search(pattern, full_context) for pattern in selected_patterns) or \
       any(re.search(pattern, full_context) for pattern in seasonal_patterns):
        return 1

    # Rest of the existing promotional patterns check
    # These patterns focus on clear sale indicators rather than code-related patterns
    promo_patterns = [
        # Site-wide sale indicators
        r"extra\s+\d+%?\s+off\s+all",
        r"\d+%\s+off\s+everything",
        r"off\s+all\s+(?:sale\s+)?styles",
        
        # Major promotional event indicators
        r"(?:biggest|major|massive)\s+(?:sale|savings?|discount)",
        r"up\s+to\s+\d+%\s+off",
        r"save\s+up\s+to\s+\d+%",
        
        # Time-sensitive sale language
        r"ends?\s+(?:today|tomorrow|soon|midnight)",
        r"last\s+(?:day|chance|call)",
        r"\d+\s+(?:hours|days)\s+(?:only|left)",
        r"limited\s+time\s+(?:only|offer)",
        
        # Additional site-wide sale indicators
        r"everything\s+(?:is\s+)?(?:on\s+)?sale",  # Matches "everything sale", "everything is on sale"
        r"site\s*wide\s+discount",
        r"(?:huge|mega|special|exclusive)\s+(?:sale|savings|discount|offer)",
        
        # Additional time-based patterns
        r"(?:today|weekend|week)\s+only",  # Matches "today only", "weekend only"
        r"final\s+(?:hours|days|chance|clearance)",
        r"(?:hurry|shop)\s+(?:now|before|while)",
        
        # Additional discount patterns
        r"minimum\s+\d+%\s+off",  # Matches "minimum 40% off"
        r"at\s+least\s+\d+%\s+off",  # Matches "at least 30% off"
        r"save\s+(?:big|more|extra)",
        r"further\s+reductions?",
        
        # Additional event patterns
        r"(?:clearance|outlet)\s+(?:sale|event)",
        r"(?:vip|members?)\s+(?:sale|event|preview)",
        r"(?:season|holiday)\s+(?:sale|savings)",
        
        # Additional promotional messaging
        r"don'?t\s+miss\s+(?:out|this)",
        r"prices\s+slashed",
        r"biggest\s+(?:deals?|savings?)\s+(?:of|ever)",
        
        # Additional time urgency patterns
        r"ending\s+(?:soon|tonight|tomorrow)",
        r"final\s+(?:sale|markdowns?|reductions?)",
        r"last\s+(?:chance|opportunity)",
        r"while\s+stocks?\s+last?s?",  # New pattern - matches both "while stock lasts" and "while stocks last"
        
        # Additional discount scope patterns
        r"across\s+(?:the\s+)?(?:site|store)",
        r"(?:store|site)\s*wide\s+savings",
        r"all\s+(?:items?|products?)\s+(?:reduced|discounted)"
    ]
    
    # Look for promotional patterns that indicate an active sale event
    pattern_matches = 0
    for pattern in promo_patterns:
        if re.search(pattern, full_context):
            pattern_matches += 1
            if pattern_matches >= 2:  # Require at least 2 different sale indicators
                return 1
    
    # 4. Default case - not a major sale
    return 0

def aggregate_sales(df):
    """Aggregate sales data by combining consecutive entries of the same event within 4 days"""
    # Convert snapshot timestamps to datetime for comparison
    df['start_dt'] = pd.to_datetime(df['snapshot'], format='%Y%m%d%H%M%S')
    df['end_dt'] = pd.to_datetime(df['snapshot'], format='%Y%m%d%H%M%S')
    
    # Sort by event and start date
    df = df.sort_values(['event', 'start_dt'])
    
    aggregated_rows = []
    current_group = None
    
    for _, row in df.iterrows():
        if current_group is None:
            current_group = {
                'brand': row['brand'],
                'y': row['y'],
                'event': row['event'],
                'sitewide': row['sitewide'],
                'discount': row['discount'],
                'start_dt': row['start_dt'],
                'end_dt': row['end_dt'],
                'snapshot': row['snapshot']
            }
            continue
        
        # Check if this row should be merged with current group
        same_event = row['event'] == current_group['event']
        dates_close = (row['start_dt'] - current_group['end_dt']).days <= 4
        
        if same_event and dates_close:
            # Update date range
            current_group['end_dt'] = max(current_group['end_dt'], row['end_dt'])
            # Update sitewide flag if either entry is sitewide
            current_group['sitewide'] = max(current_group['sitewide'], row['sitewide'])
            # Keep earliest snapshot
            current_group['snapshot'] = min(current_group['snapshot'], row['snapshot'])
        else:
            # Add current group to results and start new group
            aggregated_rows.append(current_group)
            current_group = {
                'brand': row['brand'],
                'y': row['y'],
                'event': row['event'],
                'sitewide': row['sitewide'],
                'discount': row['discount'],
                'start_dt': row['start_dt'],
                'end_dt': row['end_dt'],
                'snapshot': row['snapshot']
            }
    
    # Add last group
    if current_group:
        aggregated_rows.append(current_group)
    
    # Convert back to DataFrame
    result_df = pd.DataFrame(aggregated_rows)
    
    # Sort by datetime column before converting to string
    result_df = result_df.sort_values('start_dt')
    
    # Convert dates back to string formatI
    result_df['start_date'] = result_df['start_dt'].dt.strftime('%d/%m/%Y')
    result_df['end_date'] = result_df['end_dt'].dt.strftime('%d/%m/%Y')
    
    # Drop temporary columns
    result_df = result_df.drop(['start_dt', 'end_dt'], axis=1)
    
    return result_df[['brand', 'y', 'event', 'sitewide', 'discount', 'start_date', 'end_date', 'snapshot']]

if __name__ == "__main__":
    folder_name = "nutra"  # Directory name in newData/
    file_name = "nutraorganics"  # Base name of your json file (without 'Raw.json')
    display_name = "Nutra Organics"  # Optional: How you want the brand to appear in output
    
    paths = DataPaths(folder_name, file_name, display_name)
    clean_data(paths, display_name or file_name)
