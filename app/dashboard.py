import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pyspark.errors import AnalysisException
from pyspark.sql import SparkSession, functions as F

import football_sql as queries

GOLD = "/lakehouse/gold"
PALETTE = ["#28b493", "#60a5fa", "#f7ba6c", "#c2a5f5", "#79ccd3"]
st.set_page_config(page_title="Qui recrute chez qui ?", layout="wide")
st.markdown("""
<style>
.mercato-head {background:repeating-linear-gradient(90deg,#083d34 0 9%,#0a4439 9% 18%);
color:white;border-radius:18px;padding:2rem 2.4rem;border-bottom:5px solid #9de392}
.mercato-head h1 {color:white;margin:0;font-weight:800;letter-spacing:-.04em}
.mercato-head p {margin:.4rem 0 0;color:#daf5df}
</style>
<header class="mercato-head"><h1>Qui recrute chez qui ?</h1>
<p>Les routes du mercato · Mouvements entre championnats</p></header>
""", unsafe_allow_html=True)


@st.cache_resource
def spark_session():
    return (
        SparkSession.builder.appName("FootballMercatoDashboard")
        .config("spark.driver.memory", "512m")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )


def table(name):
    return spark_session().read.format("delta").load(f"{GOLD}/football_league_{name}")


@st.cache_data(ttl=600)
def summaries():
    return tuple(table(name).toPandas() for name in ("coverage", "annual", "pareto"))


@st.cache_data(ttl=600)
def annual_flows(year):
    return table("flows").where(F.col("year") == year).toPandas()


@st.cache_data(ttl=60)
def players(year, origin, destination):
    return (
        table("transfers")
        .where((F.col("year") == year) & (F.col("origin_league_id") == origin)
               & (F.col("destination_league_id") == destination))
        .select("player_name", "origin_club", "destination_club", "transfer_type", "fee")
        .orderBy(F.desc_nulls_last("fee"), "player_name", "origin_club", "destination_club")
        .limit(100).toPandas()
    )


def league_label(name, country, identifier):
    name = str(name) if pd.notna(name) else "Ligue sans libellé"
    country = f" · {country}" if pd.notna(country) and country else ""
    return f"{name}{country} [{identifier}]"


def fee_text(amount):
    return f"{amount:,.0f}".replace(",", " ") if pd.notna(amount) else "—"


try:
    coverage, annual, pareto = summaries()
except AnalysisException as error:
    if "PATH_NOT_FOUND" not in str(error):
        raise
    st.info("Exécute d’abord le notebook EDA dans JupyterLab pour créer les tables Gold.")
    st.stop()

years = sorted(coverage["year"].dropna().astype(int).unique(), reverse=True)
if not years:
    st.info("Aucune année de transfert exploitable.")
    st.stop()

filters = st.columns(3)
year = int(filters[0].selectbox("Année", years, index=years.index(2023) if 2023 in years else 0))
direction = filters[1].radio("Sens", ["Arrivées", "Départs"], horizontal=True)
focus, partner = ("destination", "origin") if direction == "Arrivées" else ("origin", "destination")

coverage_year = coverage[coverage["year"] == year]
both = coverage_year[
    (coverage_year["origin_status"] == "rattaché") & (coverage_year["destination_status"] == "rattaché")
]
total = coverage_year["count"].sum()
st.caption(f"Couverture des deux championnats pour {year} : {both['count'].sum():,} sur {total:,} "
           f"transferts ({both['count'].sum() / total:.1%}). Les rattachements ambigus restent hors des flux.")

current = annual_flows(year)
if current.empty:
    st.info("Aucun flux avec deux championnats rattachés pour cette année.")
    st.stop()

for side in ("origin", "destination"):
    current[f"{side}_label"] = [
        league_label(name, country, identifier)
        for name, country, identifier in zip(
            current[f"{side}_league"], current[f"{side}_country"], current[f"{side}_league_id"]
        )
    ]
choices = current.groupby(f"{focus}_label")["transfers"].sum().sort_values(ascending=False)
selected = filters[2].selectbox("Championnat", choices.index.tolist())
routes = current[current[f"{focus}_label"] == selected].sort_values(
    ["transfers", f"{partner}_label"], ascending=[False, True]
)
routes_total = routes["transfers"].sum()
internal = routes[routes["origin_league_id"] == routes["destination_league_id"]]["transfers"].sum()
stats = st.columns(3)
stats[0].metric("Transferts rattachés", f"{routes_total:,}".replace(",", " "))
stats[1].metric("Part dans le même championnat", f"{internal / routes_total:.1%}")
stats[2].metric("Indemnités positives", f"{routes['positive_fees'].sum() / routes_total:.1%}")

top = routes.head(12)
partner_labels = top[f"{partner}_label"].tolist()
labels = partner_labels + [selected] if direction == "Arrivées" else [selected] + partner_labels
n = len(top)
sources = list(range(n)) if direction == "Arrivées" else [0] * n
targets = [n] * n if direction == "Arrivées" else list(range(1, n + 1))
figure = go.Figure(go.Sankey(
    node=dict(label=labels, pad=20, thickness=18, color=[PALETTE[i % len(PALETTE)] for i in range(n + 1)]),
    link=dict(source=sources, target=targets, value=top["transfers"].tolist(),
              color="rgba(40,180,147,.34)",
              hovertemplate="%{source.label} → %{target.label}<br>%{value} transferts<extra></extra>"),
))
figure.update_layout(height=max(380, n * 41), margin=dict(l=10, r=10, t=20, b=10))
st.plotly_chart(figure, width="stretch")

def explain(query, interpretation):
    with st.expander("Requête SQL & Justification statistique"):
        st.code(query.strip(), language="sql")
        st.write(interpretation)


