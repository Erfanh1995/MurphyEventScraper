import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import dateutil.parser
import re
import os
import pytz

def generate_ics_file(event_details):
    """Creates an .ics file for a single event."""
    c = Calendar()
    e = Event()

    e.name = event_details['title']
    e.begin = event_details['datetime']
    e.location = event_details['location']
    
    # Add the URL to the description for easy access
    if event_details['link']:
        e.description = f"For more details, visit: {event_details['link']}"

    c.events.add(e)

    # Create a valid filename from the event title
    # Remove invalid characters and limit length
    filename_base = re.sub(r'[^\w\s-]', '', event_details['title']).strip()
    filename_base = re.sub(r'[-\s]+', '-', filename_base)
    filename = f"{filename_base[:50]}.ics"
    
    # Create an 'events' directory if it doesn't exist
    if not os.path.exists('events'):
        os.makedirs('events')
        
    filepath = os.path.join('events', filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(c)
        print(f"Successfully created calendar file: {filepath}")
    except IOError as err:
        print(f"Error writing file {filepath}: {err}")


def scrape_page(url):
    """Scrapes a single page for event data."""
    events_on_page = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all event entries on the page.
    # The structure has changed; each event is now within 'div' with class 'views-field-title'
    event_containers = soup.find_all('div', class_='views-field-title')

    if not event_containers:
        print("Could not find any event containers on the page. The website structure may have changed.")
        return []

    # Define the timezone for the events, as the source HTML is misleading.
    # Use 'America/Chicago' for Central Time Zone.
    central_tz = pytz.timezone("America/Chicago")

    for item in event_containers:
        title = "No Title Found"
        link = ""
        datetime_str = ""
        location = "No Location Found"

        # Find the title and the embedded link from the <a> tag
        link_element = item.find('a')
        if link_element:
            href = link_element.get('href', '')
            # Construct full URL if href is relative
            if href.startswith('/'):
                link = "https://murphy.tulane.edu" + href
            else:
                link = href
            
            # Title is inside a span with class 'font-bold' within the link
            title_span = link_element.find('span', class_='font-bold')
            if title_span:
                title = title_span.text.strip()
            else: # Fallback if the inner span is not found
                title = link_element.text.strip()

        # Find the date and time from the <time> tag's datetime attribute
        time_tag = item.find('time')
        if time_tag and time_tag.has_attr('datetime'):
            datetime_str = time_tag['datetime']

        # Find the location from the span with class 'location'
        location_element = item.find('span', class_='location')
        if location_element:
            location = location_element.text.strip()
            
        # Parse the date string into a datetime object
        try:
            # We must have a datetime to create a calendar event
            if datetime_str:
                # The website incorrectly marks local time with a 'Z' (UTC marker).
                # We need to parse it as a naive datetime and then attach the correct
                # timezone (America/Chicago).

                # 1. Parse the string, ignoring the trailing 'Z' to create a naive datetime object.
                naive_dt_str = datetime_str.rstrip('Zz')
                parsed_naive_datetime = dateutil.parser.parse(naive_dt_str)

                # 2. Localize the naive datetime object to the Central timezone.
                aware_datetime = central_tz.localize(parsed_naive_datetime)

                events_on_page.append({
                    'title': title,
                    'link': link,
                    'datetime': aware_datetime, # Use the timezone-aware object
                    'location': location
                })
            else:
                # If no datetime found, we can't create an event, so we'll note it and skip.
                if title != "No Title Found": # Only warn if we actually found an event title
                    print(f"Warning: Could not find date-time for event '{title}'")

        except (ValueError, TypeError):
            print(f"Warning: Could not parse date-time string: '{datetime_str}' for event '{title}'")
            
    return events_on_page


def main():
    """Main function to crawl all pages and generate files."""
    base_url = "https://murphy.tulane.edu/events/upcoming-events"
    all_events = []
    
    # First, get the main page to identify pagination
    try:
        print(f"Fetching base page: {base_url}")
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch the main events page. Exiting. Error: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Scrape the first page
    print("Scraping page 1...")
    all_events.extend(scrape_page(base_url))
    
    # Find pagination links to discover all pages
    # The pager links are in a 'li' with class 'pager__item'
    page_links = set() # Use a set to avoid duplicate links
    pager_items = soup.select('li.pager__item a')
    for link in pager_items:
        href = link.get('href')
        if href and href.startswith('?page='):
            full_url = base_url + href
            page_links.add(full_url)
            
    # Scrape the rest of the pages
    if page_links:
        print(f"Found {len(page_links)} additional pages to scrape.")
        for i, page_url in enumerate(sorted(list(page_links))):
             print(f"Scraping page {i+2}/{len(page_links)+1}: {page_url}")
             all_events.extend(scrape_page(page_url))
    else:
        print("No additional pages found.")

    print(f"\nFound a total of {len(all_events)} events.")

    if not all_events:
        print("No events were found to process.")
        return
        
    # Generate an .ics file for each event
    print("\nGenerating calendar files...")
    for event in all_events:
        generate_ics_file(event)
        
    print("\nProcessing complete.")


if __name__ == "__main__":
    main()




