#!/usr/bin/env python3

import csv
import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path("/Users/minovak/Code/CodexSkrin")
PRUZKUM = ROOT / "nela_pruzkum"
KANDIDATI = PRUZKUM / "kandidati"
COMPARISON = PRUZKUM / "comparison"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_html_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def match1(text: str, pattern: str, flags: int = 0, default: str | None = None) -> str | None:
    m = re.search(pattern, text, flags)
    if not m:
        return default
    return m.group(1).strip()


def parse_price_int(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = html.unescape(value).strip().replace("\xa0", " ")
    if re.fullmatch(r"\d+[.,]\d{2}", normalized):
        return int(round(float(normalized.replace(",", "."))))
    digits = re.sub(r"[^\d]", "", normalized)
    return int(digits) if digits else None


def parse_dimension_cm(value: str | None) -> int | None:
    if value is None:
        return None
    m = re.search(r"(\d+)", value)
    return int(m.group(1)) if m else None


def is_white_preferred(color: str | None, name: str | None) -> bool:
    hay = " ".join(filter(None, [color, name])).lower()
    return "bíl" in hay or "bila" in hay


def normalize_color(value: str | None) -> str | None:
    if not value:
        return value
    return clean_html_text(value).replace(" / ", "/")


def parse_dobresny(path: Path) -> dict:
    text = read_text(path)
    name = match1(text, r"<h1>(.*?)</h1>", re.S)
    canonical = match1(text, r'<link rel="canonical" href="([^"]+)"')
    image = match1(text, r'<span itemprop="image">(.*?)</span>')
    price = parse_price_int(match1(text, r'itemprop="price" content="([^"]+)"'))
    price_no_vat = parse_price_int(match1(text, r'Cena bez DPH:\s*([\d\s]+)\s*Kč'))
    price_30 = parse_price_int(match1(text, r'Nejnižší cena za 30 dní před slevou:\s*([\d\s]+)\s*Kč'))
    availability = match1(text, r'<span class="dostSkl">(.*?)</span>')
    part_number = match1(text, r"PartNO:\s*<span>(.*?)</span>")
    ean = match1(text, r"EAN:\s*<span>(.*?)</span>")
    width = parse_dimension_cm(match1(text, r"<td class=\"popis\">Šířka skříně</td><td><span class=\"hodnotaParam\">(.*?)</span>"))
    height = parse_dimension_cm(match1(text, r"<td class=\"popis\">Výška skříně</td><td><span class=\"hodnotaParam\">(.*?)</span>"))
    depth_table = parse_dimension_cm(match1(text, r"<td class=\"popis\">Hloubka skříně</td><td><span class=\"hodnotaParam\">(.*?)</span>"))
    width_desc = parse_dimension_cm(match1(text, r"<strong>Šířka</strong>\s*-\s*(\d+cm)", re.S))
    height_desc = parse_dimension_cm(match1(text, r"<strong>Výška</strong>\s*-\s*(\d+cm)", re.S))
    depth_desc = parse_dimension_cm(match1(text, r"<strong>Hloubka</strong>\s*-\s*(\d+cm)", re.S))
    color_table = normalize_color(match1(text, r"<td class=\"popis\">Barevné provedení</td><td><span class=\"hodnotaParam\">(.*?)</span>"))
    color_desc = normalize_color(match1(text, r"<strong>Barevné provedení:?</strong>\s*([^<]+)", re.S))
    color = color_desc or color_table
    mirror = match1(text, r"<td class=\"popis\">Zrcadlo</td><td><span class=\"hodnotaParam\">(.*?)</span>") == "Ano"
    drawers = parse_dimension_cm(match1(text, r"(\d+)\s*ZÁSUVK", re.I))
    doors = parse_dimension_cm(match1(text, r"(\d+)\s*DVE", re.I))
    brand = match1(text, r'<span itemprop="brand">(.*?)</span>') or "DobreSNY"
    desc_excerpt = clean_html_text(match1(text, r'<div role="tabpanel" class="tab-pane fade in active" id="tab_popis">(.*?)</div><!-- ./tab_popis -->', re.S, ""))

    notes: list[str] = []
    if depth_table and depth_desc and depth_table != depth_desc:
        notes.append(f"Hloubka se liší podle zdroje: tabulka {depth_table} cm, text {depth_desc} cm.")

    return {
        "store": "Dobrésny.cz",
        "source_url": canonical,
        "name": clean_html_text(name or ""),
        "brand": brand,
        "part_number": part_number,
        "ean": ean,
        "price_czk": price,
        "price_without_vat_czk": price_no_vat,
        "lowest_price_last_30_days_czk": price_30,
        "availability": clean_html_text(availability or ""),
        "dimensions_cm": {
            "width": width or width_desc,
            "height": height or height_desc,
            "depth": depth_table or depth_desc,
            "depth_note": f"Textový popis uvádí {depth_desc} cm." if depth_desc and depth_table and depth_table != depth_desc else None,
        },
        "color": color,
        "mirror": mirror,
        "drawer_count": drawers,
        "door_count": doors,
        "image_url": image,
        "features": [
            "otočné dveře",
            "zrcadlo",
            "2 zásuvky" if drawers == 2 else None,
            "vlastní montáž",
        ],
        "description_excerpt": desc_excerpt[:500],
        "white_preferred": is_white_preferred(color, name),
        "notes": notes,
    }


def parse_nabytek_market(path: Path) -> dict:
    text = read_text(path)
    name = match1(text, r"<h1>(.*?)</h1>", re.S)
    canonical = match1(text, r'<link href="([^"]+)" rel="canonical">')
    image = match1(text, r'<meta property="og:image" content="([^"]+)">')
    sku = match1(text, r'"sku":\s*"([^"]+)"')
    ean = match1(text, r'"gtin13":\s*"([^"]+)"')
    price = parse_price_int(match1(text, r'<span class="PricesalesPrice">([^<]+)</span>'))
    availability = match1(text, r'<div class="dostupnost"><span class="name">.*?</span><span class="value">(.*?)</span>', re.S)
    status = match1(text, r'<div class="status-skladem">(.*?)</div>')
    desc = clean_html_text(match1(text, r'"description":\s*"([^"]+)"') or "")
    width = parse_dimension_cm(match1(text, r"Šířka:\s*(\d+\s*cm)", re.I))
    height = parse_dimension_cm(match1(text, r"Výška:\s*(\d+\s*cm)", re.I))
    depth = parse_dimension_cm(match1(text, r"Hloubka:\s*(\d+\s*cm)", re.I))
    drawers = parse_dimension_cm(match1(text, r"(\d+)\s+zásuvky", re.I))
    doors = 2
    color = normalize_color(match1(text, r"BARVA:\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ /+-]+)", re.I))
    brand = "TOP E-SHOP"
    notes: list[str] = []
    if status and status != availability:
        notes.append(f"Stránka zároveň uvádí status '{clean_html_text(status)}'.")

    return {
        "store": "Nabytek-market.cz",
        "source_url": canonical,
        "name": clean_html_text(name or ""),
        "brand": brand,
        "part_number": sku,
        "ean": ean,
        "price_czk": price,
        "availability": clean_html_text(availability or status or ""),
        "dimensions_cm": {
            "width": width,
            "height": height,
            "depth": depth,
            "depth_note": None,
        },
        "color": normalize_color(color.title() if color else None),
        "mirror": "zrcadl" in desc.lower(),
        "drawer_count": drawers,
        "door_count": doors,
        "image_url": image,
        "features": [
            "TIP-ON otevírání",
            "2 velká zrcadla",
            "4 police",
            "ABS hrany",
        ],
        "description_excerpt": desc[:500],
        "white_preferred": is_white_preferred(color, name),
        "notes": notes,
    }


def parse_salmax(path: Path) -> dict:
    text = read_text(path)
    name = match1(text, r"<title>(.*?)\s*\|\s*Salmax\.cz</title>")
    canonical = match1(text, r'<link rel="canonical" href="([^"]+)"')
    image = match1(text, r'<meta property="og:image" content="([^"]+)"')
    sku = match1(text, r'"sku":\s*"([^"]+)"')
    brand = clean_html_text(match1(text, r'od výrobce\s*<a [^>]+>(.*?)</a>', re.S) or "TOP Nábytek")
    price = parse_price_int(match1(text, r'product-info-price.*?<span[^>]*>\s*([\d&nbsp;\s]+Kč)\s*</span>', re.S))
    alt_price = parse_price_int(match1(text, r"<li><strong>Cena:</strong>\s*([\d\s]+Kč)</li>"))
    availability = clean_html_text(match1(text, r"Dostupnost:\s*([^<]+)"))
    width = parse_dimension_cm(match1(text, r"<li><strong>Šířka:\s*</strong>(.*?)</li>", re.S))
    height = parse_dimension_cm(match1(text, r"<li><strong>Výška:\s*</strong>(.*?)</li>", re.S))
    depth = parse_dimension_cm(match1(text, r"<li><strong>Hloubka:\s*</strong>(.*?)</li>", re.S))
    drawers = parse_dimension_cm(match1(text, r"<li><strong>Počet šuplíků:\s*</strong>(.*?)</li>", re.S))
    doors = parse_dimension_cm(match1(text, r"<li><strong>Počet dveří:\s*</strong>(.*?)</li>", re.S))
    color = normalize_color(match1(text, r"<li><strong>Barva:\s*</strong>(.*?)</li>", re.S))
    desc = clean_html_text(
        match1(text, r'<meta name="description" content="([^"]+)"')
        or match1(text, r"(<p>Šatní skříň SS-90 se zrcadlem - .*?</p>)", re.S)
        or ""
    )
    notes: list[str] = []
    if price and alt_price and price != alt_price:
        notes.append(f"Na stránce jsou dvě ceny: nahoře {price} Kč, v detailním výpisu {alt_price} Kč.")

    return {
        "store": "Salmax.cz",
        "source_url": canonical,
        "name": clean_html_text(name or ""),
        "brand": brand,
        "part_number": None,
        "ean": sku,
        "price_czk": price or alt_price,
        "availability": availability,
        "dimensions_cm": {
            "width": width,
            "height": height,
            "depth": depth,
            "depth_note": None,
        },
        "color": color,
        "mirror": True,
        "drawer_count": drawers,
        "door_count": doors,
        "image_url": image,
        "features": [
            "TIP-ON otevírání",
            "snadná montáž",
            "hladké boky",
        ],
        "description_excerpt": desc[:500],
        "white_preferred": is_white_preferred(color, name),
        "notes": notes,
    }


def parse_sg(path: Path) -> dict:
    text = read_text(path)
    name = match1(text, r"<h1>(.*?)</h1>", re.S)
    canonical = match1(text, r'<link rel="canonical" href="([^"]+)"')
    image = match1(text, r'<meta property="og:image" content="([^"]+)"')
    sku = match1(text, r',"sku": "([^"]+)"')
    brand = match1(text, r'item_brand&quot;: &quot;([^&]+)&quot;') or "Akord"
    price = parse_price_int(match1(text, r'class="price__primary">([\d&nbsp;\s]+Kč)</strong>', re.S))
    availability = clean_html_text(match1(text, r'<span class="stock-info--available[^"]*">(.*?)</span>', re.S) or "")
    expedition = clean_html_text(match1(text, r'<p class="expedition-date noPartialUpdate">\s*<strong>(.*?)</strong>', re.S) or "")
    width = parse_dimension_cm(match1(text, r"<th>\s*Šířka\s*</th>\s*<td>\s*(.*?)\s*</td>", re.S))
    height = parse_dimension_cm(match1(text, r"<th>\s*Výška\s*</th>\s*<td>\s*(.*?)\s*</td>", re.S))
    depth = parse_dimension_cm(match1(text, r"<th>\s*Hloubka\s*</th>\s*<td>\s*(.*?)\s*</td>", re.S))
    drawers = parse_dimension_cm(match1(text, r"<th>\s*Počet šuplíků\s*</th>\s*<td>\s*(.*?)\s*</td>", re.S))
    doors = parse_dimension_cm(match1(text, r"<th>\s*Počet dveří\s*</th>\s*<td>\s*(.*?)\s*</td>", re.S)) or 2
    color = None
    prefix = "Šatní skříň se zrcadly S90 2 dvířka 2 zásuvky "
    if name and name.startswith(prefix):
        color = name[len(prefix):]

    notes: list[str] = []
    if expedition:
        notes.append(expedition)

    return {
        "store": "SG nábytek",
        "source_url": canonical,
        "name": clean_html_text(name or ""),
        "brand": brand,
        "part_number": sku,
        "ean": None,
        "price_czk": price,
        "availability": availability,
        "dimensions_cm": {
            "width": width,
            "height": height,
            "depth": depth,
            "depth_note": None,
        },
        "color": normalize_color(color),
        "mirror": True,
        "drawer_count": drawers,
        "door_count": doors,
        "image_url": image,
        "features": [
            "otočné dveře",
            "výsuvné prvky",
            "zrcadlo",
            "2 zásuvky" if drawers == 2 else None,
        ],
        "description_excerpt": "",
        "white_preferred": is_white_preferred(color, name),
        "notes": notes,
    }


PARSERS = {
    "dobresny": parse_dobresny,
    "nabytek_market": parse_nabytek_market,
    "salmax": parse_salmax,
    "sg": parse_sg,
}


CANDIDATES = [
    {"id": "k02_dobresny_bila_seda", "parser": "dobresny", "source": KANDIDATI / "k02_dobresny_bila_seda" / "source.html"},
    {"id": "k03_dobresny_dub_artisan_bila", "parser": "dobresny", "source": KANDIDATI / "k03_dobresny_dub_artisan_bila" / "source.html"},
    {"id": "k04_dobresny_dub_artisan", "parser": "dobresny", "source": KANDIDATI / "k04_dobresny_dub_artisan" / "source.html"},
    {"id": "k05_dobresny_sonoma", "parser": "dobresny", "source": KANDIDATI / "k05_dobresny_sonoma" / "source.html"},
    {"id": "k06_dobresny_wenge_sonoma", "parser": "dobresny", "source": KANDIDATI / "k06_dobresny_wenge_sonoma" / "source.html"},
    {"id": "k07_nabytek_market_bila", "parser": "nabytek_market", "source": KANDIDATI / "k07_fuf_star_bila" / "source.html"},
    {"id": "k08_salmax_bezova", "parser": "salmax", "source": KANDIDATI / "k08_nabytek_market_ss90_bila" / "source.html"},
    {"id": "k09_sg_bila", "parser": "sg", "source": KANDIDATI / "k09_sg_s90_bila" / "source.html"},
    {"id": "k10_sg_bila_dub_sonoma", "parser": "sg", "source": KANDIDATI / "k10_sg_s90_bila_dub_sonoma" / "source.html"},
    {"id": "k11_sg_bila_wenge", "parser": "sg", "source": KANDIDATI / "k11_sg_s90_bila_wenge" / "source.html"},
]


def write_candidate_files(folder: Path, data: dict) -> None:
    metadata = {
        "downloaded_at": "2026-03-24",
        **data,
    }
    (folder / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    notes = data.get("notes") or []
    features = [x for x in data.get("features") or [] if x]
    dims = data["dimensions_cm"]
    lines = [
        f"# {data['name']}",
        "",
        f"- Zdroj: {data['source_url']}",
        f"- E-shop: {data['store']}",
        f"- Cena: {data['price_czk']} Kč" if data.get("price_czk") is not None else "- Cena: neuvedena",
        f"- Dostupnost: {data['availability']}" if data.get("availability") else "- Dostupnost: neuvedena",
        f"- Rozměry: {dims.get('width')} x {dims.get('height')} x {dims.get('depth')} cm",
        f"- Barva: {data.get('color') or 'neuvedena'}",
        f"- Zrcadlo: {'ano' if data.get('mirror') else 'ne'}",
        f"- Šuplíky: {data.get('drawer_count') if data.get('drawer_count') is not None else 'neuvedeno'}",
        f"- Bílé provedení jako výhoda: {'ano' if data.get('white_preferred') else 'ne'}",
        "",
        "## Výhody",
    ]
    lines.extend([f"- {item}" for item in features] or ["- neuvedeno"])
    if notes:
        lines.append("")
        lines.append("## Poznámky")
        lines.extend([f"- {item}" for item in notes])
    (folder / "produkt.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_reference_candidate() -> dict:
    path = ROOT / "nela_kandidat1" / "metadata.json"
    data = json.loads(read_text(path))
    return {
        "id": "k01_reference_dobresny_bila",
        "store": data["store"],
        "source_url": data["source_url"],
        "name": data["product"]["name"],
        "brand": data["product"]["brand"],
        "part_number": data["product"]["part_number"],
        "ean": data["product"]["ean"],
        "price_czk": data["product"]["price_czk"],
        "price_without_vat_czk": data["product"]["price_without_vat_czk"],
        "lowest_price_last_30_days_czk": data["product"]["lowest_price_last_30_days_czk"],
        "availability": data["product"]["availability"],
        "dimensions_cm": {
            "width": data["product"]["dimensions_cm"]["width"],
            "height": data["product"]["dimensions_cm"]["height"],
            "depth": data["product"]["dimensions_cm"]["depth"]["table"],
            "depth_note": "Textový popis uvádí 51 cm.",
        },
        "color": data["product"]["color"],
        "mirror": data["product"]["mirror"],
        "drawer_count": data["product"]["drawer_count"],
        "door_count": data["product"]["door_count"],
        "image_url": "assets/reference_main.webp",
        "features": data["product"]["features"],
        "description_excerpt": "",
        "white_preferred": True,
        "notes": data.get("notes", []),
        "downloaded_at": data["downloaded_at"],
        "folder": str(ROOT / "nela_kandidat1"),
    }


def format_bool(value: bool) -> str:
    return "Ano" if value else "Ne"


def html_escape(value: str | None) -> str:
    return html.escape("" if value is None else str(value))


def format_price(value: int | None) -> str:
    if value is None:
        return "neuvedeno"
    return f"{value:,}".replace(",", " ") + " Kč"


def availability_rank(value: str | None) -> int:
    if not value:
        return 99
    low = value.lower()
    if "obvykle skladem" in low or "skladem" in low:
        return 0
    if "1-2 týdny" in low or "do 2 týdnů" in low:
        return 1
    if "na cestě" in low:
        return 2
    return 3


def candidate_warnings(candidate: dict) -> list[str]:
    warnings = []
    dims = candidate["dimensions_cm"]
    if dims.get("depth_note"):
        warnings.append(dims["depth_note"])
    warnings.extend(candidate.get("notes", []))
    return warnings


def render_badges(candidate: dict) -> str:
    dims = candidate["dimensions_cm"]
    badges = [
        ("price", format_price(candidate.get("price_czk"))),
        ("depth", f"Hloubka {dims.get('depth')} cm"),
        ("color", candidate.get("color") or "Barva neuvedena"),
        ("avail", candidate.get("availability") or "Dostupnost neuvedena"),
    ]
    if candidate.get("white_preferred"):
        badges.insert(0, ("white", "Bílá jako plus"))
    return "".join(
        f'<span class="badge badge--{html_escape(kind)}">{html_escape(label)}</span>'
        for kind, label in badges
    )


def render_family_presentation(candidates: list[dict]) -> str:
    reference = next(c for c in candidates if c["id"] == "k01_reference_dobresny_bila")
    others = [c for c in candidates if c["id"] != reference["id"]]

    def similarity_key(candidate: dict) -> tuple:
        dims = candidate["dimensions_cm"]
        ref_dims = reference["dimensions_cm"]
        diff = sum(abs((dims.get(k) or 0) - (ref_dims.get(k) or 0)) for k in ("width", "height", "depth"))
        return (
            diff,
            0 if candidate.get("white_preferred") else 1,
            availability_rank(candidate.get("availability")),
            candidate.get("price_czk") or 999999,
        )

    budget_pick = min(others, key=lambda c: (c.get("price_czk") or 999999, availability_rank(c.get("availability"))))
    white_pick = min(
        [c for c in others if c.get("white_preferred")],
        key=lambda c: (c.get("price_czk") or 999999, availability_rank(c.get("availability"))),
    )
    similar_pick = min(others, key=similarity_key)
    fast_pick = min(others, key=lambda c: (availability_rank(c.get("availability")), c.get("price_czk") or 999999))

    featured = [
        ("Referenční kus", reference, "Tohle je původní favorit, ke kterému všechno vztahujeme."),
        ("Cenový favorit", budget_pick, "Nejnižší cena z celého přehledu."),
        ("Bílá za rozumnou cenu", white_pick, "Bílé provedení a přitom stále nízká cena."),
        ("Nejbližší původní volbě", similar_pick, "Rozměrově i typově nejblíž prvnímu kandidátovi."),
        ("Nejrychlejší varianta", fast_pick, "Nejlépe vychází dostupnost, pokud chcete řešit nákup brzy."),
    ]

    quick_compare = sorted(
        candidates,
        key=lambda c: (
            0 if c["id"] in {reference["id"], budget_pick["id"], white_pick["id"], similar_pick["id"], fast_pick["id"]} else 1,
            0 if c.get("white_preferred") else 1,
            c["dimensions_cm"].get("depth") or 999,
            c.get("price_czk") or 999999,
        ),
    )

    featured_cards = []
    for label, candidate, reason in featured:
        warnings = candidate_warnings(candidate)
        warning_html = ""
        if warnings:
            warning_html = "<p class=\"card-warning\"><strong>Pozor:</strong> " + html_escape(" | ".join(warnings)) + "</p>"
        featured_cards.append(
            f"""
            <article class="hero-card">
              <div class="hero-card__image-wrap">
                <img src="{html_escape(candidate.get('image_url') or '')}" alt="{html_escape(candidate['name'])}">
                <span class="hero-card__label">{html_escape(label)}</span>
              </div>
              <div class="hero-card__body">
                <h3>{html_escape(candidate['name'])}</h3>
                <p class="hero-card__reason">{html_escape(reason)}</p>
                <p class="hero-card__price">{html_escape(format_price(candidate.get('price_czk')))}</p>
                <p class="hero-card__meta">Rozměry: {candidate['dimensions_cm'].get('width')} × {candidate['dimensions_cm'].get('height')} × {candidate['dimensions_cm'].get('depth')} cm</p>
                <p class="hero-card__meta">Barva: {html_escape(candidate.get('color') or 'neuvedena')}</p>
                <p class="hero-card__meta">Dostupnost: {html_escape(candidate.get('availability') or 'neuvedena')}</p>
                <div class="badges">{render_badges(candidate)}</div>
                <p class="card-link-wrap"><a class="card-link" href="{html_escape(candidate['source_url'])}" target="_blank" rel="noreferrer">Otevřít původní produkt</a></p>
                {warning_html}
              </div>
            </article>
            """
        )

    compact_cards = []
    for candidate in quick_compare:
        warnings = candidate_warnings(candidate)
        compact_cards.append(
            f"""
            <article class="mini-card">
              <img src="{html_escape(candidate.get('image_url') or '')}" alt="{html_escape(candidate['name'])}">
              <div class="mini-card__body">
                <h4>{html_escape(candidate['name'])}</h4>
                <p>{html_escape(format_price(candidate.get('price_czk')))} | {candidate['dimensions_cm'].get('width')} × {candidate['dimensions_cm'].get('height')} × {candidate['dimensions_cm'].get('depth')} cm</p>
                <div class="badges">{render_badges(candidate)}</div>
                <p class="mini-card__link-wrap"><a class="mini-card__link" href="{html_escape(candidate['source_url'])}" target="_blank" rel="noreferrer">Detail a všechny obrázky</a></p>
                <p class="mini-card__warning">{html_escape(' | '.join(warnings) if warnings else 'Bez zvláštní poznámky')}</p>
              </div>
            </article>
            """
        )

    discussion_rows = []
    for candidate in quick_compare:
        dims = candidate["dimensions_cm"]
        discussion_rows.append(
            f"""
            <tr>
              <td>{html_escape(candidate['name'])}<br><a class="table-link" href="{html_escape(candidate['source_url'])}" target="_blank" rel="noreferrer">Otevřít originál</a></td>
              <td>{html_escape(format_price(candidate.get('price_czk')))}</td>
              <td>{dims.get('depth')} cm</td>
              <td>{html_escape(candidate.get('color') or '')}</td>
              <td>{format_bool(bool(candidate.get('white_preferred')))}</td>
              <td>{html_escape(candidate.get('availability') or '')}</td>
              <td>{html_escape(' | '.join(candidate_warnings(candidate)) or 'Bez poznámky')}</td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rodinné srovnání skříní pro Nelu</title>
  <style>
    :root {{
      --bg: #f7f2ea;
      --paper: #fffdf8;
      --ink: #211c18;
      --muted: #6b6257;
      --line: #dccdb8;
      --accent: #b85c38;
      --accent-dark: #7e3920;
      --soft: #f0e0d2;
      --green: #3a6d57;
      --green-soft: #dce9e2;
      --shadow: 0 18px 40px rgba(46, 32, 16, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 0%, rgba(184,92,56,0.18), transparent 25%),
        radial-gradient(circle at 100% 20%, rgba(58,109,87,0.12), transparent 24%),
        linear-gradient(180deg, #fcf8f1 0%, var(--bg) 100%);
    }}
    .wrap {{ max-width: 1360px; margin: 0 auto; padding: 28px 18px 72px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 24px;
    }}
    .hero-main, .hero-side {{
      background: rgba(255, 253, 248, 0.92);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      padding: 24px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: clamp(2.2rem, 5vw, 4.6rem);
      line-height: 0.92;
      letter-spacing: -0.05em;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .hero-main p {{
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 1.08rem;
      max-width: 820px;
    }}
    .hero-notes {{
      display: grid;
      gap: 12px;
    }}
    .note {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px 16px;
    }}
    .note strong {{
      display: block;
      color: var(--accent-dark);
      margin-bottom: 6px;
    }}
    .section-title {{
      margin: 30px 0 14px;
      font-size: 1.45rem;
      letter-spacing: -0.03em;
      font-family: Georgia, "Times New Roman", serif;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }}
    .hero-card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 24px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    .hero-card__image-wrap {{
      position: relative;
      background: linear-gradient(180deg, #efe3d1, #f8f2e8);
    }}
    .hero-card__image-wrap img {{
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      display: block;
    }}
    .hero-card__label {{
      position: absolute;
      left: 14px;
      top: 14px;
      background: rgba(33, 28, 24, 0.88);
      color: #fff;
      padding: 7px 12px;
      border-radius: 999px;
      font-size: 0.84rem;
      letter-spacing: 0.04em;
    }}
    .hero-card__body {{ padding: 16px; }}
    .hero-card h3 {{
      margin: 0 0 8px;
      font-size: 1.15rem;
      line-height: 1.15;
    }}
    .hero-card__reason, .hero-card__meta {{
      margin: 0 0 8px;
      color: var(--muted);
    }}
    .hero-card__price {{
      margin: 0 0 10px;
      color: var(--accent-dark);
      font-size: 1.55rem;
      font-weight: 800;
    }}
    .card-warning {{
      margin: 12px 0 0;
      padding: 10px 12px;
      border-radius: 14px;
      background: #fff1e6;
      color: #7d4a1f;
      font-size: 0.92rem;
    }}
    .card-link-wrap,
    .mini-card__link-wrap {{
      margin: 12px 0 0;
    }}
    .card-link,
    .mini-card__link,
    .table-link {{
      display: inline-block;
      color: var(--accent-dark);
      font-weight: 700;
      text-decoration: none;
      border-bottom: 1px solid rgba(126, 57, 32, 0.35);
    }}
    .card-link:hover,
    .mini-card__link:hover,
    .table-link:hover {{
      border-bottom-color: var(--accent-dark);
    }}
    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }}
    .badge {{
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.83rem;
      border: 1px solid var(--line);
      background: var(--soft);
    }}
    .badge--white {{
      background: #fff;
      border-color: #d6d6d6;
    }}
    .badge--avail {{
      background: var(--green-soft);
      border-color: #b7d4c7;
    }}
    .mini-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }}
    .mini-card {{
      display: grid;
      grid-template-columns: 112px 1fr;
      gap: 12px;
      align-items: stretch;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 20px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    .mini-card img {{
      width: 100%;
      height: 100%;
      min-height: 112px;
      object-fit: cover;
      background: #efe3d1;
    }}
    .mini-card__body {{
      padding: 12px 12px 12px 0;
    }}
    .mini-card h4 {{
      margin: 0 0 6px;
      font-size: 1rem;
      line-height: 1.1;
    }}
    .mini-card p {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .mini-card__warning {{
      color: var(--accent-dark) !important;
      font-size: 0.88rem !important;
    }}
    .talk-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .talk-card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      box-shadow: var(--shadow);
    }}
    .talk-card strong {{
      display: block;
      margin-bottom: 8px;
      color: var(--accent-dark);
    }}
    .table-wrap {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      background: var(--paper);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 880px;
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #efe1cf;
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    .foot {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    @media (max-width: 980px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 720px) {{
      .wrap {{ padding: 16px 12px 40px; }}
      .hero-main, .hero-side {{ padding: 18px; border-radius: 22px; }}
      .mini-card {{ grid-template-columns: 1fr; }}
      .mini-card__body {{ padding: 0 12px 12px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-main">
        <h1>Skříně pro Nelu</h1>
        <p>Tohle je verze srovnání připravená pro společnou debatu doma. Neřeší jen technická data, ale hlavně to, co je důležité při rozhodování: cena, hloubka, barva, dostupnost a jestli je varianta opravdu blízko původnímu favoritu.</p>
        <p>Ve všech variantách jsem držel filtr: šířka 70-95 cm, výška 160-185 cm, hloubka 40-55 cm, zrcadlo a šuplíky. Bílá nebo částečně bílá varianta je plus.</p>
      </div>
      <div class="hero-side">
        <div class="hero-notes">
          <div class="note">
            <strong>Co řešit jako první</strong>
            Má být priorita cena, čistě bílý vzhled, nebo co nejmenší hloubka?
          </div>
          <div class="note">
            <strong>Co vychází z dat</strong>
            Většina kandidátů má hloubku 50 až 51 cm. Rozdíly jsou hlavně v dekoru, ceně a dostupnosti.
          </div>
          <div class="note">
            <strong>Na co pozor</strong>
            U některých variant se rozchází hloubka mezi tabulkou a popisem, případně jsou na stránce dvě různé ceny.
          </div>
        </div>
      </div>
    </section>

    <h2 class="section-title">Rychlí favoriti pro diskuzi</h2>
    <section class="hero-grid">
      {''.join(featured_cards)}
    </section>

    <h2 class="section-title">Otázky k debatě</h2>
    <section class="talk-box">
      <div class="talk-card">
        <strong>1. Která vypadá nejlíp?</strong>
        Nela asi bude řešit hlavně dekor a jak působí zrcadlo na přední straně.
      </div>
      <div class="talk-card">
        <strong>2. Je 50 až 51 cm hloubka v pokoji v pohodě?</strong>
        Tohle je prakticky nejdůležitější rozměr pro prostor před skříní.
      </div>
      <div class="talk-card">
        <strong>3. Chcete čistě bílou, nebo stačí kombinace?</strong>
        Bílé varianty jsou vizuálně lehčí, ale některé kombinace jsou levnější nebo zajímavější.
      </div>
      <div class="talk-card">
        <strong>4. Má hrát roli rychlost dodání?</strong>
        Některé varianty vypadají dostupnější než původní reference.
      </div>
    </section>

    <h2 class="section-title">Všechny varianty na jedné obrazovce</h2>
    <section class="mini-grid">
      {''.join(compact_cards)}
    </section>

    <h2 class="section-title">Jednoduchá tabulka pro finální debatu</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Varianta</th>
            <th>Cena</th>
            <th>Hloubka</th>
            <th>Barva</th>
            <th>Bílá jako plus</th>
            <th>Dostupnost</th>
            <th>Poznámky</th>
          </tr>
        </thead>
        <tbody>
          {''.join(discussion_rows)}
        </tbody>
      </table>
    </div>
    <p class="foot">Doporučení k dalšímu kroku: po společné debatě si z této stránky vyberte 2 až 3 kusy a teprve pak uděláme finální shortlistové srovnání, případně ověření dopravy, vrácení a detailních rozměrů.</p>
  </div>
</body>
</html>
"""


def render_comparison(candidates: list[dict]) -> str:
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("white_preferred") else 1,
            item.get("dimensions_cm", {}).get("depth") or 999,
            item.get("price_czk") or 999999,
        ),
    )
    cheapest = min((c for c in candidates if c.get("price_czk") is not None), key=lambda c: c["price_czk"])
    shallowest = min((c for c in candidates if c["dimensions_cm"].get("depth") is not None), key=lambda c: c["dimensions_cm"]["depth"])
    white_count = sum(1 for c in candidates if c.get("white_preferred"))

    cards = []
    rows = []
    for c in sorted_candidates:
        dims = c["dimensions_cm"]
        notes = "<br>".join(html_escape(n) for n in c.get("notes", [])) or "Bez poznámky"
        image = c.get("image_url") or ""
        card = f"""
        <article class="card">
          <img src="{html_escape(image)}" alt="{html_escape(c['name'])}">
          <div class="card-body">
            <div class="tag">{html_escape(c['id'])}</div>
            <h2>{html_escape(c['name'])}</h2>
            <p class="store">{html_escape(c['store'])}</p>
            <p class="price">{html_escape(c.get('price_czk'))} Kč</p>
            <p class="meta">Rozměry: {dims.get('width')} × {dims.get('height')} × {dims.get('depth')} cm</p>
            <p class="meta">Barva: {html_escape(c.get('color') or 'neuvedena')}</p>
            <p class="meta">Dostupnost: {html_escape(c.get('availability') or 'neuvedena')}</p>
            <p class="notes">{notes}</p>
            <p><a href="{html_escape(c['source_url'])}" target="_blank" rel="noreferrer">Otevřít produkt</a></p>
          </div>
        </article>
        """
        cards.append(card)

        rows.append(
            f"""
            <tr>
              <td>{html_escape(c['id'])}</td>
              <td>{html_escape(c['name'])}</td>
              <td>{html_escape(c['store'])}</td>
              <td>{html_escape(c.get('price_czk'))} Kč</td>
              <td>{dims.get('width')}</td>
              <td>{dims.get('height')}</td>
              <td>{dims.get('depth')}</td>
              <td>{html_escape(c.get('color') or '')}</td>
              <td>{format_bool(bool(c.get('mirror')))}</td>
              <td>{html_escape(c.get('drawer_count'))}</td>
              <td>{format_bool(bool(c.get('white_preferred')))}</td>
              <td>{html_escape(c.get('availability') or '')}</td>
              <td>{html_escape('; '.join(c.get('notes', [])))}</td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Srovnání skříní pro Nelu</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #20201c;
      --muted: #6c675b;
      --line: #d9cfbf;
      --accent: #2f6d62;
      --accent-soft: #dcebe7;
      --warn: #8d5a2b;
      --shadow: 0 10px 30px rgba(58, 46, 24, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(47,109,98,0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(141,90,43,0.10), transparent 24%),
        linear-gradient(180deg, #f8f3eb 0%, var(--bg) 100%);
    }}
    .wrap {{ max-width: 1320px; margin: 0 auto; padding: 32px 20px 80px; }}
    header {{
      background: linear-gradient(135deg, rgba(255,250,242,0.95), rgba(244,239,230,0.95));
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 28px;
      box-shadow: var(--shadow);
      margin-bottom: 28px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    .lead {{ margin: 0; color: var(--muted); max-width: 850px; font-size: 1.08rem; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 24px 0 0;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
    }}
    .stat strong {{ display: block; font-size: 1.6rem; }}
    .section-title {{
      margin: 34px 0 14px;
      font-size: 1.35rem;
      letter-spacing: -0.03em;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    .card img {{
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      display: block;
      background: #ece5d8;
    }}
    .card-body {{ padding: 16px; }}
    .tag {{
      display: inline-block;
      font-size: 0.8rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
      background: var(--accent-soft);
      border-radius: 999px;
      padding: 4px 10px;
      margin-bottom: 10px;
    }}
    .card h2 {{
      font-size: 1.15rem;
      line-height: 1.1;
      margin: 0 0 8px;
    }}
    .store, .meta, .notes {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .price {{
      font-size: 1.35rem;
      margin: 0 0 8px;
      color: var(--accent);
      font-weight: 700;
    }}
    a {{ color: var(--accent); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 0.95rem;
    }}
    th {{
      background: #efe4d2;
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    .table-wrap {{ overflow: auto; border-radius: 20px; }}
    .footnote {{
      margin-top: 16px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    @media (max-width: 720px) {{
      .wrap {{ padding: 18px 12px 40px; }}
      header {{ padding: 20px; border-radius: 18px; }}
      .card-body {{ padding: 14px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Srovnání skříní pro Nelu</h1>
      <p class="lead">Porovnání zahrnuje referenční variantu z <code>nela_kandidat1</code> a dalších 10 podobných kandidátů. Filtr: šířka 70-95 cm, výška 160-185 cm, hloubka 40-55 cm, zrcadlo, šuplíky. Bílé nebo částečně bílé provedení je plus. Prostorový limit v rohu: max 113x70 cm.</p>
      <div class="stats">
        <div class="stat"><span>Celkem variant</span><strong>{len(candidates)}</strong></div>
        <div class="stat"><span>Bílé jako výhoda</span><strong>{white_count}</strong></div>
        <div class="stat"><span>Nejnižší cena</span><strong>{cheapest['price_czk']} Kč</strong>{html_escape(cheapest['id'])}</div>
        <div class="stat"><span>Nejmenší hloubka</span><strong>{shallowest['dimensions_cm']['depth']} cm</strong>{html_escape(shallowest['id'])}</div>
      </div>
    </header>

    <h2 class="section-title">Karty kandidátů</h2>
    <section class="cards">
      {''.join(cards)}
    </section>

    <h2 class="section-title">Tabulkové srovnání</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Název</th>
            <th>Obchod</th>
            <th>Cena</th>
            <th>Šířka</th>
            <th>Výška</th>
            <th>Hloubka</th>
            <th>Barva</th>
            <th>Zrcadlo</th>
            <th>Šuplíky</th>
            <th>Bílá výhoda</th>
            <th>Dostupnost</th>
            <th>Poznámky</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    <p class="footnote">Poznámka: u části variant jde o stejnou konstrukční rodinu skříně v jiných dekorech a z různých e-shopů. To je pro rodinné rozhodování užitečné, protože uvidíte rozdíl v ceně, dostupnosti a vzhledu při skoro stejných rozměrech.</p>
  </div>
</body>
</html>
"""


def main() -> None:
    COMPARISON.mkdir(parents=True, exist_ok=True)
    assets_dir = COMPARISON / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "nela_kandidat1" / "images" / "main.webp", assets_dir / "reference_main.webp")
    all_candidates: list[dict] = [load_reference_candidate()]

    for item in CANDIDATES:
        parser = PARSERS[item["parser"]]
        data = parser(item["source"])
        data["id"] = item["id"]
        data["downloaded_at"] = "2026-03-24"
        data["folder"] = str(item["source"].parent)
        write_candidate_files(item["source"].parent, data)
        all_candidates.append(data)

    all_candidates_json = COMPARISON / "all_candidates.json"
    all_candidates_json.write_text(
        json.dumps(all_candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    html_output = COMPARISON / "comparison.html"
    html_output.write_text(render_comparison(all_candidates), encoding="utf-8")
    family_output = COMPARISON / "family_presentation.html"
    family_html = render_family_presentation(all_candidates)
    family_output.write_text(family_html, encoding="utf-8")
    (COMPARISON / "index.html").write_text(family_html, encoding="utf-8")

    csv_path = PRUZKUM / "kandidati_index.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "nazev", "obchod", "cena_czk", "dostupnost", "sirka_cm", "vyska_cm",
            "hloubka_cm", "hloubka_poznamka", "zrcadlo", "supliky", "barva",
            "bila_vyhoda", "url", "poznamka",
        ])
        for c in all_candidates:
            dims = c["dimensions_cm"]
            writer.writerow([
                c["id"],
                c["name"],
                c["store"],
                c.get("price_czk"),
                c.get("availability"),
                dims.get("width"),
                dims.get("height"),
                dims.get("depth"),
                dims.get("depth_note"),
                "ano" if c.get("mirror") else "ne",
                c.get("drawer_count"),
                c.get("color"),
                "ano" if c.get("white_preferred") else "ne",
                c.get("source_url"),
                " | ".join(c.get("notes", [])),
            ])


if __name__ == "__main__":
    main()
