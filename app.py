import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
st.set_page_config(page_title="Coca-Cola vs. PepsiCo", page_icon="🥤", layout="wide")

KO = "#E61A27"
PEP = "#0B4EA2"
PEP_LIGHT = "#8FB3E3"
TEXT = "#1F2328"
MUTED = "#6B7280"
CFG = {"displayModeBar": False}

# ------------------------------------------------------------
# DATOS OFICIALES (US$ miles de millones · cifras GAAP reportadas)
# Fuente: comunicados de resultados y 10-K presentados ante la SEC
# ------------------------------------------------------------
DATA = {
    "Año 2025": {
        "ko": {"ingresos": 47.941, "prev": 47.061, "neto": 13.107,
               "m_bruto": 61.6, "m_op": 28.7, "m_op_aj": 31.2, "organico": 5.0},
        "pep": {"ingresos": 93.925, "prev": 91.854, "neto": 8.240,
                "m_bruto": 54.1, "m_op": 12.2, "m_op_aj": 15.9, "organico": 1.7},
    },
    "1er semestre 2026": {
        "ko": {"ingresos": 25.852, "prev": 23.664, "neto": 8.349,
               "m_bruto": 62.9, "m_op": 34.9, "m_op_aj": 35.0, "organico": 8.0},
        "pep": {"ingresos": 43.624, "prev": 40.645, "neto": 5.308,
                "m_bruto": 54.7, "m_op": 16.6, "m_op_aj": 16.3, "organico": 2.5},
    },
}
PUBLICIDAD_2025 = {"ko": 5.4, "pep": 3.4, "pep_total": 5.4}
VENTAS_2025 = {"ko": 47.941, "pep": 93.925}
MIX_PEP = {"Alimentos": 58, "Bebidas": 42}


# ------------------------------------------------------------
# FORMATO
# ------------------------------------------------------------
def fmt(x, d=1):
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=1, signo=False):
    return ("+" if signo and x > 0 else "") + fmt(x, d) + "%"


def usd(x):
    return f"US$ {fmt(x)} mil M"


def lider(a, b):
    return "Coca-Cola" if a > b else "PepsiCo"


def kpi(label, ko_val, pep_val, pie, ganador):
    color = KO if ganador == "Coca-Cola" else PEP
    return (
        f'<div class="kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-row"><span class="brand"><i style="background:{KO}"></i>Coca-Cola</span>'
        f'<span class="val" style="color:{KO}">{ko_val}</span></div>'
        f'<div class="kpi-row"><span class="brand"><i style="background:{PEP}"></i>PepsiCo</span>'
        f'<span class="val" style="color:{PEP}">{pep_val}</span></div>'
        f'<div class="kpi-foot">{pie}</div>'
        f'<div class="kpi-win" style="color:{color}">▲ Ventaja {ganador}</div>'
        f'</div>'
    )


def base(fig, titulo, alto=320):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=TEXT), x=0.02, xanchor="left"),
        height=alto,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif", color=TEXT, size=12),
        legend=dict(orientation="h", yanchor="top", y=-0.08, x=0.5, xanchor="center"),
        bargap=0.3,
        bargroupgap=0.08,
    )
    return fig


def mostrar(fig):
    st.plotly_chart(fig, use_container_width=True, config=CFG, theme=None)


# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown(
    """
<style>
.stApp {background:#F4F5F7;}
header[data-testid="stHeader"] {background:transparent;}
#MainMenu, footer {visibility:hidden;}
.block-container {padding-top:1.6rem; padding-bottom:1.2rem; max-width:1500px;}
.stApp p, .stApp label, .stApp span, .stApp li {color:#1F2328;}
.title {font-size:2.2rem; font-weight:800; line-height:1.1;}
.title .vs {color:#9CA3AF; font-weight:600; font-size:1.6rem;}
.subtitle {color:#6B7280; font-size:.95rem; margin-top:6px;}
.kpi {background:#fff; border:1px solid #E8EAEE; border-radius:14px; padding:16px 18px;
      box-shadow:0 1px 3px rgba(16,24,40,.05); height:100%;}
.kpi-label {font-size:.74rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase;
            color:#6B7280; margin-bottom:10px;}
.kpi-row {display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap;
          gap:4px; margin:5px 0;}
.kpi .brand {display:flex; align-items:center; gap:7px; font-size:.84rem; color:#4B5563;}
.kpi .brand i {width:9px; height:9px; border-radius:50%; display:inline-block;}
.kpi .val {font-size:1.22rem; font-weight:800;}
.kpi-foot {font-size:.74rem; color:#6B7280; margin-top:10px; padding-top:8px; border-top:1px solid #F0F1F4;}
.kpi-win {font-size:.74rem; font-weight:700; margin-top:4px;}
div[data-testid="stPlotlyChart"] {background:#fff; border:1px solid #E8EAEE; border-radius:14px;
      padding:6px; box-shadow:0 1px 3px rgba(16,24,40,.05);}
.card {background:#fff; border:1px solid #E8EAEE; border-radius:14px; padding:18px 22px;
       box-shadow:0 1px 3px rgba(16,24,40,.05); height:100%;}
.card h4 {margin:0 0 12px 0; font-size:15px; color:#1F2328;}
.card ul {padding-left:18px; margin:0;}
.card li {margin-bottom:9px; font-size:.92rem; line-height:1.45;}
.note {font-size:.8rem; color:#6B7280; margin:6px 4px 0 4px; line-height:1.4;}
.spacer {height:14px;}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# ENCABEZADO
# ------------------------------------------------------------
top_l, top_r = st.columns([3, 1.4], vertical_alignment="center")
with top_l:
    st.markdown(
        f'<div class="title"><span style="color:{KO}">Coca-Cola</span> '
        f'<span class="vs">vs.</span> <span style="color:{PEP}">PepsiCo</span></div>'
        '<div class="subtitle">Modelo de negocio · Finanzas · Marketing — '
        'datos oficiales presentados ante la SEC</div>',
        unsafe_allow_html=True,
    )
with top_r:
    periodo = st.radio("Período", list(DATA.keys()), horizontal=True, label_visibility="collapsed")

k = DATA[periodo]["ko"]
p = DATA[periodo]["pep"]

var_k = (k["ingresos"] / k["prev"] - 1) * 100
var_p = (p["ingresos"] / p["prev"] - 1) * 100
mn_k = k["neto"] / k["ingresos"] * 100
mn_p = p["neto"] / p["ingresos"] * 100
pub_k = PUBLICIDAD_2025["ko"] / VENTAS_2025["ko"] * 100
pub_p = PUBLICIDAD_2025["pep"] / VENTAS_2025["pep"] * 100
pub_p_total = PUBLICIDAD_2025["pep_total"] / VENTAS_2025["pep"] * 100

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# FILA 1 · 5 PARÁMETROS CLAVE
# ------------------------------------------------------------
cards = [
    kpi("Ingresos netos", usd(k["ingresos"]), usd(p["ingresos"]),
        f"Variación interanual: {pct(var_k, 1, True)} vs. {pct(var_p, 1, True)}",
        lider(k["ingresos"], p["ingresos"])),
    kpi("Margen operativo", pct(k["m_op"]), pct(p["m_op"]),
        f"Ajustado: {pct(k['m_op_aj'])} vs. {pct(p['m_op_aj'])}",
        lider(k["m_op"], p["m_op"])),
    kpi("Beneficio neto", usd(k["neto"]), usd(p["neto"]),
        f"Margen neto: {pct(mn_k)} vs. {pct(mn_p)}",
        lider(k["neto"], p["neto"])),
    kpi("Crecimiento orgánico", pct(k["organico"], 1, True), pct(p["organico"], 1, True),
        "Sin efecto cambiario ni adquisiciones",
        lider(k["organico"], p["organico"])),
    kpi("Inversión publicitaria", usd(PUBLICIDAD_2025["ko"]), usd(PUBLICIDAD_2025["pep"]),
        f"{pct(pub_k)} vs. {pct(pub_p)} de las ventas · año 2025",
        lider(pub_k, pub_p)),
]
for col, html in zip(st.columns(5, gap="small"), cards):
    col.markdown(html, unsafe_allow_html=True)

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# FILA 2 · MODELO DE NEGOCIO · RENTABILIDAD · CRECIMIENTO
# ------------------------------------------------------------
c1, c2, c3 = st.columns([1, 1.25, 1], gap="small")

with c1:
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]])
    fig.add_trace(go.Pie(labels=["Bebidas"], values=[100], hole=0.7, sort=False,
                         marker=dict(colors=[KO]), textinfo="none",
                         hovertemplate="Coca-Cola · %{label}: %{value}%<extra></extra>"), 1, 1)
    fig.add_trace(go.Pie(labels=list(MIX_PEP.keys()), values=list(MIX_PEP.values()), hole=0.7,
                         sort=False, marker=dict(colors=[PEP, PEP_LIGHT]), textinfo="none",
                         hovertemplate="PepsiCo · %{label}: %{value}%<extra></extra>"), 1, 2)
    fig.add_annotation(x=0.225, y=0.5, xref="paper", yref="paper", showarrow=False,
                       text=f"<b style='color:{KO}'>Coca-Cola</b><br><b>100%</b><br>bebidas",
                       font=dict(size=13, color=TEXT))
    fig.add_annotation(x=0.775, y=0.5, xref="paper", yref="paper", showarrow=False,
                       text=f"<b style='color:{PEP}'>PepsiCo</b><br><b>58%</b> alimentos<br><b>42%</b> bebidas",
                       font=dict(size=13, color=TEXT))
    base(fig, "Modelo de negocio: ¿de qué viven?")
    fig.update_layout(showlegend=False)
    mostrar(fig)
    st.markdown(
        '<p class="note">Coca-Cola vende principalmente concentrado y licencia sus marcas a embotelladores. '
        'PepsiCo fabrica y distribuye gran parte de lo que vende (snacks como Lay\'s y Doritos, y bebidas).</p>',
        unsafe_allow_html=True,
    )

with c2:
    cats = ["Margen bruto", "Margen operativo", "Margen neto"]
    ko_vals = [k["m_bruto"], k["m_op"], mn_k]
    pep_vals = [p["m_bruto"], p["m_op"], mn_p]
    fig = go.Figure()
    fig.add_bar(y=cats, x=ko_vals, name="Coca-Cola", orientation="h", marker_color=KO,
                text=[f"US$ {fmt(v)}" for v in ko_vals], textposition="outside",
                hovertemplate="Coca-Cola · %{y}: %{x:.1f}%<extra></extra>")
    fig.add_bar(y=cats, x=pep_vals, name="PepsiCo", orientation="h", marker_color=PEP,
                text=[f"US$ {fmt(v)}" for v in pep_vals], textposition="outside",
                hovertemplate="PepsiCo · %{y}: %{x:.1f}%<extra></extra>")
    base(fig, "Rentabilidad: de cada US$ 100 vendidos, cuánto queda")
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(visible=False, range=[0, 78])
    mostrar(fig)

with c3:
    per = list(DATA.keys())
    etiquetas = ["2025", "1S 2026"]
    ko_org = [DATA[x]["ko"]["organico"] for x in per]
    pep_org = [DATA[x]["pep"]["organico"] for x in per]
    fig = go.Figure()
    fig.add_bar(x=etiquetas, y=ko_org, name="Coca-Cola", marker_color=KO,
                text=[pct(v, 1, True) for v in ko_org], textposition="outside",
                hovertemplate="Coca-Cola · %{x}: %{y:.1f}%<extra></extra>")
    fig.add_bar(x=etiquetas, y=pep_org, name="PepsiCo", marker_color=PEP,
                text=[pct(v, 1, True) for v in pep_org], textposition="outside",
                hovertemplate="PepsiCo · %{x}: %{y:.1f}%<extra></extra>")
    base(fig, "Crecimiento orgánico de ventas")
    fig.update_layout(barmode="group")
    fig.update_yaxes(visible=False, range=[0, max(ko_org + pep_org) * 1.3])
    fig.update_xaxes(showgrid=False)
    mostrar(fig)

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# FILA 3 · MARKETING + LECTURA RÁPIDA
# ------------------------------------------------------------
c4, c5 = st.columns([1.25, 1], gap="small")

with c4:
    etiquetas = ["Coca-Cola · publicidad", "PepsiCo · publicidad", "PepsiCo · publicidad + marketing"]
    valores = [PUBLICIDAD_2025["ko"], PUBLICIDAD_2025["pep"], PUBLICIDAD_2025["pep_total"]]
    sobre_ventas = [pub_k, pub_p, pub_p_total]
    fig = go.Figure()
    fig.add_bar(y=etiquetas, x=valores, orientation="h", marker_color=[KO, PEP, PEP_LIGHT],
                text=[f"{usd(v)} · {pct(s)} de las ventas" for v, s in zip(valores, sobre_ventas)],
                textposition="outside", hovertemplate="%{y}: US$ %{x:.1f} mil M<extra></extra>")
    base(fig, "Inversión publicitaria 2025", alto=270)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(visible=False, range=[0, 10.5])
    mostrar(fig)

with c5:
    ratio = p["ingresos"] / k["ingresos"]
    items = [
        f"<b>Escala vs. rentabilidad:</b> PepsiCo factura {fmt(ratio)} veces más, pero Coca-Cola gana más: "
        f"{usd(k['neto'])} contra {usd(p['neto'])} de beneficio neto.",
        "<b>Dos modelos:</b> Coca-Cola cobra por marca y concentrado; PepsiCo fabrica y distribuye. "
        "Más ventas, pero también más costos.",
        f"<b>Crecimiento:</b> las ventas orgánicas de Coca-Cola crecieron {pct(k['organico'], 1, True)} "
        f"contra {pct(p['organico'], 1, True)} de PepsiCo.",
        f"<b>Marketing:</b> Coca-Cola destina {pct(pub_k)} de sus ventas a publicidad, "
        f"el triple que PepsiCo ({pct(pub_p)}).",
    ]
    if periodo == "1er semestre 2026":
        items.append(
            "<b>Efecto Mundial 2026:</b> la campaña global de Coca-Cola superó los 60.000 millones de "
            "impresiones digitales y la marca Coca-Cola creció 5% en volumen en el 2º trimestre."
        )
    st.markdown(
        '<div class="card"><h4>Lectura rápida</h4><ul>'
        + "".join(f"<li>{i}</li>" for i in items)
        + "</ul></div>",
        unsafe_allow_html=True,
    )

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# NOTAS Y FUENTES
# ------------------------------------------------------------
with st.expander("Notas metodológicas y fuentes"):
    st.markdown(
        """
