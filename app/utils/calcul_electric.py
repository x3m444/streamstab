import math


def calcul_curent(putere_w, tensiune_v=230, cos_phi=0.9):
    return putere_w / (tensiune_v * cos_phi)


def selectie_mcb_special(putere_w, trifazat=False):
    tensiune = 400 if trifazat else 230
    curent = calcul_curent(putere_w, tensiune)
    scara = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63]
    for val in scara:
        if val >= curent * 1.25:
            return val
    return 63


def calcul_numar_rccb(nr_iluminat, nr_prize):
    total = nr_iluminat + nr_prize
    return math.ceil(total / 8)


def genereaza_bom(config):
    bom = []
    alimentare = config["alimentare"]
    curent_bransament = config["curent_bransament"]
    tip_mcb = config["tip_mcb"]
    nr_iluminat = config["nr_iluminat"]
    nr_prize = config["nr_prize"]
    speciali = config["speciali"]

    # Separator cu fuzibile
    poli_separator = "4P" if alimentare == "Trifazat" else "2P"
    bom.append({
        "componenta": f"Separator cu fuzibile {poli_separator} {curent_bransament}A",
        "cantitate": 1,
        "categorie": "Protectie generala"
    })

    # RCCB-uri
    if alimentare == "Monofazat":
        nr_rccb = calcul_numar_rccb(nr_iluminat, nr_prize)
        bom.append({
            "componenta": f"RCCB 40A/30mA/2P",
            "cantitate": nr_rccb,
            "categorie": "Diferential"
        })
    else:
        bom.append({
            "componenta": "RCCB 40A/30mA/2P",
            "cantitate": 3,
            "categorie": "Diferential"
        })

    # MCB iluminat
    if nr_iluminat > 0:
        bom.append({
            "componenta": f"MCB {tip_mcb} 10A — Iluminat",
            "cantitate": nr_iluminat,
            "categorie": "MCB"
        })

    # MCB prize
    if nr_prize > 0:
        bom.append({
            "componenta": f"MCB {tip_mcb} 16A — Prize",
            "cantitate": nr_prize,
            "categorie": "MCB"
        })

    # RCBO consumatori speciali
    for s in speciali:
        amperaj = selectie_mcb_special(s["putere_w"], s.get("trifazat", False))
        poli = "3P+N" if s.get("trifazat", False) else "1P+N"
        bom.append({
            "componenta": f"RCBO {poli} {amperaj}A/30mA — {s['denumire']}",
            "cantitate": 1,
            "categorie": "RCBO"
        })

    # Upgrade-uri optionale
    if config.get("spd"):
        poli_spd = "3P+N" if alimentare == "Trifazat" else "1P+N"
        bom.append({
            "componenta": f"SPD Tip 2 {poli_spd}",
            "cantitate": 1,
            "categorie": "Protectie supratensiune"
        })

    if config.get("releu_tensiune"):
        if alimentare == "Trifazat":
            bom.append({
                "componenta": "Releu monitorizare faze 3F",
                "cantitate": 1,
                "categorie": "Protectie tensiune"
            })
        else:
            bom.append({
                "componenta": "Releu protectie tensiune 1F (min/max)",
                "cantitate": 1,
                "categorie": "Protectie tensiune"
            })
        bom.append({
            "componenta": f"Contactor {curent_bransament}A",
            "cantitate": 1,
            "categorie": "Protectie tensiune"
        })

    if config.get("contor_energie"):
        bom.append({
            "componenta": "Contor energie montat pe sina DIN",
            "cantitate": 1,
            "categorie": "Masurare"
        })

    return bom


def calcul_module(bom, tip_mcb):
    total = 0
    for item in bom:
        comp = item["componenta"]
        cant = item["cantitate"]
        if "Separator" in comp:
            total += 3 * cant
        elif "RCCB" in comp:
            total += 2 * cant
        elif "RCBO" in comp:
            if "3P+N" in comp:
                total += 4 * cant
            else:
                total += 2 * cant
        elif "MCB" in comp:
            if tip_mcb == "1P+N":
                total += 2 * cant
            else:
                total += 1 * cant
        elif "SPD" in comp:
            total += 3 * cant
        elif "Releu" in comp:
            total += 2 * cant
        elif "Contactor" in comp:
            total += 3 * cant
        elif "Contor" in comp:
            total += 2 * cant
    return total


def selectie_cutie(nr_module):
    if nr_module <= 12:
        return "Tablou 1 rand — 12 module"
    elif nr_module <= 24:
        return "Tablou 2 randuri — 24 module"
    elif nr_module <= 36:
        return "Tablou 3 randuri — 36 module"
    else:
        return f"Tablou 4+ randuri — minim {nr_module} module"
