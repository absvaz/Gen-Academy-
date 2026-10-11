# Campaign Performance Dashboard

## Run locally or in Replit

Extract all files into the same folder. Open a terminal there and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the URL shown in the terminal. In Replit, use the same commands in Shell and open the web preview.

The supplied campaigns.csv loads automatically. Upload another CSV from the sidebar using these columns:
Date, Campaign, Channel, Audience, Goal, Impressions, Clicks, Spend, Conversions, Revenue.
Dates must be parseable and numeric values finite and non-negative. Monetary amounts are assumed to be USD.

Four views share date, channel, audience and campaign-goal filters. Campaign Details also has a local text search. Reset filters restores all records. Dates outside the dataset are allowed; if no dated records exist, the app displays exactly "No data in this range".

ROI = (total revenue - total spend) / total spend * 100. CTR = clicks / impressions * 100. Conversion rate = conversions / clicks * 100. CPA = spend / conversions. CPC = spend / clicks. ROAS = revenue / spend. All grouped ratios are calculated from summed values, never averaged row percentages. Undefined ratios display N/A or a blank in tables.

ROI accounts for advertising spend only, not product costs, overhead or attribution quality. Charts connect observed data; missing dates are not imputed as zero.
