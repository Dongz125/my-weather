# MyWeather

MyWeather is a project built with Python and Streamlit. A user copies latitude and longitude from Google Maps, submits them directly, and receives a resolved place name, current weather, an interactive weather map, OpenWeather air-quality data, and a five-day forecast. Optional local accounts let users keep a personal list of locations. Google Maps is used only to copy coordinates; no Google Maps API key is required.

The application uses ordinary OpenWeather endpoints available to free accounts. It does not subscribe to or enable paid services.

## Feature checklist

- [x] Text inputs with numeric, finite-value, latitude, and longitude validation
- [x] Reverse geocoding to city, optional state, and ISO 3166-1 alpha-2 country code
- [x] Current temperature, feels-like temperature, humidity, wind, Vietnamese description, and icon
- [x] Interactive Folium map with a marker
- [x] OpenWeather Maps 1.0 temperature, wind, cloud, and precipitation overlays
- [x] OpenWeather 1–5 AQI with the correct Good → Very Poor labels
- [x] PM2.5, PM10, CO, NO₂, O₃, SO₂, plus optional NO and NH₃ concentrations
- [x] Five-day/three-hour forecast charts for temperature, humidity, and wind
- [x] Location-local forecast times using the UTC offset returned by OpenWeather
- [x] Lightweight custom weather summary embedded with `st.iframe`
- [x] API response caching, timeouts, partial-result handling, and safe errors
- [x] Mocked tests that never call or consume the live API
- [x] Interactive technical walkthrough notebook with sanitized examples
- [x] Local account registration and sign-in with Argon2 password hashes
- [x] Per-user saved locations backed by SQLite
- [x] Load and delete controls with account-level ownership isolation

The summary widget is explicitly labeled custom. The official OpenWeather city widget is not embedded because this application has a coordinate-first workflow, while a local summary avoids unnecessary third-party script execution.

## Project structure

```text
MyWeather/
├── app.py                         # Streamlit entry point and workflow coordinator
├── services/
│   ├── api_client.py              # HTTP timeout and safe status handling
│   ├── weather_service.py         # Current weather parsing/client
│   ├── geocoding_service.py       # Reverse-geocoding parsing/client
│   ├── air_quality_service.py     # AQI and pollutant parsing/client
│   ├── forecast_service.py        # Forecast parsing and local-time conversion
│   ├── auth_service.py            # Registration and Argon2 authentication
│   └── saved_location_service.py  # Ownership-safe location persistence
├── views/
│   ├── dashboard.py               # Reusable Streamlit UI sections
│   ├── weather_map.py             # Folium marker and Weather Maps tiles
│   ├── account.py                 # Sign-in, registration, and logout UI
│   └── saved_locations.py         # Save, load, and delete controls
├── data/
│   ├── database.py                # SQLite schema and connections
│   └── myweather.db               # Local runtime data (generated, Git-ignored)
├── core/
│   ├── validation.py              # Coordinate validation
│   └── formatting.py              # Safe display formatting
├── config/
│   └── settings.py                # Defaults and API-key loading
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── notebooks/
│   └── MyWeather.ipynb
└── tests/
    ├── test_accounts.py
    ├── test_validation.py
    └── test_weather_services.py
```

## Requirements

- Python 3.11 or newer
- An OpenWeather account and API key
- Internet access while using live weather features
- Write access to the project `data/` directory for local account persistence

The project was locally verified with Python 3.12.0. Dependencies are listed in `requirements.txt`.

## Create a virtual environment

Clone or download the project, open a terminal in its root directory, and use the commands for your operating system.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, either use Command Prompt or review your local execution policy rather than weakening a managed system policy.

### Windows Command Prompt

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Get an OpenWeather API key

