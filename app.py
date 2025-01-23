from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
import requests

app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Company Data API",
        "description": "API for fetching financial data and analyzing company performance.",
        "version": "1.0.0"
    },
    "host": "companyanalysisapi.onrender.com",
    "basePath": "/",
    "schemes": ["https"]
}

Swagger(app, config=swagger_config, template=swagger_template)

@app.route("/")
def home():
    return "Welcome to the Company Data API!"

@app.route("/fetch_live_data", methods=["POST"])
@swag_from({
    "parameters": [
        {
            "name": "symbol",
            "in": "body",
            "type": "string",
            "required": True,
            "description": "The stock symbol (e.g., AAPL)."
        }
    ],
    "responses": {
        "200": {
            "description": "JSON response with financial data"
        },
        "400": {
            "description": "Bad request (missing or invalid parameters)"
        }
    }
})
def fetch_live_data():
    data = request.json
    if not data or "symbol" not in data:
        return jsonify({"error": "Symbol is required"}), 400

    symbol = data["symbol"]
    ALPHA_VANTAGE_API_KEY = "4PZ9M38DME05M9II"
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        json_data = response.json()
        if "Symbol" not in json_data:
            return jsonify({"error": "Invalid symbol or no data found"}), 404
        return jsonify(json_data)
    else:
        return jsonify({"error": "Failed to fetch live data"}), response.status_code

@app.route("/fetch_10k_filing", methods=["POST"])
@swag_from({
    "parameters": [
        {
            "name": "cik",
            "in": "body",
            "type": "string",
            "required": True,
            "description": "The Central Index Key (CIK)."
        }
    ],
    "responses": {
        "200": {
            "description": "10-K filing URLs"
        },
        "400": {
            "description": "Bad request (missing or invalid parameters)"
        }
    }
})
def fetch_10k_filing():
    data = request.json
    if not data or "cik" not in data:
        return jsonify({"error": "CIK (Central Index Key) is required"}), 400

    cik = data["cik"].zfill(10)
    headers = {"User-Agent": "YourName/YourEmail@example.com"}
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        filings = response.json().get("filings", {}).get("recent", {})
        filing_urls = [
            f"https://www.sec.gov/Archives/{path}"
            for path, form in zip(filings["primaryDocument"], filings["form"])
            if "10-K" in form
        ]
        return jsonify({"filing_urls": filing_urls})
    else:
        return jsonify({"error": "Failed to fetch 10-K filings"}), 400

@app.route("/company_analysis", methods=["POST"])
@swag_from({
    "parameters": [
        {
            "name": "symbol",
            "in": "body",
            "type": "string",
            "required": True,
            "description": "The stock symbol (e.g., AAPL)."
        },
        {
            "name": "cik",
            "in": "body",
            "type": "string",
            "required": True,
            "description": "The Central Index Key (CIK)."
        }
    ],
    "responses": {
        "200": {
            "description": "Combined analysis and financial data"
        },
        "400": {
            "description": "Bad request (missing or invalid parameters)"
        }
    }
})
def company_analysis():
    data = request.json
    if not data or "symbol" not in data or "cik" not in data:
        return jsonify({"error": "Symbol and CIK are required"}), 400

    symbol = data["symbol"]
    cik = data["cik"].zfill(10)
    ALPHA_VANTAGE_API_KEY = "4PZ9M38DME05M9II"
    financial_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    financial_response = requests.get(financial_url)

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
        analysis = {"pros": [], "cons": []}
        if float(financial_data.get("ProfitMargin", 0)) > 0.2:
            analysis["pros"].append("High profit margin")
        else:
            analysis["cons"].append("Low profit margin")

        if float(financial_data.get("PEGRatio", 0)) < 1:
            analysis["pros"].append("Undervalued stock (based on PEG ratio)")
        else:
            analysis["cons"].append("Overvalued stock (based on PEG ratio)")

        return jsonify({
            "financial_data": financial_data,
            "filing_urls": filing_urls,
            "analysis": analysis
        })
    else:
        return jsonify({"error": "Failed to fetch data"}), 400

if __name__ == "__main__":
    app.run(port=5000)
