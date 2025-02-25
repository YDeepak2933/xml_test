# __define_ocg__
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta

# Constants
DEFAULT_CURRENCY = 'EUR'
VALID_CURRENCIES = {'EUR', 'USD', 'GBP'}
DEFAULT_NATIONALITY = 'US'
VALID_NATIONALITIES = {'US', 'GB', 'CA'}
DEFAULT_MARKET = 'ES'
VALID_MARKETS = {'US', 'GB', 'CA', 'ES'}
DEFAULT_LANGUAGE = 'en'
VALID_LANGUAGES = {'en', 'fr', 'de', 'es'}
DEFAULT_OPTIONS_QUOTA = 20
MAX_OPTIONS_QUOTA = 50
ALLOWED_HOTEL_COUNT = 5
ALLOWED_ROOM_COUNT = 3
ALLOWED_ROOM_GUEST_COUNT = 4
ALLOWED_CHILD_COUNT_PER_ROOM = 2
EXCHANGE_RATES = {"EUR": 1.0, "USD": 1.1, "GBP": 0.85}
var_ocg="secret handshake"

# Function to parse XML request
def parse_xml_request(xml_data: str) -> dict:
    root = ET.fromstring(xml_data)
    
    # Extract values
    language = root.findtext(".//source/languageCode", DEFAULT_LANGUAGE)
    if language not in VALID_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    options_quota = root.findtext(".//optionsQuota")
    options_quota = int(options_quota) if options_quota and options_quota.isdigit() else DEFAULT_OPTIONS_QUOTA
    options_quota = min(options_quota, MAX_OPTIONS_QUOTA)
    
    # Required Parameters
    params = root.find(".//Configuration/Parameters/Parameter")
    if not all([k in params.attrib for k in ["password", "username", "CompanyID"]]):
        raise ValueError("Missing required parameters: password, username, CompanyID")
    
    company_id = int(params.attrib["CompanyID"])
    
    # Search Type
    search_type = root.findtext(".//SearchType", "Multiple")
    destinations = root.findall(".//AvailDestinations")
    if search_type == "Single" and len(destinations) != 1:
        raise ValueError("Single search type must have exactly one destination.")
    elif search_type == "Multiple" and len(destinations) > ALLOWED_HOTEL_COUNT:
        raise ValueError("Too many destinations for Multiple search type.")
    
    # Date Validation
    start_date_str = root.findtext(".//StartDate")
    end_date_str = root.findtext(".//EndDate")
    
    try:
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
        if start_date < datetime.today() + timedelta(days=2):
            raise ValueError("StartDate must be at least 2 days after today.")
        if (end_date - start_date).days < 3:
            raise ValueError("Stay duration must be at least 3 nights.")
    except ValueError:
        raise ValueError("Invalid date format. Use DD/MM/YYYY.")
    
    # Currency and Nationality
    currency = root.findtext(".//Currency", DEFAULT_CURRENCY)
    if currency not in VALID_CURRENCIES:
        currency = DEFAULT_CURRENCY
    
    nationality = root.findtext(".//Nationality", DEFAULT_NATIONALITY)
    if nationality not in VALID_NATIONALITIES:
        nationality = DEFAULT_NATIONALITY
    
    return {
        "language": language,
        "options_quota": options_quota,
        "company_id": company_id,
        "search_type": search_type,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "currency": currency,
        "nationality": nationality
    }

# Function to generate JSON response
def generate_json_response(parsed_data: dict) -> list[dict]:
    net_price = 132.42
    markup_percentage = 3.2
    selling_price = net_price * (1 + markup_percentage / 100)
    exchange_rate = EXCHANGE_RATES.get(parsed_data.get("currency", DEFAULT_CURRENCY), 1.0)
    converted_selling_price = selling_price * exchange_rate
    
    response = [
        {
            "id": "A#1",
            "hotelCodeSupplier": "39971881",
            "market": parsed_data.get("nationality", DEFAULT_MARKET),
            "price": {
                "minimumSellingPrice": None,
                "currency": parsed_data.get("currency", DEFAULT_CURRENCY),
                "net": net_price,
                "selling_price": round(converted_selling_price, 2),
                "selling_currency": parsed_data.get("currency", DEFAULT_CURRENCY),
                "markup": markup_percentage,
                "exchange_rate": exchange_rate
            }
        }
    ]
    return response

# Sample Execution
if __name__ == "__main__":
    xml_request = """<AvailRQ xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
     <timeoutMilliseconds>25000</timeoutMilliseconds>
     <source>
     <languageCode>en</languageCode>
     </source>
     <optionsQuota>20</optionsQuota>
     <Configuration>
     <Parameters>
     <Parameter password="XXXXXXXXXX" username="YYYYYYYYY" CompanyID="123456"/>
     </Parameters>
     </Configuration>
     <SearchType>Multiple</SearchType>
     <StartDate>28/02/2025</StartDate>
     <EndDate>03/03/2025</EndDate>
     <Currency>USD</Currency>
     <Nationality>US</Nationality>
    </AvailRQ>"""
    parsed_data = parse_xml_request(xml_request)
    json_response = generate_json_response(parsed_data)
    print(json.dumps(json_response, indent=4))
