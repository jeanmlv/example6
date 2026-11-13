# example6

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui import show_table, download_row


SHEET = "10_DEPLOYMENTS"

COLUMNS = [
    "Name",
    "Protocol ID",
    "Compound / indication",
    "Hypothesis / ARGES",
    "FPI",
    "LPI",
    "DBL",
    "IA",
    "ARGES analysis",
    "ICF",
    "Protocol",
    "Other",
    "Endo",
    "SRP",
    "SRS",
    "PML",
    "ARGES personnel",
    "Other key personnel",
    "Next steps",
    "Source / qualifications",
]

MISSING = {"", "-", "—", "n/a", "na", "nan", "none", "not listed"}


def has_value(series):
    values = series.fillna("").astype(str).str.strip().str.lower()
    return ~values.isin(MISSING)


def prepare_deployments(data):
    df = data.get(SHEET, pd.DataFrame()).copy()

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    # Workbook loader reads the first row as column headers.
    # The second Excel row contains the actual field names.
    if "Name" not in df.columns:
        header_row = df.iloc[0].astype(str).str.strip().tolist()

        if "Name" in header_row and "Protocol ID" in header_row:
            df = df.iloc[1:].copy()
            df.columns = header_row
        else:
            st.error("Unexpected header structure in 10_DEPLOYMENTS.")
            return pd.DataFrame(columns=COLUMNS)

    df.columns = [str(c).strip() for c in df.columns]

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLUMNS].copy()
    df = df[df["Name"].notna()].copy()
    df = df[has_value(df["Name"])].copy()

    for col in ["FPI", "LPI", "DBL", "IA", "ARGES analysis"]:
        df[col] = df[col].apply(
            lambda x: x.strftime("%Y-%m-%d")
            if isinstance(x, (pd.Timestamp,))
            else x.strftime("%Y-%m-%d")
            if hasattr(x, "strftime")
            else x
        )

    return df.reset_index(drop=True)


def apply_study_filters(df, filtered):
    studies = filtered.get("01_STUDIES", pd.DataFrame())

    if df.empty or studies.empty:
        return df

    if "Study ID" not in studies.columns:
        return df

    allowed_ids = set(
        studies["Study ID"].dropna().astype(str).str.strip()
    )

    # Avoid losing rows with missing protocol IDs.
    # Apply filters only when the main study inventory is filtered.
    return df[
        df["Protocol ID"].astype(str).str.strip().isin(allowed_ids)
        | ~has_value(df["Protocol ID"])
    ].copy()


def render(filtered, data):
    st.header("Deployments")
    st.markdown(
        '<div class="section-note">'
        'Clinical trial planning, timelines, documentation, '
        'key personnel and next steps for ARGES deployments.'
        '</div>',
        unsafe_allow_html=True,
    )

    df = prepare_deployments(data)

    if df.empty:
        st.info("No deployment information is available.")
        return

    # Apply dashboard filters only when a subset of studies is selected.
    studies_all = data.get("01_STUDIES", pd.DataFrame())
    studies_selected = filtered.get("01_STUDIES", pd.DataFrame())

    if (
        not studies_all.empty
        and not studies_selected.empty
        and len(studies_selected) < len(studies_all)
    ):
        df = apply_study_filters(df, filtered)

    if df.empty:
        st.info("No deployments match the current filters.")
        return

    # KPIs
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Studies", len(df))
    c2.metric("Protocols identified", int(has_value(df["Protocol ID"]).sum()))
    c3.metric("DBL documented", int(has_value(df["DBL"]).sum()))
    c4.metric("Next steps defined", int(has_value(df["Next steps"]).sum()))

    st.divider()

    # Portfolio
    st.subheader("Deployment Portfolio")

    def indication(name):
        name = str(name).upper()
        if "UC" in name:
            return "Ulcerative Colitis"
        if "CD" in name:
            return "Crohn's Disease"
        return "Other / Unspecified"

    chart_df = df.copy()
    chart_df["Indication"] = chart_df["Name"].apply(indication)

    counts = (
        chart_df["Indication"]
        .value_counts()
        .rename_axis("Indication")
        .reset_index(name="Studies")
    )

    fig = px.bar(
        counts,
        x="Indication",
        y="Studies",
        color="Indication",
        text="Studies",
        color_discrete_map={
            "Ulcerative Colitis": "#E2231A",
            "Crohn's Disease": "#F46B62",
            "Other / Unspecified": "#808899",
        },
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=10, r=10, t=15, b=10),
        height=330,
    )

    st.plotly_chart(fig, width="stretch")

    # Timeline
    st.subheader("Clinical Trial Timeline")
    st.caption(
        "FPI: First Patient In | LPI: Last Patient In | "
        "DBL: Database Lock | IA: Interim Analysis"
    )

    timeline_cols = [
        "Name", "Protocol ID", "FPI", "LPI",
        "DBL", "IA", "ARGES analysis"
    ]

    st.dataframe(
        df[timeline_cols],
        width="stretch",
        hide_index=True,
    )

    # Personnel
    st.subheader("Key Personnel")

    personnel_cols = [
        "Name", "SRP", "SRS", "PML",
        "ARGES personnel", "Other key personnel"
    ]

    st.dataframe(
        df[personnel_cols],
        width="stretch",
        hide_index=True,
    )

    # Documentation
    st.subheader("Documentation & Modality")

    docs_cols = [
        "Name", "ICF", "Protocol", "Other", "Endo"
    ]

    st.dataframe(
        df[docs_cols],
        width="stretch",
        hide_index=True,
    )

    # Next steps
    st.subheader("Next Steps & Source Notes")

    st.dataframe(
        df[["Name", "Next steps", "Source / qualifications"]],
        width="stretch",
        hide_index=True,
    )

    # Complete inventory
    st.subheader("Complete Deployment Inventory")

    show_table(
        df,
        key="deployments_table",
    )

    download_row(
        df,
        "filtered_deployments",
    )


