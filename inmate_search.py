# TODO: Implement inmate search and data extraction after login
# This file will contain functions to:
# - Navigate to the search page
# - Submit search queries
# - Parse inmate details (cell location, custody duration, release status)

from bs4 import BeautifulSoup
from datetime import datetime
import re

def parse_inmate_search_results(html, today=None):
    """
    Parse PBSO inmate search results HTML and extract booking info.
    Returns a list of dicts with keys: booking_number, booking_date, release_date, custody_duration, facility.
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    if today is None:
        today = datetime.today()
    # Find all booking blocks by looking for 'Booking Number:'
    for booking_div in soup.find_all('div', style=re.compile(r'border:1px solid black')):
        booking_number = None
        booking_date = None
        release_date = None
        facility = None
        custody_duration = None
        # Booking Number
        bn = booking_div.find('strong', string=re.compile('Booking Number'))
        if bn and bn.next_sibling:
            a = bn.find_next('a')
            if a:
                booking_number = a.text.strip()
        # Booking Date/Time
        bd = booking_div.find('strong', string=re.compile('Booking Date/Time'))
        if bd and bd.next_sibling:
            dt_text = bd.next_sibling
            if isinstance(dt_text, str):
                booking_date_str = dt_text.strip()
                try:
                    booking_date = datetime.strptime(booking_date_str, '%m/%d/%Y %H:%M')
                except Exception:
                    booking_date = None
        # Facility (if present)
        fac = booking_div.find('strong', string=re.compile('Facility'))
        if fac and fac.parent:
            facility = fac.parent.text.replace('Facility:', '').strip()
        # Release Date
        rel = booking_div.find('strong', string=re.compile('Release Date'))
        if rel and rel.parent:
            rel_text = rel.parent.text.replace('Release Date:', '').strip()
            if rel_text and 'N/A' not in rel_text:
                # Try to extract date and time
                m = re.search(r'(\d{2}/\d{2}/\d{2,4})', rel_text)
                t = re.search(r'Time:?\s*([0-9:]+)', rel_text)
                if m:
                    rel_date_str = m.group(1)
                    rel_time_str = t.group(1) if t else '00:00'
                    try:
                        # Handle 2-digit or 4-digit year
                        if len(rel_date_str.split('/')[-1]) == 2:
                            rel_date_fmt = '%m/%d/%y %H:%M'
                        else:
                            rel_date_fmt = '%m/%d/%Y %H:%M'
                        release_date = datetime.strptime(rel_date_str + ' ' + rel_time_str, rel_date_fmt)
                    except Exception:
                        release_date = None
        # Custody duration
        if booking_date and booking_number:
            if release_date:
                custody_duration = release_date - booking_date
            else:
                custody_duration = today - booking_date
            results.append({
                'booking_number': booking_number,
                'booking_date': booking_date,
                'release_date': release_date,
                'custody_duration': custody_duration,
                'facility': facility
            })
    return results