- **Cifras GAAP reportadas**, en US$. El margen **ajustado** es el *comparable* (Coca-Cola) o *core* (PepsiCo), que excluye partidas extraordinarias.
- **1er semestre 2026:** Coca-Cola informa 6 meses al 3/7/2026; PepsiCo, 24 semanas al 13/6/2026.
- **Beneficio neto 2025:** el de Coca-Cola incluye ganancias por venta de participaciones y un deterioro de BODYARMOR; el de PepsiCo, deterioros de marcas (Rockstar, entre otras).
- **Publicidad:** Coca-Cola informa "costos de publicidad". PepsiCo separa publicidad (US$ 3,4 mil M) del total de publicidad y marketing (US$ 5,4 mil M). No hay dato semestral.
- **Crecimiento orgánico:** medida no-GAAP de cada empresa (excluye tipo de cambio y compras/ventas de negocios).
- **Mix de PepsiCo:** Informe Anual 2025 (58% alimentos / 42% bebidas).

**Fuentes**
- [Coca-Cola · Resultados 4T y año 2025 (SEC)](https://www.sec.gov/Archives/edgar/data/21344/000162828026006642/a2025q4earningsreleaseex-9.htm)
- [Coca-Cola · Formulario 10-K 2025 (SEC)](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm)
- [Coca-Cola · Resultados 2T 2026 (SEC)](https://www.sec.gov/Archives/edgar/data/0000021344/000162828026049922/a2026q2earningsreleaseex-9.htm)
- [PepsiCo · Resultados 4T y año 2025](https://investors.pepsico.com/docs/pepsico-5v9wci20/media/Files/investors/q4-2025-earnings-release.pdf)
- [PepsiCo · Formulario 10-K 2025 (SEC)](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm)
- [PepsiCo · Informe Anual 2025 (SEC)](https://www.sec.gov/Archives/edgar/data/77476/000130817926000172/pep015012-ars.pdf)
- [PepsiCo · Resultados 2T 2026 (SEC)](https://www.sec.gov/Archives/edgar/data/0000077476/000007747626000037/q220268-kxexhibit991.htm)
"""
    )

st.markdown(
    '<p class="note" style="text-align:center">Dashboard elaborado con datos oficiales · Octubre 2026</p>',
    unsafe_allow_html=True,
)
