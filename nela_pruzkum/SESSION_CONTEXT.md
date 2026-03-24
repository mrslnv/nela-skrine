# Session Context

Datum: 2026-03-24

## Cíl projektu

Průzkum a porovnání skříní pro Nelu, s důrazem na:

- šířka 70 až 95 cm
- výška 160 až 185 cm
- hloubka 40 až 55 cm
- zrcadlo
- šuplíky
- bílá nebo částečně bílá varianta je výhoda

## Co je hotové

- Vytvořen referenční kandidát v `nela_kandidat1/`.
- Vytvořen průzkum v `nela_pruzkum/` s dalšími kandidáty.
- Uložené zdrojové stránky a metadata pro více variant.
- Vygenerované technické srovnání:
  - `nela_pruzkum/comparison/comparison.html`
- Vygenerovaná rodinná prezentace:
  - `nela_pruzkum/comparison/family_presentation.html`
  - `nela_pruzkum/comparison/index.html`
- Přidané odkazy na původní produktové stránky přímo v prezentaci.

## Veřejné publikování

Repozitář:

- `git@github.com:mrslnv/nela-skrine.git`

Veřejná URL:

- `https://mrslnv.github.io/nela-skrine/`

GitHub Pages používá root `index.html`, který přesměrovává na:

- `nela_pruzkum/comparison/index.html`

## Důležité soubory

- `index.html`
- `nela_kandidat1/`
- `nela_pruzkum/README.md`
- `nela_pruzkum/SESSION_CONTEXT.md`
- `nela_pruzkum/kandidati_index.csv`
- `nela_pruzkum/build_comparison.py`
- `nela_pruzkum/comparison/index.html`
- `nela_pruzkum/comparison/summary.md`

## Důležité poznámky

- U některých variant z Dobrésny.cz je rozpor v hloubce:
  - tabulka uvádí 50 cm
  - text uvádí 51 cm
- U kandidáta `k08_salmax_bezova` byly na stránce dvě různé ceny.
- Více kandidátů patří do velmi podobné konstrukční řady `S90 / SS-90`, liší se hlavně dekorem, obchodem a cenou.
- Rozměr rohu / dostupného prostoru:
  - teoreticky se do rohu vejde až 113 cm na šířku a 70 cm na hloubku
  - to není cílový rozměr skříně, ale je to důležitý orientační limit pro usazení skříně a případné místo vedle ní, například pro zatažení závěsu

## Poslední důležité commity

- `0fc44ff` Add wardrobe research and family comparison site
- `edf76eb` Add root index redirect for GitHub Pages
- `7694c7b` Add source links to comparison pages

## Doporučené další kroky

1. Udělat shortlist 2 až 3 nejzajímavějších variant.
2. Připravit finální shortlistové srovnání.
3. Případně ověřit u shortlistu:
   - přesnou dostupnost
   - dopravu
   - vrácení zboží
   - detailní rozměry a další fotografie
