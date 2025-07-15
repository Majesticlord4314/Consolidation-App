# Inventory Consolidation Analysis Web App

A modern, interactive Streamlit web application for inventory rebalancing and movement recommendations between stores and warehouses, built for retail and supply chain analysts.

## Features
- **Upload and preview CSVs**: Upload Sales, SOH (Stock On Hand), and Format Template files. Preview columns and sample data instantly.
- **Automatic data cleaning**: Standardizes product names, filters out unwanted products (e.g., 'Apple'), and validates required columns.
- **Smart aggregation**: Summarizes sales and stock data by store and product, with clear summary and compact aggregation stats.
- **Forecast & allocation**: Merges sales and stock, estimates demand, and suggests optimal transfer movements between stores/warehouses.
- **Interactive analytics**: Get movement summaries, download Excel reports, and explore detailed movement tables—all in your browser.

## File Structure
```
consolidation_webapp/
├── main.py          # Streamlit app code
├── requirements.txt # Python dependencies
├── README.md        # This file
```

## Quick Start
1. **Clone the repo**
   ```sh
   git clone <your-repo-url>
   cd consolidation_webapp
   ```
2. **Install dependencies** (recommend using a virtual environment)
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the app**
   ```sh
   streamlit run main.py
   ```
4. **Open in browser**
   - Follow the Streamlit link (http://localhost:8501](https://consolidate.streamlit.app/))

## CSV Format Requirements
- **Sales CSV**: Must contain columns: `StoreName`, `ProductCode`, `ProductName`, `Quantity`
- **SOH CSV**: Must contain columns: `StoreName`, `ProductCode`, `ProductName`, `ActualStock`
- **Format Template CSV**: Must contain column: `Part No`

## How It Works
1. **Upload your CSVs**
2. **Preview and validate data**
3. **App cleans, aggregates, and analyzes inventory**
4. **Get suggested transfers and download Excel report**

## Example Workflow
1. Upload your three CSV files
2. Review the sample data and aggregation summaries
3. View movement recommendations and download the Excel report
4. Explore the analysis summary and detailed movement table in the app

## Tech Stack
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [XlsxWriter](https://xlsxwriter.readthedocs.io/)