1. [Create an OpenWeather account](https://home.openweathermap.org/users/sign_up).
2. Verify the account email.
3. Open the **API keys** tab in the account dashboard.
4. Copy the default key or generate a dedicated key for this project.
5. Wait for activation if a newly created key initially returns HTTP 401. Activation is controlled by OpenWeather and may not be immediate.

Do not paste a real key into source code, this README, a notebook output, screenshots, issues, or commits.

## Configure the API key safely

Choose one of the following methods. Streamlit secrets take precedence over environment variables.

### Option A: Streamlit secrets (recommended)

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:

```toml
OPENWEATHER_API_KEY = "your_real_api_key"
```

The real `.streamlit/secrets.toml` is ignored by Git.

### Option B: environment variable

PowerShell:

```powershell
$env:OPENWEATHER_API_KEY = "your_real_api_key"
```

Command Prompt:

```bat
set OPENWEATHER_API_KEY=your_real_api_key
```

macOS/Linux:

```bash
export OPENWEATHER_API_KEY="your_real_api_key"
```

## Run the application

With the virtual environment active and the API key configured:

```bash
streamlit run app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`. The app does not refresh automatically: API calls happen after the coordinate form is submitted, and successful results are cached for a bounded time.

## Local user accounts and saved locations

Weather lookup remains available without an account. Use the sidebar to register or sign in when you want to save locations.

- Usernames contain 3–32 letters, numbers, dots, hyphens, or underscores and are unique without regard to case.
- Passwords contain 8–128 characters with at least one letter and one number.
- Passwords are stored only as salted Argon2id hashes; plaintext passwords are never written to the database.
- After a successful weather lookup, select **Save _city_** to add the resolved location to the signed-in account.
- Use **Load** in the sidebar to fetch weather for a saved location or **Delete** to remove it.
- Each account can store up to 50 distinct coordinate pairs.

SQLite tables are created automatically in `data/myweather.db` on startup. The application always uses this local path. The database file and its journal files are ignored by Git.

## Obtain coordinates from Google Maps

1. Open [Google Maps](https://maps.google.com/) and find the required location.
2. On desktop, right-click the exact point. On mobile, press and hold to drop a pin.
3. Select or tap the coordinate pair to copy it.
4. Paste the first number into **Latitude** and the second into **Longitude**.
5. Select **Look up weather**.

Example for Ho Chi Minh City: latitude `10.8231`, longitude `106.6297`. Valid latitude is -90 through 90; valid longitude is -180 through 180.

## API endpoints and calling order

When the form is submitted, the app validates coordinates before any network request, then calls these services independently in the following logical order:

1. Reverse Geocoding: `GET https://api.openweathermap.org/geo/1.0/reverse`
   - `lat`, `lon`, `limit=1`, `appid`
2. Current Weather: `GET https://api.openweathermap.org/data/2.5/weather`
   - `lat`, `lon`, `appid`, `units=metric`, `lang=vi`
3. Air Pollution: `GET https://api.openweathermap.org/data/2.5/air_pollution`
   - `lat`, `lon`, `appid`
4. 5-day/3-hour Forecast: `GET https://api.openweathermap.org/data/2.5/forecast`
   - `lat`, `lon`, `appid`, `units=metric`
5. Map tiles are requested by the browser while the map is visible:
   - `https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={API_KEY}`

The clients are independent, so a failed forecast request does not discard successfully loaded current weather. The implemented Weather Maps 1.0 identifiers are the currently documented `temp_new`, `wind_new`, `clouds_new`, and `precipitation_new`.

Official documentation:

- [Geocoding API](https://openweathermap.org/api/geocoding-api)
- [Current Weather API](https://openweathermap.org/api/current)
- [Air Pollution API](https://openweathermap.org/api/air-pollution)
- [5-day/3-hour Forecast](https://openweathermap.org/api/forecast5)
- [Weather Maps 1.0](https://openweathermap.org/api/weathermaps)

## Air-quality interpretation

The displayed score is OpenWeather's AQI, **not the US EPA AQI**:

| OpenWeather AQI | Label |
|---:|---|
| 1 | Good |
| 2 | Fair |
| 3 | Moderate |
| 4 | Poor |
| 5 | Very Poor |

All displayed pollutant concentrations are in µg/m³, as documented by the provider.

## Run the notebook

Start Jupyter from the project root:

```bash
jupyter notebook notebooks/MyWeather.ipynb
```

The notebook walks through the architecture, API setup, sanitized response processing, Streamlit workflow, tests, forecast visualization, and operational limitations. Most demonstrations use local sample payloads, so a real API key is not needed to run them.

## Run tests and checks

The tests mock `requests.get`; they do not contact OpenWeather.

```bash
python -m pytest -q
python -m compileall -q .
```

The completed project currently has 48 passing tests covering:

- valid, non-numeric, non-finite, and out-of-range coordinates;
- empty and valid reverse-geocoding responses;
- successful current-weather parsing and missing optional fields;
- all five OpenWeather AQI labels and pollutant parsing;
- forecast timezone conversion;
- correct request parameters;
- safe handling of timeout, invalid JSON, HTTP 401, 404, 429, and 5xx;
- Argon2 password hashing, registration validation, and generic login failures;
- case-insensitive unique usernames;
- saved-location duplication rules, account isolation, deletion, and foreign-key cascades.

## Common errors

### `OPENWEATHER_API_KEY` is not configured

Create `.streamlit/secrets.toml` from its example or set the environment variable in the same shell used to launch Streamlit. Restart Streamlit after changing configuration.

### HTTP 401 / rejected API key

- Check for missing characters or surrounding quotation marks in an environment variable.
- Confirm the account email is verified.
- A new key can require an activation delay. Wait and retry later.
- Confirm the key was not revoked in the OpenWeather dashboard.

The app deliberately does not display the provider's raw error text because a request URL or diagnostic could expose credentials.

### HTTP 429 / rate limit reached

Wait before retrying. Do not repeatedly refresh the page. MyWeather caches network results and has no automatic refresh loop, but limits are account-wide and other applications may use the same key.

### HTTP 404

The requested resource or location data was not found. Verify the coordinates and try a nearby point.

### Timeout, connection error, or HTTP 5xx

Check the local connection and OpenWeather service status, then retry later. Requests have a 10-second timeout so the UI does not hang indefinitely.

### Blank weather map layer

Confirm that the API key is active and permitted to use Weather Maps 1.0. Base-map tiles may load even when OpenWeather rejects its overlay. Browser content blockers or network policy can also prevent tile requests.

### SQLite database cannot be opened

Ensure the process can create and write files in the local `data/` directory. The directory is created automatically when permissions allow it.

## Security and provider limitations

- Real credentials are never hardcoded. `.env` and `.streamlit/secrets.toml` are ignored by Git. The project provides only the Streamlit secrets example to avoid duplicate key files.
- Passwords are processed with Argon2id and only password hashes are stored. Database queries use bound parameters rather than string-built SQL.
- Saved-location reads and deletes always include the authenticated user ID, preventing one account from operating on another account's rows.
- Exceptions shown in the UI use fixed messages and do not include raw request URLs, keys, or provider response text.
- Caching reduces calls but does not remove account-level quota limits.
- OpenWeather data accuracy, update frequency, coverage, and availability are provider-controlled.
- `city.timezone` is a fixed UTC offset, not an IANA timezone name. The app correctly uses the supplied offset but cannot infer future daylight-saving transitions from it.
- Optional response fields can be absent; the UI displays `N/A` instead of claiming data exists.
- The application never claims that an API request succeeded unless a valid response was received.
- Authentication uses Streamlit session state. Sign-in does not persist through a new browser session, and the project does not provide email verification, password recovery, persistent cookies, or OAuth.
- SQLite is appropriate for local use or a small single-instance deployment. The application always stores accounts in `data/myweather.db`; platforms with ephemeral filesystems can erase this file during restart or redeployment.

### Important Weather Maps API-key exposure limitation

Weather Maps 1.0 authenticates raster tile requests with `appid` in the tile URL. Folium/Leaflet runs those tile requests in the browser, so the map key is visible to a user through browser developer tools even though it is absent from Git, logs, documentation, and screenshots.

For this application, that provider-side limitation is disclosed in the UI. For a production deployment:

- use a dedicated, revocable/rotatable key rather than sharing a key used by other systems;
- monitor usage and rotate the key if exposed;
- consider a same-origin server-side tile proxy that keeps the upstream key server-side and adds strict validation, caching, rate limiting, and access control;
- verify that proxying/caching complies with the current OpenWeather license and terms before deployment.

A tile proxy is not included because it requires a separately deployed server component, operational rate limiting, cache management, and a review of the provider's current license terms. Streamlit does not natively provide an in-process tile-proxy endpoint.

## Data and licensing

Weather data and map tiles remain subject to OpenWeather's terms and attribution requirements.
