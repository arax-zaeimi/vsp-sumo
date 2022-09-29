import time
import geocoder
import requests


def geocodeByNominatim(address):
    # https://nominatim.openstreetmap.org/search?q=4545+walkley&format=json&addressdetails=1&limit=1&polygon_svg=1
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': '1',
        'limit': '20'}
    response = requests.get(url, params=params)
    # Because the geocode is limited, we need to pause for 1 second at least.
    time.sleep(1)
    if response.ok and response.status_code == 200:
        results = response.json()
        # for result in results:
        #     print(result['lat'], result['lon'], result['display_name'])
        if len(results) > 0:
            return results[0]['lat'], results[0]['lon'], results[0]['display_name']
        return None


def geocodeByOsm(address):
    with requests.Session() as session:
        home = geocoder.osm(address, session=session)
        return home


if __name__ == "__main__":
    lat, lon, display_name = geocodeByNominatim('4545 walkley montreal')
    print(f"{lat}, {lon}, display_name: {display_name}")
