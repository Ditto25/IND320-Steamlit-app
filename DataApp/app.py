# app.py
import re
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="Open Meteo Explorer", layout="wide")

# -------------------------
# CACHED DATA LOADING
# -------------------------
@st.cache_data
def load_csv(path: str = "open-meteo-subset.csv") -> pd.DataFrame:
    """Les CSV og gjør noen grunnleggende parsingforsøk (dato). Cached for raskere gjenkjøringer."""
    df = pd.read_csv(path)
    # Prøv å parse en mulig dato-kolonne (vanlige navn)
    for cand in ("time", "date", "datetime", "timestamp"):
        if cand in df.columns:
            df[cand] = pd.to_datetime(df[cand], errors="coerce")
            break
    return df

# -------------------------
# Hjelpefunksjoner for kolonner / måneder
# -------------------------
def guess_month_like_columns(df: pd.DataFrame) -> List[str]:
    """Finn kolonner som ser ut som 'months' eller numeriske målekolonner.
       Heuristikk: YYYY-MM eller month_*, ellers fallback = alle numeriske kolonner."""
    month_cols = []
    for col in df.columns:
        if re.match(r"^\d{4}-\d{2}$", col) or re.match(r"^\d{4}_\d{2}$", col):
            month_cols.append(col)
        elif re.match(r"(?i)^month(_|-)?\d+", col):
            month_cols.append(col)
        elif col.lower() in ("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"):
            month_cols.append(col)
    if not month_cols:
        # fallback: bruk alle numeriske kolonner (ikke-dato)
        month_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    return month_cols

def make_row_series_column(df: pd.DataFrame, cols: List[str], new_col_name: str = "month_series") -> pd.DataFrame:
    """Lag en kolonne hvor hver celle er en liste (krav for LineChartColumn)."""
    if len(cols) == 0:
        df[new_col_name] = [[] for _ in range(len(df))]
    else:
        df[new_col_name] = df[cols].apply(lambda r: [ (float(x) if not pd.isna(x) else None) for x in r.values ], axis=1)
    return df

# -------------------------
# Last data
# -------------------------
df = load_csv("open-meteo-subset.csv")

# Gjett månedskolonner / målekolonner
month_cols = guess_month_like_columns(df)

# Lag en kolonne med liste-verdier (kreves for LineChartColumn i st.dataframe)
df = make_row_series_column(df, month_cols, new_col_name="month_series")

# -------------------------
# SIDENAV / MULTI-PAGE (EN FIL)
# -------------------------
page = st.sidebar.radio("Velg side", ["Hjem", "Data (tabell)", "Plot (interaktiv)", "Side 4 (dummy)"])

if page == "Hjem":
    st.title("Hjem — Open Meteo Explorer")
    st.write("Dette er forsiden. Bruk menyen i venstre sidebar for å gå til de andre sidene.")
    st.write("CSV-fil som leses:", "`open-meteo-subset.csv` (må være i samme mappe som app.py)")
    st.write("Antall rader:", len(df))
    st.write("Gjettede 'måned'/målekolonner:", month_cols)

elif page == "Data (tabell)":
    st.title("Data – tabellvisning med innebygde minidiagrammer")
    st.write("Tabellen under viser innlastet data. Kolonnen `month_series` inneholder rader med lister — disse vises som små linjediagrammer i tabellen.")
    # Konfigurer LineChartColumn for 'month_series' (krever at cellene er lists of numbers)
    # Vi setter y_min/y_max for bedre visning dersom mulig:
    try:
        y_min = float(df[month_cols].min().min()) if month_cols else None
        y_max = float(df[month_cols].max().max()) if month_cols else None
    except Exception:
        y_min = None
        y_max = None

    # Bygg column_config dersom st.column_config er tilgjengelig:
    column_config = {}
    if "month_series" in df.columns:
        column_config["month_series"] = st.column_config.LineChartColumn("Første måned (mini-sparkline)", y_min=y_min, y_max=y_max)

    st.dataframe(df.head(200), use_container_width=True, column_config=column_config)

