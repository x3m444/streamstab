import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(__file__))
from utils.calcul_electric import genereaza_bom, calcul_module, selectie_cutie, REZERVA_PROCENT

st.set_page_config(
    page_title="Configurator Tablou Electric",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Configurator Tablou Electric")
st.caption("Completează pașii de mai jos pentru a genera lista de materiale")

# ─── PASUL 1 — Date de bază ───────────────────────────────────────────────────
st.header("Pasul 1 — Date de bază")

col1, col2, col3 = st.columns(3)

with col1:
    alimentare = st.selectbox("Tip alimentare", ["Monofazat", "Trifazat"])

with col2:
    curent_bransament = st.selectbox("Curent branșament (A)", [25, 32, 40, 50, 63], index=1)

with col3:
    tip_mcb = st.selectbox(
        "Tip MCB circuite",
        ["1P", "1P+N"],
        help="1P — mai compact și economic | 1P+N — întrerupere omnipolară"
    )

col4, col5 = st.columns(2)
with col4:
    nr_iluminat = st.number_input("Nr. circuite iluminat", min_value=0, max_value=20, value=2, step=1)
with col5:
    nr_prize = st.number_input("Nr. circuite prize", min_value=0, max_value=20, value=4, step=1)

# ─── Consumatori speciali ──────────────────────────────────────────────────────
CONSUMATORI_PREDEFINITI = {
    "Boiler electric":              2000,
    "Aparat aer condiționat":       1500,
    "Mașină de spălat":             2200,
    "Uscător de rufe":              2500,
    "Mașină de spălat vase":        1800,
    "Cuptor electric":              3500,
    "Plită electrică":              7000,
    "Pompă piscină / hidrofor":     1100,
    "Încălzire electrică":          2000,
    "Stație încărcare VE (wallbox)": 7400,
    "Altul...":                     1000,
}

st.subheader("Consumatori speciali")
nr_speciali = st.number_input("Câți consumatori speciali?", min_value=0, max_value=10, value=0, step=1)

speciali = []
if nr_speciali > 0:
    for i in range(int(nr_speciali)):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            tip = st.selectbox(
                f"Tip consumator #{i+1}",
                list(CONSUMATORI_PREDEFINITI.keys()),
                key=f"tip_{i}"
            )
        with c2:
            putere_default = CONSUMATORI_PREDEFINITI[tip]
            putere = st.number_input(
                f"Putere (W) #{i+1}",
                min_value=100, max_value=20000,
                value=putere_default, step=100,
                key=f"put_{i}"
            )
        with c3:
            if tip == "Altul...":
                denumire = st.text_input(f"Denumire #{i+1}", value="Consumator", key=f"den_{i}")
            else:
                denumire = tip
                st.text_input(f"Denumire #{i+1}", value=tip, disabled=True, key=f"den_{i}")
        with c4:
            trifazat_c = False
            if alimentare == "Trifazat":
                trifazat_c = st.checkbox(f"Trifazat #{i+1}", key=f"tri_{i}")
        speciali.append({"denumire": denumire, "putere_w": putere, "trifazat": trifazat_c})

st.divider()

# ─── PASUL 2 — Upgrade-uri opționale ─────────────────────────────────────────
st.header("Pasul 2 — Upgrade-uri opționale")

col_u1, col_u2, col_u3 = st.columns(3)

with col_u1:
    spd = st.checkbox(
        "SPD — Protecție supratensiune",
        help="Recomandat conform I7/2023 pentru protecția echipamentelor sensibile"
    )

with col_u2:
    label_releu = "Releu monitorizare faze + contactor" if alimentare == "Trifazat" \
        else "Releu protecție tensiune + contactor"
    releu_tensiune = st.checkbox(
        label_releu,
        help="Protejează echipamentele la variații mari de tensiune sau pierdere fază"
    )

with col_u3:
    pass

st.divider()

# ─── PASUL 3 — Generare BOM ───────────────────────────────────────────────────
st.header("Pasul 3 — Rezultat")

if st.button("Generează lista de materiale", type="primary"):
    config = {
        "alimentare": alimentare,
        "curent_bransament": curent_bransament,
        "tip_mcb": tip_mcb,
        "nr_iluminat": int(nr_iluminat),
        "nr_prize": int(nr_prize),
        "speciali": speciali,
        "spd": spd,
        "releu_tensiune": releu_tensiune,
    }

    bom = genereaza_bom(config)
    module_utilizate, rezerva, module_total = calcul_module(bom)
    cutie = selectie_cutie(module_total)

    # Sumar tablou
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Alimentare", alimentare)
    col_s2.metric("Module utilizate", module_utilizate)
    col_s3.metric(f"Rezervă {int(REZERVA_PROCENT*100)}% (I7)", rezerva)
    col_s4.metric("Cutie recomandată", cutie)

    st.subheader("Lista de materiale")
    df = pd.DataFrame(bom)
    df.columns = ["Componentă", "Cantitate", "Categorie"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export Excel
    excel_path = "/tmp/bom_tablou.xlsx"
    df.to_excel(excel_path, index=False)
    with open(excel_path, "rb") as f:
        st.download_button(
            label="Descarcă BOM (Excel)",
            data=f,
            file_name="tablou_electric_bom.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
