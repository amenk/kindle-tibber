import os
import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
from flask import Flask, send_file
import io
from PIL import Image

# Initialize the Flask app
app = Flask(__name__)

# Read API key from environment variable
API_KEY = os.getenv("TIBBER_API_KEY")
if not API_KEY:
    raise ValueError("TIBBER_API_KEY environment variable not set.")

API_URL = "https://api.tibber.com/v1-beta/gql"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

query = """
query {
  viewer {
    homes {
      currentSubscription {
        priceInfo {
         current{
            total
            energy
            tax
            startsAt
          }        
          today {
            total
            startsAt
          }
          tomorrow {
            total
            startsAt
          }
        }
      }
    }
  }
}
"""

# Function to fetch and process the data
def fetch_data():
    response = requests.post(API_URL, headers=headers, json={"query": query})
    data = response.json()

    prices_today = data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]["today"]
    prices_tomorrow = data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]["tomorrow"]

    prices = prices_today + prices_tomorrow

    berlin_tz = pytz.timezone('Europe/Berlin')
    times = [datetime.fromisoformat(price["startsAt"]).astimezone(berlin_tz) for price in prices]
    values = [price["total"] for price in prices]

    times_extended = times + [times[-1] + timedelta(hours=1)]
    values_extended = values + [values[-1]]

    current_time = datetime.now().astimezone(berlin_tz)

    current_price = data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]["current"]["total"]
    
    return times_extended, values_extended, current_time, current_price

# Route to serve the image
@app.route('/image.png')
def serve_image():
    times_extended, values_extended, current_time, current_price = fetch_data()

    plt.figure(figsize=(8, 6))
    fig, ax = plt.subplots(figsize=(8, 6))  # Adjust the figure size

    values_extended_ct = [value * 100 for value in values_extended]

    plt.step(times_extended, values_extended_ct, where="post", label="Electricity Price", color="black")

    current_hour_index = None
    for i, time in enumerate(times_extended):
        if time <= current_time < time + timedelta(hours=1):
            current_hour_index = i
            break

    if current_hour_index is not None:
        plt.axvspan(times_extended[current_hour_index], times_extended[current_hour_index] + timedelta(hours=1), color="gray", alpha=0.3, label="Current Hour")

    plt.xticks(times_extended, [time.strftime("%H:%M") for time in times_extended], rotation=-90, color="black")
    plt.yticks(color="black")
    ax.set_ylim(0, 50)

    ax.axhline(
        y=32.74,  # The y-coordinate where the line will be drawn
        color='gray',  # Color of the line
        linestyle='--',  # Dashed line style
        linewidth=1.5,  # Thickness of the line
        label="32.74 ct/kWh"  # Add a label for the legend
    )

    plt.xlabel("Time", color="black")
    plt.ylabel("Price (ct/kWh)", color="black")
    plt.title("Tibber Electricity Prices", color="black")
    plt.grid(axis="x", linestyle="--", alpha=0.7, color="black")
    plt.legend(loc="upper left", frameon=False)

    current_date = current_time.strftime("%Y.%m.%d %H:%M:%S")
    plt.text(0.95, 0.01, f"Generated on: {current_date}", transform=plt.gca().transAxes, fontsize=10, color='gray', ha='right', va='bottom')
    
    current_price_ct = current_price * 100
    
    plt.text(
       0.5, 0.2,  # Positioning the text (x, y), adjust x and y as necessary
       f"{current_price_ct:.2f} ct/kWh",  # Text to display
       transform=ax.transAxes,  # Use axis fraction (0.0 to 1.0) for positioning
       ha='center',  # Center the text horizontally
       va='bottom',  # Place text below the top of the plot
       fontsize=28,  # Font size
       color='black',  # Color of the text (light gray)
       weight='bold'  # Make the font bold for visibility
    )


    # Save the figure to a BytesIO object (in-memory)
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png', dpi=150)
    img_io.seek(0)

    # Load the image using PIL for resizing and rotation
    img = Image.open(img_io)

    # Rotate and resize to fit Kindle 4 resolution (600x800)
    img = img.rotate(90, expand=True)  # Rotate the image by 90 degrees
    img = img.resize((600, 800))  # Resize to 600x800 pixels (Kindle 4 resolution)
    img = img.convert('L')
    
    # Save the modified image back into the BytesIO object
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    # Return the image as a response
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

