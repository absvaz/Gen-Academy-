from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from metrics import load_data, summarize, filter_data

st.set_page_config(page_title='Campaign Performance', page_icon='📊', layout='wide')
st.markdown('''<style>
.block-container {padding-top:2rem;}
[data-testid="stMetric"] {background:#f0f5fa;padding:18px;border-radius:12px;}
</style>''', unsafe_allow_html=True)
st.title('Campaign Performance')
st.caption('Understand where your advertising budget delivers results.')
COLORS = {'Facebook':'#2563eb','Instagram':'#c026d3','Pinterest':'#dc2626','Twitter':'#0891b2'}

with st.sidebar:
    st.header('Data & global filters')
    uploaded = st.file_uploader('Upload campaign CSV', type=['csv'])
try:
    df = load_data(uploaded if uploaded else Path(__file__).with_name('campaigns.csv'))
except Exception as exc:
    st.error(f'Unable to load CSV: {exc}')
    st.stop()

with st.sidebar:
    st.caption(f'{len(df):,} records · {df.Date.min():%b %d, %Y} – {df.Date.max():%b %d, %Y}')
    st.caption('Monetary values are displayed as USD ($).')
    # Keys vary with the source so new uploads get their own valid defaults.
    signature = str(hash(df.to_csv(index=False)))
    def key(name): return name + signature
    def reset():
        for name in ['start', 'end', 'channels', 'audiences', 'goals']:
            st.session_state.pop(key(name), None)
    st.button('Reset filters', on_click=reset)
    start = st.date_input('Start date', value=df.Date.min().date(), key=key('start'))
    end = st.date_input('End date', value=df.Date.max().date(), key=key('end'))
    def select(label, col, name):
        options = sorted(df[col].unique())
        return st.multiselect(label, options, default=options, key=key(name))
    channels = select('Channel', 'Channel', 'channels')
    audiences = select('Audience', 'Audience', 'audiences')
    goals = select('Campaign goal', 'Goal', 'goals')
    st.caption('All four views use these filters. Clear a selection to show no matches.')

if start > end:
    st.error('Start date must be on or before end date.')
    st.stop()
dated, data = filter_data(df, start, end, channels, audiences, goals)
if dated.empty:
    st.info('No data in this range')
    st.stop()
if data.empty:
    st.info('No campaigns match your selected filters. Adjust or reset the filters.')
    st.stop()
st.caption(f'Showing {len(data):,} of {len(df):,} records · {start:%b %d, %Y} – {end:%b %d, %Y}')

def chart(fig):
    fig.update_layout(template='plotly_white', margin=dict(l=20,r=20,t=50,b=20), legend_title_text='')
    st.plotly_chart(fig, width='stretch')

def table(frame):
    configs = {}
    for col in frame.columns:
        if col in ['Spend', 'Revenue'] or col.startswith(('CPC', 'CPA')):
            configs[col] = st.column_config.NumberColumn(col if col not in ['Spend','Revenue'] else col+' ($)', format='$%.2f')
        elif '(%)' in col:
            configs[col] = st.column_config.NumberColumn(col, format='%.2f%%')
        elif col in ['Clicks','Conversions','Impressions']:
            configs[col] = st.column_config.NumberColumn(col+' (count)', format='%d')
    st.dataframe(frame, hide_index=True, width='stretch', column_config=configs)

