# Michigan County Air Quality Explorer (2025)

## Live Streamlit Dashboard
https://ebnerashid-cmse-830-app-hslkmx.streamlit.app/

## Project Objective
To analyze air quality across Michigan counties in 2025 using the EPA Air Quality Index (AQI) dataset.

## Main Research Question
How does air quality vary across Michigan counties throughout the year?

## Intended Audience
Michigan residents, students, and anyone interested in understanding local air quality conditions.

## Dataset
- Source: U.S. EPA Daily AQI by County
- Year: 2025
- Original dataset: National county-level AQI observations.
- After cleaning: 8,373 county-day observations from 27 Michigan counties.

## Analysis and Visualizations

The project examines AQI distributions, EPA AQI categories, county-level differences, monthly patterns, defining pollutants, and reporting coverage.
The Streamlit dashboard includes interactive county and month filters and a Michigan county map with hover information.

## How to Run
1. Download or clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`



## Limitations
- Data are available for only 27 of Michigan's 83 counties.
- Reporting coverage varies among counties.
- The analysis covers 2025 only.
- More complete county-day coverage would improve the reliability of comparisons.

## AI Use Disclosure

AI Tool Used: ChatGPT (GPT-6)

Purpose of Use: ChatGPT was used to assist with Python coding, debugging, Streamlit dashboard development, data visualization, and improving interactive visualization and project documentation.

Verification: The suggested code and outputs were tested and reviewed, and the dashboard was checked to ensure that the visualizations and interactive filters worked correctly.

My Contribution: I selected the research question and dataset, performed the data analysis, reviewed the results, and prepared the final project and interpretations.
