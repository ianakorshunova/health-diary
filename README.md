# Health Diary ❤️

A simple Russian-language Streamlit app for tracking personal health records: blood pressure, pulse, oxygen level, and general well-being.

The app was built as a practical family health diary and a small data-tracking project using Python, Streamlit, pandas, and Altair.

## Live Demo

Coming soon.

## Features

- Add daily health records
- Track:
  - systolic blood pressure
  - diastolic blood pressure
  - pulse
  - oxygen level (SpO₂)
  - general well-being
  - comments
- Mark individual values as “not measured”
- View the latest record in a summary card
- Browse health history
- Filter records by year and month
- Edit existing records
- Delete the latest added record with confirmation
- View monthly statistics
- Display charts for:
  - blood pressure
  - pulse
  - oxygen level
- Export filtered records as a CSV backup
- Store user data locally

## Tech Stack

- Python
- Streamlit
- pandas
- Altair
- CSV file storage

## Privacy

Health records are stored locally in:

```text
data/health_log.csv
```

The data/ folder is excluded from GitHub via .gitignore.

This means personal health data is not uploaded to the repository.

## Medical Disclaimer

This app is intended only for personal tracking and record keeping.

It does not provide medical advice, diagnosis, or treatment recommendations. Please consult a qualified healthcare professional for medical concerns.

## How to Run Locally

Clone the repository:

```bash
git clone https://github.com/ianakorshunova/health-diary.git
cd health-diary

Install dependencies:

pip install -r requirements.txt

## Run the app:

streamlit run app.py
Project Structure

```text
health-diary/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The app automatically creates a local data/health_log.csv file when records are added.

## Notes

The interface is currently in Russian because the app was designed for family use.

## Possible future improvements:

Add English interface option
Add sample demo data
Add more detailed monthly summaries
Add optional export to Excel
Improve mobile layout
Add safer record deletion by selecting a specific record
