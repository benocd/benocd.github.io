import os
import json
import exifread
from opencage.geocoder import OpenCageGeocode

# ========== CONFIG ==========
FOLDER = './'
OUTPUT = 'images.json'
OPENCAGE_API_KEY = 'bdc2394b319445efb6737ecfaf857032'  # replace with your OpenCage key
# ============================

geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

def dms_to_decimal(dms, ref):
    degrees, minutes, seconds = [float(val.num) / float(val.den) for val in dms]
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    return -decimal if ref in ['S', 'W'] else decimal

def extract_metadata(filepath):
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f, details=False)

    date = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
    date_str = str(date) if date else 'Unknown Date'

    gps_lat = tags.get('GPS GPSLatitude')
    gps_lat_ref = tags.get('GPS GPSLatitudeRef')
    gps_lon = tags.get('GPS GPSLongitude')
    gps_lon_ref = tags.get('GPS GPSLongitudeRef')

    lat = lng = None
    place = city = country = None

    if gps_lat and gps_lon and gps_lat_ref and gps_lon_ref:
        lat = dms_to_decimal(gps_lat.values, gps_lat_ref.values)
        lng = dms_to_decimal(gps_lon.values, gps_lon_ref.values)
        results = geocoder.reverse_geocode(lat, lng, no_annotations=1, language='en')
        if results:
            comp = results[0].get('components', {})
            place = comp.get('attraction') or comp.get('building') or comp.get('neighbourhood') or comp.get('suburb') or comp.get('road')
            city = comp.get('city') or comp.get('town') or comp.get('village') or comp.get('municipality')
            country = comp.get('country')

    make = str(tags.get('Image Make', '')).strip()
    model = str(tags.get('Image Model', '')).strip()
    camera = f"{make} {model}".strip() if make or model else None

    return {
        "url": os.path.join(FOLDER, os.path.basename(filepath)).replace("\\", "/"),
        "date": date_str,
        "lat": round(lat, 6) if lat else None,
        "lng": round(lng, 6) if lng else None,
        "place": place,
        "city": city,
        "country": country,
        "camera": camera
    }

def main():
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff'}
    images = []

    for filename in os.listdir(FOLDER):
        ext = os.path.splitext(filename)[1].lower()
        if ext in image_extensions:
            path = os.path.join(FOLDER, filename)
            try:
                meta = extract_metadata(path)
                images.append(meta)
                print(f"✔ Processed: {filename}")
            except Exception as e:
                print(f"✖ Failed: {filename} — {e}")

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(images, f, indent=2)

    print(f"\n✅ Done. Metadata for {len(images)} images written to {OUTPUT}")

if __name__ == '__main__':
    main()
