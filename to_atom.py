#!/usr/bin/env python3
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import datetime
import sys
from urllib.parse import quote


def format_xml(element):
    """Format XML with proper indentation"""
    rough_string = ET.tostring(element, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ").replace(
        '<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-8"?>'
    )


def json_to_atom(
    json_data,
    feed_title="Nature Observations Feed",
    feed_id="https://example.com/feed",
    author_name="Feed Generator",
    feed_updated=None,
):
    """
    Convert JSON data to Atom feed

    Args:
        json_data (dict): The parsed JSON data
        feed_title (str): The title of the Atom feed
        feed_id (str): The unique ID of the feed
        author_name (str): Name of the feed author/generator
        feed_updated (str): Update time for the feed, defaults to current time

    Returns:
        str: Formatted XML string of the Atom feed
    """

    # Create the root element with namespaces
    atom = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")

    # Add feed metadata
    ET.SubElement(atom, "title").text = feed_title
    ET.SubElement(atom, "id").text = feed_id

    # Use the current time if no update time provided
    if feed_updated is None:
        feed_updated = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.SubElement(atom, "updated").text = feed_updated

    # Add author information
    author = ET.SubElement(atom, "author")
    ET.SubElement(author, "name").text = author_name

    # Process each observation result as an entry
    for item in json_data.get("results", []):
        entry = ET.SubElement(atom, "entry")

        # Create unique ID for the entry using iNaturalist URL format
        obs_id = item.get("id")
        inaturalist_url = f"https://www.inaturalist.org/observations/{obs_id}"
        ET.SubElement(entry, "id").text = inaturalist_url

        # Use the place_guess as the entry title instead of observation ID
        observation_time = item.get("time_observed_at")
        place = item.get("place_guess", "Unknown location")
        title_text = f"Brown Pelican at {place}"
        ET.SubElement(entry, "title").text = title_text
        ET.SubElement(entry, "updated").text = observation_time

        # Add location information in the content
        content = ET.SubElement(entry, "content")
        content.set("type", "html")

        # Format the content with HTML
        html_content = f"<div><p>Location: {item.get('place_guess', 'Unknown')}</p>"

        # Add coordinates if available and link to Google Maps
        if item.get("geojson") and item.get("geojson").get("coordinates"):
            coords = item.get("geojson").get("coordinates")
            lat, lon = coords[1], coords[0]
            google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            html_content += f'<p>Coordinates: <a href="{google_maps_url}" target="_blank">{lat}, {lon}</a></p>'

        # Add photos without using a list
        if item.get("observation_photos"):
            html_content += "<p>Photos:</p>"
            for photo_data in item.get("observation_photos"):
                if photo_data.get("photo") and photo_data.get("photo").get("url"):
                    photo_url = (
                        photo_data.get("photo")
                        .get("url")
                        .replace("square.jpg", "large.jpg")
                    )
                    photo_attribution = photo_data.get("photo").get("attribution", "")
                    html_content += (
                        f'<div><img src="{photo_url}" alt="Observation photo"/>'
                    )
                    html_content += f"<br/>{photo_attribution}</div>"

        html_content += "</div>"
        content.text = html_content

        if item.get("observation_photos"):
            for photo_data in item.get("observation_photos"):
                if photo_data.get("photo") and photo_data.get("photo").get("url"):
                    photo_url = (
                        photo_data.get("photo")
                        .get("url")
                        .replace("square.jpg", "large.jpg")
                    )
                    # Create a link with the appropriate relationship
                    link = ET.SubElement(entry, "link")
                    link.set("rel", "enclosure")
                    link.set("href", photo_url)
                    link.set("type", "image/jpeg")

        # Add a link to the iNaturalist observation page
        link = ET.SubElement(entry, "link")
        link.set("rel", "alternate")
        link.set("href", inaturalist_url)

        # Add location as a category
        if item.get("place_guess"):
            category = ET.SubElement(entry, "category")
            category.set("term", quote(item.get("place_guess")))
            category.set("label", item.get("place_guess"))

    # Return formatted XML
    return format_xml(atom)


def main():
    """
    Main function to process JSON from stdin or file and output Atom feed
    """
    # Read from stdin if no file is provided, otherwise read from file
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Generate feed with current timestamp
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Print the Atom feed
    print(
        json_to_atom(
            data,
            feed_title="California Brown Pelican Sightings",
            feed_id="https://example.com/observations/feed",
            author_name="Observation Feed Generator",
            feed_updated=now,
        )
    )


if __name__ == "__main__":
    main()
