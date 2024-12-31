import os
import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz  # Import pytz for time zone handling

# Read API key from the environment
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

response = requests.post(API_URL, headers=headers, json={"query": query})
data = response.json()

prices_today = data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]["today"]
prices_tomorrow = data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]["tomorrow"]

# Combine today and tomorrow
prices = prices_today + prices_tomorrow

# Get Europe/Berlin time zone
berlin_tz = pytz.timezone('Europe/Berlin')

# Convert start times into local time (Europe/Berlin)
times = [datetime.fromisoformat(price["startsAt"]).astimezone(berlin_tz) for price in prices]
values = [price["total"] for price in prices]

# Extend times by one hour for the step diagram
times_extended = times + [times[-1] + timedelta(hours=1)]
values_extended = values + [values[-1]]  # Repeat the last price for the final step

# Identify current time for marking (convert to Europe/Berlin)
current_time = datetime.now().astimezone(berlin_tz)

current_hour_index = None
for i, time in enumerate(times):
    if time <= current_time < time + timedelta(hours=1):
        current_hour_index = i
        break

# Plot data as a step diagram
plt.figure(figsize=(8, 6))
plt.step(times_extended, values_extended, where="post", label="Electricity Price", color="black")

# Highlight the current hour
if current_hour_index is not None:
    plt.axvspan(
        times[current_hour_index], 
        times[current_hour_index] + timedelta(hours=1),
        color="gray", alpha=0.3, label="Current Hour"
    )

# Customize for grayscale display
plt.xticks(times, [time.strftime("%H:%M") for time in times], rotation=45, color="black")
plt.yticks(color="black")
plt.xlabel("Time", color="black")
plt.ylabel("Price (€/kWh)", color="black")
plt.title("Tibber Electricity Prices (Step Diagram)", color="black")
plt.grid(axis="x", linestyle="--", alpha=0.7, color="black")
plt.legend(loc="upper left", frameon=False)

# Add current date
current_date = current_time.strftime("%Y-%m-%d")
plt.text(0.95, 0.01, f"Generated on: {current_date}", 
         transform=plt.gca().transAxes, fontsize=10, color='gray',
         ha='right', va='bottom')

plt.tight_layout()

# Save to PNG
plt.savefig("image.png", dpi=150, bbox_inches="tight")
print("Chart saved as image.png")

