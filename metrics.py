import numpy as np
import pandas as pd

DIMENSIONS = ['Campaign', 'Channel', 'Audience', 'Goal']
VALUES = ['Impressions', 'Clicks', 'Spend', 'Conversions', 'Revenue']

def load_data(source):
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip()
    missing = set(['Date'] + DIMENSIONS + VALUES) - set(df.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    if df.empty:
        raise ValueError('The CSV contains no records.')
    df['Date'] = pd.to_datetime(df['Date'], errors='raise').dt.normalize()
    if df['Date'].isna().any():
        raise ValueError('Every record must have a valid date.')
    for col in DIMENSIONS:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq('').any():
            raise ValueError(f'{col} contains blank values.')
        df[col] = df[col].astype(str).str.strip()
    for col in VALUES:
        df[col] = pd.to_numeric(df[col], errors='raise')
        if not np.isfinite(df[col]).all() or (df[col] < 0).any():
            raise ValueError(f'{col} must contain finite, non-negative numbers.')
    return df.sort_values('Date')

def ratios(df):
    out = df.copy()
    def divide(a, b):
        return out[a].div(out[b].replace(0, np.nan))
    out['ROI (%)'] = (divide('Revenue', 'Spend') - 1) * 100
    out['ROAS (x)'] = divide('Revenue', 'Spend')
    out['CTR (%)'] = divide('Clicks', 'Impressions') * 100
    out['Conversion rate (%)'] = divide('Conversions', 'Clicks') * 100
    out['CPC ($/click)'] = divide('Spend', 'Clicks')
    out['CPA ($/conversion)'] = divide('Spend', 'Conversions')
    return out

def summarize(df, groups=None):
    totals = df.groupby(groups, dropna=False)[VALUES].sum().reset_index() if groups else pd.DataFrame([df[VALUES].sum()])
    return ratios(totals)

def filter_data(df, start, end, channels, audiences, goals):
    dated = df[df.Date.between(pd.Timestamp(start), pd.Timestamp(end))]
    filtered = dated[dated.Channel.isin(channels) & dated.Audience.isin(audiences) & dated.Goal.isin(goals)]
    return dated, filtered
