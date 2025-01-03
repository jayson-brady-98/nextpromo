import json
import csv
import re
from typing import Dict, List
import pandas as pd
from datetime import datetime

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
        'gift card',
        'e-gift card', 
        'products',
        'accessories',
        'all sale',
        'best sellers',
        'gifts for him',
        'gifts for her',
        'trending',
        'products under'
    ]
    
    # Separate gender keywords
    gender_keywords = ['womens', "women's", 'mens', "men's"]
    
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
        # Add Friends and Family pattern at the top
        r'friends?\s*(?:&|and)\s*family',  # Matches "Friends & Family" or "Friend and Family" variations - specific to Gymshark
        
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
        
        # Threshold-based offers
        r'(?:orders?|purchases?|spend).*(?:over|above)?\s*[\$£€]?\d+',  # Matches spending threshold offers
        r'\d+%\s*off.*(?:orders?|purchases?).*(?:over|above)?\s*[\$£€]?\d+',  # Combined threshold discounts
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
        
        # Only keep entry if it still has multiple keywords after filtering
        if len(cleaned_contexts) > 1:
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
        # Add other priority mappings as needed
    }
    
    # Check if any priority keywords were used
    for keyword, event_name in priority_keywords.items():
        if keyword in keywords_used:
            return event_name
    
    # If no priority keywords found, continue with existing logic...
    all_contexts = []
    for context_list in promo_contexts.values():
        all_contexts.extend(context_list)
    
    # Convert to lowercase and join for pattern matching
    full_context = ' '.join(all_contexts).lower()
    brand = brand.lower()
    
    # Map brand-specific sale to Generic Sale
    if brand and f"{brand} sale" in full_context:
        return "Generic Sale"
    
    # Special case for summer/winter sale
    if "summer sale" in full_context or "winter sale" in full_context:
        return "Summer/Winter Sale"
    
    # Check for other major sale keywords
    major_sale_keywords = [
        "black friday", "cyber monday", "afterpay day", "boxing day", 
        "flash sale", "singles day", "international womens day", 
        "end of season", "mid season", "eofy", "end of financial year",
        "birthday sale", "blackout", "labour day", "labor day",
        "4th of july", "fourth of july"
    ]
    
    # Return first matching keyword found
    for keyword in major_sale_keywords:
        if keyword in full_context:
            return keyword.title()  # Capitalize first letter of each word
    
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

def clean_data(input_file: str, output_file: str, validation_file: str, brand: str):
    # Load and clean data
    raw_data = load_raw_data(input_file)
    
    # Apply filters sequentially
    promo_only = filter_non_promotional(raw_data)
    multi_context = filter_single_context(promo_only)
    cleaned_data = clean_promo_contexts(multi_context)
    
    # Create initial CSV with all cleaned entries and columns in desired order
    temp_rows = []
    for timestamp, entry in cleaned_data.items():
        y_value = determine_y_value(entry)
        if y_value == 1:  # Only include rows where y = 1
            event = determine_event(entry['promo_contexts'], brand)
            sitewide = 1 if entry.get('sitewide', False) else 0
            discount = determine_discount(entry['promo_contexts'])
            temp_rows.append({
                'brand': brand,
                'y': y_value,
                'sitewide': sitewide,
                'start_date': timestamp,  # We'll rename this in aggregation
                'end_date': timestamp,    # We'll rename this in aggregation
                'event': event,
                'discount': discount,
                'snapshot': timestamp     # Add snapshot column
            })
    
    # Convert to DataFrame with columns already in correct order
    df = pd.DataFrame(temp_rows)
    
    # Aggregate the sales data
    aggregated_df = aggregate_sales(df)
    
    # Reorder columns to put brand first and include snapshot at the end
    columns = ['brand', 'y', 'event', 'sitewide', 'discount', 'start_date', 'end_date', 'snapshot']
    aggregated_df = aggregated_df[columns]
    
    # Write aggregated data to CSV
    aggregated_df.to_csv(output_file, index=False)
    
    # Save filtered entries for validation
    save_filtered_entries(raw_data, cleaned_data, validation_file)

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
    # Get brand name from the function parameters
    brand_name = row.get('brand', '').lower()
    
    # 1. First check if sitewide is true
    if row.get('sitewide', False):
        return 1
        
    # 2. Check for major sale keywords in promo_contexts
    major_sale_keywords = [
        "black friday", "cyber monday", "afterpay day", "boxing day", 
        "flash sale", "summer sale", "winter sale", "singles day",
        "international womens day", "end of season", "mid season",
        "eofy", "end of financial year", "birthday sale", "blackout",
        "labour day", "labor day", "4th of july", "fourth of july"
    ]
    
    # Add brand-specific sale keyword if brand is available
    if brand_name:
        major_sale_keywords.append(f"{brand_name} sale")
    
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
    # Convert dates to datetime for comparison
    df['start_dt'] = pd.to_datetime(df['start_date'], format='%Y%m%d%H%M%S')
    df['end_dt'] = pd.to_datetime(df['end_date'], format='%Y%m%d%H%M%S')
    
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
    
    # Convert dates back to string format
    result_df['start_date'] = result_df['start_dt'].dt.strftime('%d/%m/%Y')
    result_df['end_date'] = result_df['end_dt'].dt.strftime('%d/%m/%Y')
    
    # Drop temporary columns
    result_df = result_df.drop(['start_dt', 'end_dt'], axis=1)
    
    return result_df[['brand', 'y', 'event', 'sitewide', 'discount', 'start_date', 'end_date', 'snapshot']]

if __name__ == "__main__":
    input_file = "gymsharkRaw.json"
    output_file = "gymsharkCleaned.csv"
    validation_file = "gymsharkForReview.json"
    brand = "Gymshark"
    clean_data(input_file, output_file, validation_file, brand)
