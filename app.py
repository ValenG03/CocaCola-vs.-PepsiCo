import base64
import io
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
from PIL import Image

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(page_title="Coca-Cola vs. PepsiCo", page_icon="🥤", layout="wide")

KO = "#E61A27"
PEP = "#0B4EA2"
PEP_LIGHT = "#8FB3E3"
KO_SOFT = "rgba(230,26,39,0.10)"
PEP_SOFT = "rgba(11,78,162,0.10)"
TEXT = "#1F2328"
MUTED = "#6B7280"
GRID = "#EEF0F3"
AXIS = "#CBD0D8"
FONT = "Inter, sans-serif"
H = 400  # altura única de todos los bloques de gráficos
CFG = {"displayModeBar": False}
IMAGEN_BANNER = "PepsiCoca.png"  # imagen subida al repo, en la misma carpeta que app.py

# ============================================================
# DATOS OFICIALES (US$ miles de millones · GAAP)
# Fuente: comunicados de resultados, 10-Q y 10-K presentados ante la SEC
# ============================================================
BASE = {
    "2025": {
        "ko": {"ingresos": 47.941, "prev": 47.061, "bruto": 29.544, "op": 13.762,
               "op_aj": 15.013, "m_op_aj": 31.2, "neto": 13.107, "organico": 5.0},
        "pep": {"ingresos": 93.925, "prev": 91.854, "bruto": 50.859, "op": 11.498,
                "op_aj": 14.912, "m_op_aj": 15.9, "neto": 8.240, "organico": 1.7},
    },
    "1S26": {
        "ko": {"ingresos": 25.852, "prev": 23.664, "bruto": 16.267, "op": 9.031,
               "op_aj": 9.058, "m_op_aj": 35.0, "neto": 8.349, "organico": 8.0},
        "pep": {"ingresos": 43.624, "prev": 40.645, "bruto": 23.842, "op": 7.236,
                "op_aj": 7.117, "m_op_aj": 16.3, "neto": 5.308, "organico": 2.5},
    },
}

TRIMESTRES = ["T1 25", "T2 25", "T3 25", "T4 25", "T1 26", "T2 26"]
ORG_Q = {"ko": [6.0, 5.0, 6.0, 5.0, 10.0, 6.0], "pep": [1.2, 2.1, 1.3, 2.1, 2.6, 2.4]}
ING_Q = {"ko": [11.129, 12.535, 12.455, 11.822, 12.472, 13.380],
         "pep": [17.919, 22.726, 23.937, 29.343, 19.443, 24.181]}

PUB_2025 = {"ko": 5.4, "pep": 3.4, "pep_total": 5.4}
VENTAS_2025 = {"ko": 47.941, "pep": 93.925}
MIX_PEP = {"Alimentos": 58, "Bebidas": 42}

PERIODOS = {
    "2025 + 1S 2026": {"claves": ["2025", "1S26"], "detalle": "Acumulado enero 2025 – junio 2026 · 18 meses",
                       "comp": "vs. 2024 + 1S 2025", "rango": None},
    "Año 2025": {"claves": ["2025"], "detalle": "Año completo · enero – diciembre 2025",
                 "comp": "vs. 2024", "rango": (-0.5, 3.5)},
    "1er semestre 2026": {"claves": ["1S26"], "detalle": "Primer semestre · enero – junio 2026",
                          "comp": "vs. 1S 2025", "rango": (3.5, 5.5)},
}
DEFAULT = "2025 + 1S 2026"


# ============================================================
# BANNER DE PORTADA
# ============================================================
@st.cache_data
def cargar_banner(nombre):
    ruta = Path(__file__).parent / nombre
    if not ruta.exists():
        return None
    img = Image.open(ruta).convert("RGB")
    w, h = img.size
    mitad = w // 2
    # Invierte las mitades: Coca-Cola (rojo) a la izquierda, Pepsi (azul) a la derecha
    izq = img.crop((0, 0, mitad, h))
    der = img.crop((mitad, 0, w, h))
    nueva = Image.new("RGB", (w, h))
    nueva.paste(der, (0, 0))
    nueva.paste(izq, (w - mitad, 0))
    # Recorta el espacio vacío de arriba y abajo
    nueva = nueva.crop((0, int(h * 0.2), w, int(h * 0.8)))
    color_izq = nueva.getpixel((4, 4))
    color_der = nueva.getpixel((nueva.width - 5, 4))
    buffer = io.BytesIO()
    nueva.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode(), color_izq, color_der


