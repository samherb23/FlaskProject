from flask import Flask, request
import requests

app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return "Welcome to the Company Data API!"

# Route to fetch live financial data
@app.route("/fetch_live_data", methods=["POST"])
def fetch_live_data():
    data = request.json
    if not data or "symbol" not in data:
        return {"error": "Symbol is required"}, 400

    symbol = data.get("symbol")
    ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key"  # Replace with your API key
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        json_data = response.json()
        if "Symbol" not in json_data:  # Check if valid data was returned
            return {"error": "Invalid symbol or no data found"}, 404
        return json_data
    else:
        return {"error": "Failed to fetch live data"}, response.status_code

# Route to fetch SEC 10-K filings
@app.route("/fetch_10k_filing", methods=["POST"])
def fetch_10k_filing():
    data = request.json
    if not data or "cik" not in data:
        return {"error": "CIK (Central Index Key) is required"}, 400

    cik = data.get("cik").zfill(10)  # Ensure CIK is 10 digits
    headers = {"User-Agent": "YourName/YourEmail@example.com"}  # Required by SEC
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        filings = response.json().get("filings", {}).get("recent", {})
        filing_urls = [
            f"https://www.sec.gov/Archives/{path}"
            for path, form in zip(filings["primaryDocument"], filings["form"])
            if "10-K" in form
        ]
        return {"filing_urls": filing_urls}
    else:
        return {"error": "Failed to fetch 10-K filings"}, 400

# Route to combine data and provide analysis
@app.route("/company_analysis", methods=["POST"])
def company_analysis():
    data = request.json
    if not data or "symbol" not in data or "cik" not in data:
        return {"error": "Symbol and CIK are required"}, 400

    symbol = data.get("symbol")
    cik = data.get("cik").zfill(10)

    # Fetch financial data
    ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key"  # Replace with your API key
    financial_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    financial_response = requests.get(financial_url)

    # Fetch 10-K filings
    filing_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": "YourName/YourEmail@example.com"}
    filing_response = requests.get(filing_url, headers=headers)

    if financial_response.status_code == 200 and filing_response.status_code == 200:
        financial_data = financial_response.json()
        filings = filing_response.json().get("filings", {}).get("recent", {})
        filing_urls = [
            f"https://www.sec.gov/Archives/{path}"
            for path, form in zip(filings["primaryDocument"], filings["form"])
            if "10-K" in form
        ]

        # Add analysis based on financial data
        analysis = {"pros": [], "cons": []}
        if float(financial_data.get("ProfitMargin", 0)) > 0.2:
            analysis["pros"].append("High profit margin")
        else:
            analysis["cons"].append("Low profit margin")

        if float(financial_data.get("PEGRatio", 0)) < 1:
            analysis["pros"].append("Undervalued stock (based on PEG ratio)")
        else:
            analysis["cons"].append("Overvalued stock (based on PEG ratio)")

        return {
            "financial_data": financial_data,
            "filing_urls": filing_urls,
            "analysis": analysis
        }
    else:
        return {"error": "Failed to fetch data"}, 400

if __name__ == "__main__":
    app.run(port=5000)