elif page == "Plot (interaktiv)":
    st.title("Plot — interaktivt (velg kolonne + måneder)")

    # Prøv å finne en tidskolonne som kan brukes for x-aksen:
    time_col = None
    for cand in ("time", "date", "datetime", "timestamp"):
        if cand in df.columns and pd.api.types.is_datetime64_any_dtype(df[cand]):
            time_col = cand
            break

    # Lag månedstrenger hvis vi har en tid-kolonne
    months = []
    if time_col:
        df["_month"] = df[time_col].dt.to_period("M").astype(str)
        months = sorted(df["_month"].dropna().unique().tolist())

    # Dropdown for kolonnevalg (enkeltkolonne eller "All")
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != "month_series"]
    select_options = ["All"] + numeric_cols
    selected = st.selectbox("Velg kolonne (eller 'All')", select_options, index=0)

    # Velg måned(er) med select_slider — default = første måned
    if months:
        default = (months[0], months[0])
        month_range = st.select_slider("Velg måned(er) (range)", options=months, value=default)
        # Filtrer etter valgt måned-range
        mask = (df["_month"] >= month_range[0]) & (df["_month"] <= month_range[1])
        df_plot = df[mask]
        x_field = time_col
    else:
        # fallback: hvis ingen tid, tillat å velge kolonner fra month_cols ved indeks
        if month_cols:
            st.info("Ingen tid/dato-kolonne funnet — bruker wide-format kolonner som 'måned' kolonner.")
            # velg start og slutt indeks blant month_cols
            start = st.select_slider("Velg startmåned (kolonne)", options=month_cols, value=month_cols[0])
            end = st.select_slider("Velg sluttmåned (kolonne)", options=month_cols, value=month_cols[0])
            # finn indekser og velg kolonner
            si, ei = month_cols.index(start), month_cols.index(end)
            if si <= ei:
                chosen_cols = month_cols[si:ei+1]
            else:
                chosen_cols = month_cols[ei:si+1]
            df_plot = df[chosen_cols]
            x_field = None
        else:
            st.warning("Fant ingen numeriske/månedskolonner å plotte.")
            df_plot = df.copy()
            x_field = None

    # Lag diagram
    st.subheader("Diagram")
    if x_field and len(df_plot) > 0:
        if selected == "All":
            # plott alle numeriske kolonner i valgt tidsutvalg
            plot_cols = [c for c in numeric_cols if c in df_plot.columns]
            if len(plot_cols) == 0:
                st.warning("Ingen numeriske kolonner å vise for 'All'.")
            else:
                df_long = df_plot[[x_field] + plot_cols].melt(id_vars=[x_field], value_vars=plot_cols,
                                                               var_name="variable", value_name="value")
                chart = (
                    alt.Chart(df_long)
                    .mark_line()
                    .encode(
                        x=alt.X(f"{x_field}:T", title="Tid"),
                        y=alt.Y("value:Q", title="Verdi"),
                        color=alt.Color("variable:N", title="Serie"),
                        tooltip=[f"{x_field}:T", "variable", "value"]
                    )
                    .properties(height=400)
                    .interactive()
                )
                st.altair_chart(chart, use_container_width=True)
        else:
            if selected not in df_plot.columns:
                st.warning(f"Valgt kolonne '{selected}' finnes ikke i data for valgt periode.")
            else:
                chart = (
                    alt.Chart(df_plot)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X(f"{x_field}:T", title="Tid"),
                        y=alt.Y(f"{selected}:Q", title=selected),
                        tooltip=[f"{x_field}:T", selected]
                    )
                    .properties(height=400)
                    .interactive()
                )
                st.altair_chart(chart, use_container_width=True)
    else:
        # fallback enklere plotting (tabell / linje uten x)
        if selected == "All":
            st.line_chart(df_plot)
        else:
            if selected in df_plot.columns:
                st.line_chart(df_plot[selected])
            else:
                st.info("Ingen plott tilgjengelig — sjekk at kolonnen finnes og at data er numerisk.")

elif page == "Side 4 (dummy)":
    st.title("Side 4 - dummy")
    st.write("Testinnhold / placeholder for side 4.")