explain(queries.FLOWS, "La largeur des rubans représente le nombre de transferts rattachés.")
if len(routes) > len(top):
    st.caption("Les 12 flux les plus importants sont dessinés. Tous sont disponibles dans le sélecteur.")

route_index = st.selectbox(
    "Explorer un flux",
    routes.index.tolist(),
    format_func=lambda i: f"{routes.loc[i, 'origin_label']} → {routes.loc[i, 'destination_label']}"
                          f" · {routes.loc[i, 'transfers']:,} transferts",
)
route = routes.loc[route_index]
st.caption(f"Indemnité positive médiane : {fee_text(route['median_positive_fee'])} · "
           f"Moyenne : {fee_text(route['mean_positive_fee'])} · "
           f"{route['positive_fees']:,} montants positifs")
movements = players(year, str(route["origin_league_id"]), str(route["destination_league_id"]))
movements["transfer_type"] = movements["transfer_type"].replace({
    "Unknown": "Type inconnu", "Not loan": "Hors prêt", "Loan": "Prêt", "End of loan": "Fin de prêt",
    "Unknown - test MERGE": "Type inconnu (test J2)",
})
if not movements.empty:
    with st.container(border=True):
        ticket = st.selectbox("Fiche de transfert", range(len(movements)), format_func=lambda i:
                              f"{i + 1}. {movements.iloc[i]['player_name'] or 'Joueur inconnu'}")
        movement = movements.iloc[ticket]
        origin, dest, price = st.columns(3)
        origin.metric("Club de départ", movement["origin_club"] or "Inconnu")
        dest.metric("Club d’arrivée", movement["destination_club"] or "Inconnu")
        price.metric("Indemnité enregistrée", fee_text(movement["fee"]))
        st.caption(f"{year} · {movement['transfer_type']} · Un zéro est la valeur inscrite dans la source.")
st.dataframe(
    movements.rename(columns={
        "player_name": "Joueur", "origin_club": "Club de départ", "destination_club": "Club d’arrivée",
        "transfer_type": "Type de transfert", "fee": "Indemnité",
    }), hide_index=True, width="stretch",
)
st.caption("Jusqu’à 100 lignes par flux, triées par indemnité décroissante.")

explain(queries.DETAILS, "Chaque ligne représente un transfert. Les montants inconnus restent vides.")

st.subheader("Principales filières du championnat")
bars = px.bar(top.sort_values("transfers"), x="transfers", y=f"{partner}_label", orientation="h",
              labels={"transfers": "Transferts", f"{partner}_label": "Championnat"},
              color_discrete_sequence=PALETTE)
st.plotly_chart(bars, width="stretch")
explain(queries.FLOWS, "Le nombre de transferts permet de comparer les filières même lorsque les indemnités manquent.")

st.subheader("Concentration des indemnités connues")
concentration = pareto[(pareto["year"] == year) & pareto["cumulative_share"].notna()].sort_values("pareto_order")
if concentration.empty:
    st.caption("Aucun total exploitable pour cette année.")
else:
    line = px.line(concentration, x="pareto_order", y="cumulative_share", hover_name="league",
                   markers=True, labels={"pareto_order": "Position du championnat",
                                         "cumulative_share": "Part cumulée"},
                   color_discrete_sequence=PALETTE)
    line.update_yaxes(tickformat=".0%")
    line.add_hline(y=0.8, line_dash="dot")
    st.plotly_chart(line, width="stretch")
explain(queries.PARETO, "La ligne pointillée montre à partir de combien de championnats on atteint "
        "80 % du total enregistré pour l’année. Ce calcul retient les transferts dont le championnat d’arrivée est identifié.")

st.subheader("Évolution des transferts")
if not annual.empty:
    trend = px.line(annual.sort_values("year"), x="year", y="transfers", color="scope", markers=True,
                    hover_data={"growth": ":.1%", "median_fee": ":,.0f"},
                    labels={"year": "Année", "transfers": "Transferts", "scope": "Périmètre",
                            "growth": "Évolution annuelle", "median_fee": "Indemnité positive médiane"},
                    color_discrete_sequence=PALETTE)
    st.plotly_chart(trend, width="stretch")
explain(queries.TIME, "LAG compare deux années adjacentes. La médiane limite l’influence des "
        "indemnités extrêmes. Une année incomplète peut afficher un faible volume.")


@st.cache_data(ttl=60)
def segments():
    return table("segments").toPandas()


st.subheader("Profils de recrutement des clubs")
try:
    clubs = segments()
except AnalysisException as error:
    if "PATH_NOT_FOUND" not in str(error):
        raise
    st.info("Exécute J4 pour afficher les profils de recrutement.")
else:
    if not clubs.empty:
        first_year = int(clubs["first_year"].iloc[0])
        last_year = int(clubs["last_year"].iloc[0])
        st.caption(f"Période de segmentation : {first_year}–{last_year}.")
        profiles = px.scatter(clubs, x="arrivals", y="median_fee", color="segment",
                              hover_name="club", hover_data={"cross_share": ":.1%", "origin_clubs": True},
                              log_y=True, labels={"arrivals": "Arrivées rattachées",
                                                  "median_fee": "Indemnité positive médiane",
                                                  "segment": "Profil"},
                              color_discrete_sequence=PALETTE)
        st.plotly_chart(profiles, width="stretch")
        explain(queries.FEATURES.format(first_year=first_year, last_year=last_year),
                "Spark agrège un profil par club. Le notebook J4 applique log1p, StandardScaler "
                "et K-means à quatre variables. L’axe des indemnités est logarithmique.")