overview, platforms, campaigns, times = st.tabs(['Overview','Platform Comparison','Campaign Details','Time Series'])
with overview:
    total = summarize(data).iloc[0]
    columns = st.columns(5)
    for c, label, value in zip(columns, ['Spend ($)','Clicks (count)','Conversions (count)','Revenue ($)','ROI (%)'],
        [f'${total.Spend:,.2f}', f'{total.Clicks:,.0f}', f'{total.Conversions:,.0f}', f'${total.Revenue:,.2f}', 'N/A' if pd.isna(total['ROI (%)']) else f"{total['ROI (%)']:,.2f}%"]):
        c.metric(label,value)
    daily = summarize(data, ['Date'])
    fig = make_subplots(specs=[[{'secondary_y':True}]])
    fig.add_trace(go.Scatter(x=daily.Date,y=daily.Spend,name='Spend ($)',mode='lines+markers',line_color='#2563eb'),secondary_y=False)
    fig.add_trace(go.Scatter(x=daily.Date,y=daily.Conversions,name='Conversions (count)',mode='lines+markers',line_color='#0d9488'),secondary_y=True)
    fig.update_layout(title='Spend versus conversions over time')
    fig.update_yaxes(title_text='Spend ($)',secondary_y=False)
    fig.update_yaxes(title_text='Conversions (count)',secondary_y=True)
    chart(fig)
    ranking = summarize(data,['Channel']).dropna(subset=['ROI (%)']).sort_values('ROI (%)',ascending=False)
    if not ranking.empty:
        winner = ranking.iloc[0]
        st.success(f"Highest channel ROI in this selection: {winner.Channel} · {winner['ROI (%)']:.2f}%")
    st.caption('ROI = (Revenue − Spend) ÷ Spend × 100. This measures return after advertising spend, before other business costs. Ratios use aggregated totals; zero denominators show N/A. Trends connect observed dates only.')

with platforms:
    st.subheader('Compare advertising channels')
    summary = summarize(data,['Channel'])
    a,b = st.columns(2)
    for container, metric, label in [(a,'Spend','Spend ($)'),(b,'Clicks','Clicks (count)')]:
        with container:
            chart(px.bar(summary,x='Channel',y=metric,color='Channel',color_discrete_map=COLORS,title=label,labels={metric:label}))
    a,b = st.columns(2)
    for container, metric in [(a,'Conversions'),(b,'ROI (%)')]:
        with container:
            chart(px.bar(summary,x='Channel',y=metric,color='Channel',color_discrete_map=COLORS,title=metric if metric!='Conversions' else 'Conversions (count)',labels={'Conversions':'Conversions (count)'}))
    table(summary)

with campaigns:
    st.subheader('Campaign-level results')
    search = st.text_input('Search campaign name', placeholder='e.g. Spring Sale')
    summary = summarize(data,['Campaign','Channel','Audience','Goal'])
    summary = summary[summary.Campaign.str.contains(search,case=False,regex=False)].sort_values('ROI (%)',ascending=False)
    st.caption('One row per campaign, channel, audience and goal combination; sorted by ROI. Click a column header to change sorting.')
    if summary.empty:
        st.info('No campaigns match your search.')
    else:
        table(summary)
        st.download_button('Download campaign results (CSV)',summary.to_csv(index=False),'campaign_results.csv','text/csv')

with times:
    st.subheader('Explore performance over time')
    a,b = st.columns(2)
    with a:
        metric = st.selectbox('Performance metric',['Spend','Clicks','Conversions','Revenue','ROI (%)','CTR (%)','Conversion rate (%)','CPA ($/conversion)'])
    with b:
        frequency = st.selectbox('Time interval',['Daily','Weekly','Monthly'])
    trend_data = data.copy()
    trend_data['Period'] = trend_data.Date.dt.to_period({'Daily':'D','Weekly':'W-SUN','Monthly':'M'}[frequency]).dt.start_time
    trend = summarize(trend_data,['Period','Channel'])
    label = metric+' ($)' if metric in ['Spend','Revenue'] else metric+' (count)' if metric in ['Clicks','Conversions'] else metric
    chart(px.line(trend,x='Period',y=metric,color='Channel',markers=True,color_discrete_map=COLORS,labels={metric:label,'Period':'Period start'},title=f'{label} by channel'))
    st.caption('Weekly periods begin Monday; monthly periods begin on the first day. Missing periods are not treated as zero activity.')
    table(trend)