# ============================================================
# FUNCIONES
# ============================================================
def fmt(x, d=1):
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=1, signo=False):
    return ("+" if signo and x > 0 else "") + fmt(x, d) + "%"


def usd(x):
    return f"US$ {fmt(x)} mil M"


def metricas(emp, claves):
    campos = ["ingresos", "prev", "bruto", "op", "op_aj", "neto"]
    t = {c: sum(BASE[k][emp][c] for k in claves) for c in campos}
    return {
        "ingresos": t["ingresos"],
        "neto": t["neto"],
        "var": (t["ingresos"] / t["prev"] - 1) * 100,
        "m_bruto": t["bruto"] / t["ingresos"] * 100,
        "m_op": t["op"] / t["ingresos"] * 100,
        "m_neto": t["neto"] / t["ingresos"] * 100,
        "m_op_aj": BASE[claves[0]][emp]["m_op_aj"] if len(claves) == 1 else t["op_aj"] / t["ingresos"] * 100,
        "org": [BASE[k][emp]["organico"] for k in claves],
    }


def org_txt(vals):
    return " → ".join(pct(v, 1, True) for v in vals)


def lider(a, b):
    return "Coca-Cola" if a > b else "PepsiCo"


def kpi(label, ko_val, pep_val, pie, ganador):
    color, soft = (KO, KO_SOFT) if ganador == "Coca-Cola" else (PEP, PEP_SOFT)
    return (
        f'<div class="kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-brand"><i style="background:{KO}"></i>Coca-Cola</div>'
        f'<div class="kpi-val" style="color:{KO}">{ko_val}</div>'
        f'<div class="kpi-brand"><i style="background:{PEP}"></i>PepsiCo</div>'
        f'<div class="kpi-val" style="color:{PEP}">{pep_val}</div>'
        f'<div class="kpi-foot"><span>{pie}</span></div>'
        f'<div class="kpi-win" style="color:{color};background:{soft}">▲ Ventaja {ganador}</div>'
        f'</div>'
    )


def base(fig, titulo, t=100, b=64, l=64, r=28, leyenda=True):
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", font=dict(size=16, color=TEXT, family=FONT),
                   x=0.5, xanchor="center", xref="paper", y=0.975, yanchor="top"),
        height=H,
        margin=dict(l=l, r=r, t=t, b=b),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT, color=TEXT, size=12),
        separators=",.",
        showlegend=leyenda,
        legend=dict(orientation="h", x=1, xanchor="right", y=1.06, yanchor="bottom",
                    font=dict(size=12, family=FONT), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(font=dict(family=FONT, size=12), bgcolor="white"),
        bargap=0.32,
        bargroupgap=0.08,
    )
    return fig


def ejes(fig, x_titulo=None, y_titulo=None):
    estilo = dict(showline=True, linecolor=AXIS, linewidth=1, ticks="outside", tickcolor=AXIS,
                  ticklen=5, automargin=True, zeroline=False,
                  tickfont=dict(size=12, color=TEXT, family=FONT),
                  title_font=dict(size=12, color=MUTED, family=FONT))
    fig.update_xaxes(**estilo, title_text=x_titulo, title_standoff=10)
    fig.update_yaxes(**estilo, title_text=y_titulo, title_standoff=10)
    return fig


def mostrar(fig):
    st.plotly_chart(fig, use_container_width=True, config=CFG, theme=None)


def espacio(px=26):
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)


