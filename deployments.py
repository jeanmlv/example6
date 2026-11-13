import pandas as pd
import plotly.express as px
import streamlit as st
from src.ui import download_row

SHEET = '10_DEPLOYMENTS'
COLUMNS = ['Deployment ID', 'Study ID', 'Study Name', 'Compound / Indication',
           'ARGES Hypothesis', 'FPI', 'LPI', 'DBL', 'IA', 'ARGES Analysis',
           'ICF', 'Protocol', 'Other', 'Endo', 'SRP', 'SRS', 'PML',
           'ARGES Personnel', 'Other Key Personnel', 'Next steps',
           'Source / Qualifications']
MISSING = {'', '-', '—', 'n/a', 'na', 'nan', 'none', 'not listed'}

def has_value(series):
    return ~series.fillna('').astype(str).str.strip().str.lower().isin(MISSING)

def prepare_deployments(data):
    df = data.get(SHEET, pd.DataFrame()).copy()
    df.columns = df.columns.astype(str).str.strip()
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        st.error('Missing deployment columns: ' + ', '.join(sorted(missing)))
        return pd.DataFrame(columns=COLUMNS)
    df = df.loc[has_value(df['Deployment ID']), COLUMNS].copy()
    for col in COLUMNS:
        df[col] = df[col].map(lambda x: '' if pd.isna(x) else
                              x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x).strip())
    if df['Deployment ID'].duplicated().any():
        st.error('Deployment IDs must be unique.')
        return pd.DataFrame(columns=COLUMNS)
    return df.reset_index(drop=True)

def apply_study_filters(df, filtered, data):
    all_studies = data.get('01_STUDIES', pd.DataFrame())
    selected = filtered.get('01_STUDIES', pd.DataFrame())
    if 'Study ID' not in all_studies or 'Study ID' not in selected:
        return df
    all_ids = set(all_studies['Study ID'].dropna().astype(str).str.strip())
    ids = set(selected['Study ID'].dropna().astype(str).str.strip())
    if ids == all_ids:
        return df
    if not ids:
        return df.iloc[:0]
    return df[df['Study ID'].isin(ids)].copy()

def render(filtered, data):
    st.header('Deployments')
    st.caption('Clinical trial planning, timelines, documentation, key personnel and next steps for ARGES deployments.')
    full = prepare_deployments(data)
    if full.empty:
        st.info('No deployment information is available.')
        return
    df = apply_study_filters(full, filtered, data)
    st.subheader('Deployment Explorer')
    search = st.text_input('Search deployments', key='dep_search', placeholder='Study, compound, hypothesis, personnel...')
    with st.expander('Filter by column', expanded=True):
        columns = st.multiselect('Columns to filter', COLUMNS, key='dep_filter_columns')
        for col in columns:
            values = sorted(df[col].unique().tolist())
            options = ['(Blank)' if v == '' else v for v in values]
            chosen = st.multiselect(col, options, key='dep_filter_' + col)
            if chosen:
                df = df[df[col].isin(['' if v == '(Blank)' else v for v in chosen])]
    if search.strip():
        mask = df.apply(lambda s: s.str.contains(search.strip(), case=False, regex=False)).any(axis=1)
        df = df[mask]
    st.caption(f'{len(df)} of {len(full)} deployment records. Global study filters exclude records without a matching Study ID.')
    if df.empty:
        st.info('No deployments match the current filters.')
        return
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Deployment records', len(df))
    c2.metric('Protocols identified', int(has_value(df['Study ID']).sum()))
    c3.metric('DBL documented', int(has_value(df['DBL']).sum()))
    c4.metric('Next steps defined', int(has_value(df['Next steps']).sum()))
    st.subheader('Deployment Portfolio')
    def indication(value):
        v = value.lower().rsplit('/', 1)[-1].strip()
        if v in ('uc', 'ulcerative colitis'): return 'Ulcerative Colitis'
        if v in ('cd', "crohn's disease", 'crohn’s disease'): return "Crohn's Disease"
        return 'Other / Unspecified'
    counts = df['Compound / Indication'].map(indication).value_counts().rename_axis('Indication').reset_index(name='Records')
    fig = px.bar(counts, x='Indication', y='Records', color='Indication', text='Records', color_discrete_map={'Ulcerative Colitis':'#E2231A', "Crohn's Disease":'#F46B62', 'Other / Unspecified':'#808899'})
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300, margin=dict(l=10,r=10,t=15,b=10))
    st.plotly_chart(fig, use_container_width=True)
    tabs = st.tabs(['Complete inventory', 'Timeline', 'Personnel', 'Documentation', 'Next steps'])
    with tabs[0]:
        st.dataframe(df, use_container_width=True, hide_index=True)
        download_row(df, 'filtered_deployments')
    groups = [(['Study Name','Study ID','FPI','LPI','DBL','IA','ARGES Analysis'], 'FPI: First Patient In | LPI: Last Patient In | DBL: Database Lock | IA: Interim Analysis'), (['Study Name','SRP','SRS','PML','ARGES Personnel','Other Key Personnel'], None), (['Study Name','ICF','Protocol','Other','Endo'], None), (['Study Name','ARGES Hypothesis','Next steps','Source / Qualifications'], None)]
    for tab,(cols,note) in zip(tabs[1:],groups):
        with tab:
            if note: st.caption(note)
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
    with st.expander('Edit deployment records (draft)'):
        st.caption('Edit the visible records and download a draft CSV. This does not update the shared workbook. Deployment IDs are read-only.')
        # Stable key for each filtered set; prevents edits being applied to different rows.
        import hashlib
        key = hashlib.sha256(df.to_json(orient='split').encode()).hexdigest()[:20]
        edited = st.data_editor(df, disabled=['Deployment ID'], num_rows='fixed', hide_index=True, use_container_width=True, key='dep_editor_'+key)
        st.download_button('Download edited records (CSV)', edited.to_csv(index=False).encode('utf-8-sig'), file_name='deployments_edited.csv', mime='text/csv', key='dep_download_edits')