# ============================================================
# ESTILO (una sola tipografía: Inter)
# ============================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{
    font-family: 'Inter', sans-serif !important;
}}
.stApp {{background:#F4F5F7;}}
header[data-testid="stHeader"] {{background:transparent;}}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{display:none;}}
.block-container {{padding-top:1.2rem; padding-bottom:1.4rem; max-width:1520px;}}
.stApp p, .stApp label, .stApp span, .stApp li {{color:{TEXT};}}

/* ---------- Banner ---------- */
.banner {{position:relative; height:190px; border-radius:18px; overflow:hidden;
          display:flex; align-items:center; justify-content:center;
          box-shadow:0 6px 20px rgba(16,24,40,.12); margin-bottom:24px;}}
.banner img {{height:100%; max-width:100%; object-fit:contain; display:block;}}
.vs-badge {{position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
            width:46px; height:46px; border-radius:50%; background:#fff;
            display:flex; align-items:center; justify-content:center;
            font-size:.85rem; font-weight:800; letter-spacing:.04em; color:{TEXT};
            box-shadow:0 4px 14px rgba(0,0,0,.25);}}

/* ---------- Encabezado centrado ---------- */
.header-center {{text-align:center; margin:4px auto 0 auto; max-width:900px;}}
.title {{font-size:2.15rem; font-weight:800; line-height:1.1; letter-spacing:-0.02em;}}
.title .vs {{color:#9CA3AF; font-weight:600; font-size:1.5rem;}}
.tagline {{font-size:1.05rem; font-weight:600; color:#374151; margin-top:8px; letter-spacing:-0.005em;}}
.subtitle {{color:{MUTED}; font-size:.86rem; margin-top:4px;}}
.pill-wrap {{text-align:center;}}
.pill {{display:inline-flex; align-items:center; gap:8px; background:#fff; border:1px solid #E5E7EB;
        border-radius:999px; padding:6px 14px; font-size:.82rem; font-weight:600; color:{TEXT};
        margin:6px 0 4px 0;}}
.pill b {{width:8px; height:8px; border-radius:50%; background:linear-gradient(90deg,{KO} 50%,{PEP} 50%);}}
div[data-testid="stSegmentedControl"], div[data-testid="stButtonGroup"] {{display:flex; justify-content:center;}}

/* ---------- Tarjetas KPI: todo centrado y alineado ---------- */
.kpi {{background:#fff; border:1px solid #E8EAEE; border-radius:16px; padding:18px 16px 16px 16px;
       box-shadow:0 1px 3px rgba(16,24,40,.05); height:276px; box-sizing:border-box;
       display:flex; flex-direction:column; align-items:center; text-align:center;
       transition:all .18s ease;}}
.kpi:hover {{transform:translateY(-3px); box-shadow:0 10px 24px rgba(16,24,40,.10);}}
.kpi-label {{font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
             color:{MUTED}; margin-bottom:12px;}}
.kpi-brand {{display:flex; align-items:center; justify-content:center; gap:7px;
             font-size:.8rem; color:#4B5563; font-weight:500;}}
.kpi-brand i {{width:8px; height:8px; border-radius:50%; display:inline-block;}}
.kpi-val {{font-size:clamp(1.02rem, 1.35vw, 1.32rem); font-weight:800; margin:2px 0 9px 0;
           white-space:nowrap; letter-spacing:-0.01em;}}
.kpi-foot {{width:100%; height:46px; margin-top:auto; border-top:1px solid #F0F1F4;
            display:flex; align-items:center; justify-content:center; box-sizing:border-box;
            padding-top:6px;}}
.kpi-foot span {{font-size:.72rem; color:{MUTED}; line-height:1.35;}}
.kpi-win {{font-size:.7rem; font-weight:700; margin-top:8px; padding:5px 12px; border-radius:999px;
           white-space:nowrap;}}

/* ---------- Bloques de gráficos ---------- */
div[data-testid="stPlotlyChart"] {{background:#fff; border:1px solid #E8EAEE; border-radius:16px;
      overflow:hidden; box-shadow:0 1px 3px rgba(16,24,40,.05); transition:box-shadow .18s ease;}}
div[data-testid="stPlotlyChart"]:hover {{box-shadow:0 10px 24px rgba(16,24,40,.08);}}

.card {{background:#fff; border:1px solid #E8EAEE; border-radius:16px; padding:20px 22px;
        box-shadow:0 1px 3px rgba(16,24,40,.05); height:{H + 2}px; box-sizing:border-box;
        overflow-y:auto; transition:box-shadow .18s ease;}}
.card:hover {{box-shadow:0 10px 24px rgba(16,24,40,.08);}}
.card-title {{font-size:16px; font-weight:700; color:{TEXT}; margin-bottom:16px; text-align:center;}}
.ins {{border-left:3px solid #E5E7EB; padding:2px 0 2px 11px; margin-bottom:12px;
       font-size:.84rem; line-height:1.45; color:{TEXT};}}
.ins b {{display:block; font-size:.76rem; text-transform:uppercase; letter-spacing:.05em; margin-bottom:2px;}}
.note {{font-size:.78rem; color:{MUTED}; text-align:center; margin-top:6px;}}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# BANNER AL COMIENZO DE LA PÁGINA
# ============================================================
banner = cargar_banner(IMAGEN_BANNER)
if banner:
    b64, color_izq, color_der = banner
    st.markdown(
        f'<div class="banner" style="background:linear-gradient(90deg, rgb{color_izq} 50%, rgb{color_der} 50%);">'
        f'<img src="data:image/png;base64,{b64}" alt="Coca-Cola vs. PepsiCo">'
        f'<span class="vs-badge">VS</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.warning(f"No se encontró la imagen '{IMAGEN_BANNER}' en la carpeta del repositorio.")

# ============================================================
# ENCABEZADO CENTRADO + SELECTOR DE PERÍODO
# ============================================================
st.markdown(
    f'<div class="header-center">'
    f'<div class="title"><span style="color:{KO}">Coca-Cola</span> '
    f'<span class="vs">vs.</span> <span style="color:{PEP}">PepsiCo</span></div>'
    '<div class="tagline">Análisis y comparación temporal del mercado de bebidas de consumo masivo</div>'
    '<div class="subtitle">Modelo de negocio · Finanzas · Marketing — datos oficiales presentados ante la SEC</div>'
    '</div>',
    unsafe_allow_html=True,
)
espacio(14)

_, centro, _ = st.columns([1, 2, 1])
with centro:
    sel = st.segmented_control("Período", list(PERIODOS.keys()), default=DEFAULT,
                               label_visibility="collapsed", key="periodo")

periodo = sel or DEFAULT
cfg = PERIODOS[periodo]
claves = cfg["claves"]
k = metricas("ko", claves)
p = metricas("pep", claves)
pub_k = PUB_2025["ko"] / VENTAS_2025["ko"] * 100
pub_p = PUB_2025["pep"] / VENTAS_2025["pep"] * 100
pub_p_total = PUB_2025["pep_total"] / VENTAS_2025["pep"] * 100

st.markdown(f'<div class="pill-wrap"><div class="pill"><b></b>{cfg["detalle"]}</div></div>',
            unsafe_allow_html=True)
espacio(14)

# ============================================================
# FILA 1 · 5 PARÁMETROS CLAVE
# ============================================================
cards = [
    kpi("Ingresos netos", usd(k["ingresos"]), usd(p["ingresos"]),
        f'Crecimiento {cfg["comp"]}<br>{pct(k["var"], 1, True)} / {pct(p["var"], 1, True)}',
        lider(k["ingresos"], p["ingresos"])),
    kpi("Margen operativo", pct(k["m_op"]), pct(p["m_op"]),
        f'Margen ajustado<br>{pct(k["m_op_aj"])} / {pct(p["m_op_aj"])}',
        lider(k["m_op"], p["m_op"])),
    kpi("Beneficio neto", usd(k["neto"]), usd(p["neto"]),
        f'Margen neto<br>{pct(k["m_neto"])} / {pct(p["m_neto"])}',
        lider(k["neto"], p["neto"])),
    kpi("Crecimiento orgánico", org_txt(k["org"]), org_txt(p["org"]),
        "2025 → 1S 2026<br>sin tipo de cambio ni M&A" if len(claves) > 1
        else "Sin efecto cambiario<br>ni adquisiciones",
        lider(k["org"][-1], p["org"][-1])),
    kpi("Inversión publicitaria", usd(PUB_2025["ko"]), usd(PUB_2025["pep"]),
        f"% de las ventas (2025)<br>{pct(pub_k)} / {pct(pub_p)}",
        lider(pub_k, pub_p)),
]
for col, html in zip(st.columns(5, gap="medium"), cards):
    col.markdown(html, unsafe_allow_html=True)

espacio(26)

# ============================================================
# FILA 2 · CURVAS DE CRECIMIENTO + MODELO DE NEGOCIO
# ============================================================
c1, c2 = st.columns([1.75, 1], gap="medium")

with c1:
    fig = go.Figure()
    series = [("ko", "Coca-Cola", KO, "top center"), ("pep", "PepsiCo", PEP, "bottom center")]
    for emp, nombre, color, pos in series:
        fig.add_scatter(
            x=TRIMESTRES, y=ORG_Q[emp], name=nombre, mode="lines+markers+text",
            line=dict(color=color, width=3.5, shape="spline", smoothing=0.9),
            marker=dict(size=10, color="white", line=dict(color=color, width=3)),
            text=[pct(v, 1, True) for v in ORG_Q[emp]], textposition=pos,
            textfont=dict(color=color, size=11, family=FONT),
            hovertemplate=f"<b>{nombre}</b>: %{{y:.1f}}%<extra></extra>",
            visible=True,
        )
    for emp, nombre, color, pos in series:
        fig.add_scatter(
            x=TRIMESTRES, y=ING_Q[emp], name=nombre, mode="lines+markers+text",
            line=dict(color=color, width=3.5, shape="spline", smoothing=0.9),
            marker=dict(size=10, color="white", line=dict(color=color, width=3)),
            text=[fmt(v) for v in ING_Q[emp]], textposition="top center",
            textfont=dict(color=color, size=11, family=FONT),
            hovertemplate=f"<b>{nombre}</b>: US$ %{{y:.1f}} mil M<extra></extra>",
            visible=False,
        )

    ann_org = [dict(x="T1 26", y=10, text="6 días extra<br>en el calendario", showarrow=True,
                    arrowhead=0, ax=-72, ay=-4, arrowcolor=MUTED,
                    font=dict(size=10, color=MUTED, family=FONT))]
    ann_ing = [dict(x="T4 25", y=29.343, text="T4 de PepsiCo<br>= 16 semanas", showarrow=True,
                    arrowhead=0, ax=-78, ay=-2, arrowcolor=MUTED,
                    font=dict(size=10, color=MUTED, family=FONT))]

    if cfg["rango"]:
        fig.add_vrect(x0=cfg["rango"][0], x1=cfg["rango"][1], fillcolor="#F3F4F6",
                      opacity=1, layer="below", line_width=0)
    fig.add_vline(x=3.5, line=dict(color="#D1D5DB", width=1, dash="dot"))

    base(fig, "Evolución del crecimiento trimestral", t=104, b=64, l=72)
    ejes(fig, x_titulo="Trimestre", y_titulo="Crecimiento orgánico (%)")
    fig.update_layout(
        annotations=ann_org,
        hovermode="x unified",
        updatemenus=[dict(
            type="buttons", direction="right", x=0, xanchor="left", y=1.06, yanchor="bottom",
            showactive=True, bgcolor="#F3F4F6", bordercolor="#E5E7EB", borderwidth=1,
            font=dict(size=11, color=TEXT, family=FONT), pad=dict(r=0, t=0, l=0, b=0),
            buttons=[
                dict(label="Crecimiento orgánico", method="update",
                     args=[{"visible": [True, True, False, False]},
                           {"yaxis.range": [0, 12.5], "yaxis.ticksuffix": "%",
                            "yaxis.title.text": "Crecimiento orgánico (%)", "annotations": ann_org}]),
                dict(label="Ingresos trimestrales", method="update",
                     args=[{"visible": [False, False, True, True]},
                           {"yaxis.range": [0, 35], "yaxis.ticksuffix": "",
                            "yaxis.title.text": "Ingresos (US$ mil M)", "annotations": ann_ing}]),
            ],
        )],
    )
    fig.update_yaxes(range=[0, 12.5], ticksuffix="%", showgrid=True, gridcolor=GRID)
    fig.update_xaxes(showgrid=False)
    mostrar(fig)

with c2:
    fig = go.Figure()
    fig.add_trace(go.Pie(labels=["Bebidas"], values=[100], hole=0.62, sort=False,
                         domain=dict(x=[0.05, 0.45], y=[0.04, 0.66]),
                         marker=dict(colors=[KO], line=dict(color="white", width=2)), textinfo="none",
                         hovertemplate="Coca-Cola · %{label}: %{value}%<extra></extra>"))
    fig.add_trace(go.Pie(labels=list(MIX_PEP.keys()), values=list(MIX_PEP.values()), hole=0.62, sort=False,
                         domain=dict(x=[0.55, 0.95], y=[0.04, 0.66]),
                         marker=dict(colors=[PEP, PEP_LIGHT], line=dict(color="white", width=2)),
                         textinfo="none",
                         hovertemplate="PepsiCo · %{label}: %{value}%<extra></extra>"))

    leyendas = [
        (0.25, f"<b style='color:{KO}'>Coca-Cola</b><br>"
               f"<span style='color:{KO}'>●</span> Bebidas <b>100%</b>"),
        (0.75, f"<b style='color:{PEP}'>PepsiCo</b><br>"
               f"<span style='color:{PEP}'>●</span> Alimentos <b>58%</b><br>"
               f"<span style='color:{PEP_LIGHT}'>●</span> Bebidas <b>42%</b>"),
    ]
    for x, texto in leyendas:
        fig.add_annotation(x=x, y=0.99, xref="paper", yref="paper",
                           xanchor="center", yanchor="top", align="center",
                           showarrow=False, text=texto,
                           font=dict(size=12, color=TEXT, family=FONT))

    fig.add_annotation(x=0.5, y=-0.02, xref="paper", yref="paper", xanchor="center", yanchor="top",
                       showarrow=False,
                       text="Coca-Cola vende concentrado y licencia marcas · PepsiCo fabrica y distribuye",
                       font=dict(size=11, color=MUTED, family=FONT))
    base(fig, "Modelo de negocio: ¿de qué viven?", t=58, b=46, l=16, r=16, leyenda=False)
    mostrar(fig)

espacio(26)

# ============================================================
# FILA 3 · RENTABILIDAD · MARKETING · LECTURA RÁPIDA
# ============================================================
c3, c4, c5 = st.columns(3, gap="medium")

with c3:
    cats = ["Margen bruto", "Margen operativo", "Margen neto"]
    ko_vals = [k["m_bruto"], k["m_op"], k["m_neto"]]
    pep_vals = [p["m_bruto"], p["m_op"], p["m_neto"]]
    fig = go.Figure()
    fig.add_bar(y=cats, x=ko_vals, name="Coca-Cola", orientation="h", marker_color=KO,
                text=[f"US$ {fmt(v)}" for v in ko_vals], textposition="outside", cliponaxis=False,
                textfont=dict(family=FONT, size=12, color=KO),
                hovertemplate="Coca-Cola · %{y}: %{x:.1f}%<extra></extra>")
    fig.add_bar(y=cats, x=pep_vals, name="PepsiCo", orientation="h", marker_color=PEP,
                text=[f"US$ {fmt(v)}" for v in pep_vals], textposition="outside", cliponaxis=False,
                textfont=dict(family=FONT, size=12, color=PEP),
                hovertemplate="PepsiCo · %{y}: %{x:.1f}%<extra></extra>")
    base(fig, "De cada US$ 100 vendidos, cuánto queda", t=96, b=64, l=24, r=36)
    ejes(fig, x_titulo="% sobre las ventas", y_titulo=None)
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(range=[0, 85], ticksuffix="%", dtick=20, showgrid=True, gridcolor=GRID)
    mostrar(fig)

with c4:
    etiquetas = ["Coca-Cola", "PepsiCo", "PepsiCo<br>(+ marketing)"]
    valores = [PUB_2025["ko"], PUB_2025["pep"], PUB_2025["pep_total"]]
    sobre_ventas = [pub_k, pub_p, pub_p_total]
    fig = go.Figure()
    fig.add_bar(x=etiquetas, y=valores, marker_color=[KO, PEP, PEP_LIGHT], width=0.55,
                text=[f"<b>US$ {fmt(v)} mil M</b><br>{pct(s)} de ventas" for v, s in zip(valores, sobre_ventas)],
                textposition="outside", cliponaxis=False,
                textfont=dict(family=FONT, size=12, color=TEXT),
                hovertemplate="%{x}: US$ %{y:.1f} mil M<extra></extra>")
    base(fig, "Inversión publicitaria 2025", t=70, b=72, l=72, r=24, leyenda=False)
    ejes(fig, x_titulo=None, y_titulo="US$ miles de millones")
    fig.update_yaxes(range=[0, 8], dtick=2, showgrid=True, gridcolor=GRID)
    fig.update_xaxes(showgrid=False)
    mostrar(fig)

with c5:
    ratio = p["ingresos"] / k["ingresos"]
    items = [
        ("Escala vs. rentabilidad", KO,
         f"PepsiCo factura {fmt(ratio)} veces más, pero Coca-Cola gana más: "
         f"{usd(k['neto'])} contra {usd(p['neto'])}."),
        ("Dos modelos", PEP,
         "Coca-Cola cobra por marca y concentrado; PepsiCo fabrica y distribuye. Más ventas, pero más costos."),
        ("Crecimiento", KO,
         f"Coca-Cola creció más rápido en todos los trimestres: {org_txt(k['org'])} contra {org_txt(p['org'])}."),
        ("Marketing", PEP,
         f"Coca-Cola invierte {pct(pub_k)} de sus ventas en publicidad, el triple que PepsiCo ({pct(pub_p)})."),
    ]
    if "1S26" in claves:
        items.append(("Efecto Mundial 2026", KO,
                      "La campaña global de Coca-Cola superó 60.000 millones de impresiones digitales "
                      "y la marca creció 5% en volumen en el 2º trimestre."))
    html = '<div class="card"><div class="card-title">Lectura rápida</div>'
    for titulo, color, texto in items:
        html += f'<div class="ins" style="border-left-color:{color}"><b style="color:{color}">{titulo}</b>{texto}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

espacio(26)

# ============================================================
# NOTAS Y FUENTES
# ============================================================
with st.expander("Notas metodológicas y fuentes"):
    st.markdown(
        """
- **Cifras GAAP reportadas**, en US$. El margen **ajustado** es el *comparable* (Coca-Cola) o *core* (PepsiCo), que excluye partidas extraordinarias.
- **Acumulado 2025 + 1S 2026:** ingresos y beneficios sumados; los márgenes se calculan sobre esa suma. El crecimiento orgánico no se puede sumar, por eso se muestra la evolución 2025 → 1S 2026.
- **Calendarios:** el 1er semestre de Coca-Cola son 6 meses al 3/7/2026; el de PepsiCo, 24 semanas al 13/6/2026. PepsiCo reporta trimestres de 12 semanas y un 4º trimestre de 16 semanas.
- **T1 2026 de Coca-Cola:** tuvo seis días más que el T1 2025, lo que infla su crecimiento de ese trimestre.
- **Beneficio neto 2025:** el de Coca-Cola incluye ganancias por venta de participaciones y un deterioro de BODYARMOR; el de PepsiCo, deterioros de marcas (Rockstar, entre otras).
- **Publicidad:** Coca-Cola informa "costos de publicidad". PepsiCo separa publicidad (US$ 3,4 mil M) del total de publicidad y marketing (US$ 5,4 mil M). Solo hay dato anual.
- **Mix de PepsiCo:** Informe Anual 2025 (58% alimentos / 42% bebidas).

**Fuentes (SEC y sitios oficiales de inversores)**
- Coca-Cola: [Resultados T1 2025](https://www.sec.gov/Archives/edgar/data/21344/000002134425000024/a2025q1earningsreleaseex-9.htm) · [T2 2025](https://www.sec.gov/Archives/edgar/data/21344/000002134425000054/a2025q2earningsreleaseex-9.htm) · [T3 2025](https://www.sec.gov/Archives/edgar/data/21344/000162828025045577/a2025q3earningsreleaseex-9.htm) · [T4 y año 2025](https://www.sec.gov/Archives/edgar/data/21344/000162828026006642/a2025q4earningsreleaseex-9.htm) · [10-K 2025](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm) · [T1 2026](https://www.sec.gov/Archives/edgar/data/0000021344/000162828026027723/a2026q1earningsreleaseex-9.htm) · [T2 2026](https://www.sec.gov/Archives/edgar/data/0000021344/000162828026049922/a2026q2earningsreleaseex-9.htm)
- PepsiCo: [Resultados T1 2025](https://www.sec.gov/Archives/edgar/data/77476/000007747625000022/q120258-kxexhibit991.htm) · [T2 2025](https://www.sec.gov/Archives/edgar/data/77476/000007747625000046/q220258-kxexhibit991.htm) · [T3 2025](https://www.sec.gov/Archives/edgar/data/77476/000007747625000055/q320258-kxexhibit991.htm) · [T4 y año 2025](https://investors.pepsico.com/docs/pepsico-5v9wci20/media/Files/investors/q4-2025-earnings-release.pdf) · [10-K 2025](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm) · [Informe Anual 2025](https://www.sec.gov/Archives/edgar/data/77476/000130817926000172/pep015012-ars.pdf) · [T1 2026](https://www.sec.gov/Archives/edgar/data/77476/000007747626000019/q120268-kxexhibit991.htm) · [T2 2026](https://www.sec.gov/Archives/edgar/data/0000077476/000007747626000037/q220268-kxexhibit991.htm)
"""
    )

st.markdown('<p class="note">Dashboard elaborado con datos oficiales · Octubre 2026</p>', unsafe_allow_html=True)
