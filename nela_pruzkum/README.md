# Nela pruzkum

Tento adresář je pracovní prostor pro širší průzkum skříní pro Nelu.

## Cíl

Najít přibližně 10 kandidátů podobných skříni v `nela_kandidat1`:

- podobný typ
- přibližné rozměry v toleranci okolo 5 cm
- zrcadlo
- zásuvky
- výhoda: bílé provedení

## Navržený postup

1. Nasbírat kandidáty do `kandidati/`.
2. Každého kandidáta uložit stejně jako `nela_kandidat1`:
   `produkt.md`, `metadata.json`, `source.html`, `images/`.
3. Průběžně doplňovat `kandidati_index.csv`.
4. Vygenerovat HTML srovnání všech kandidátů včetně `nela_kandidat1`.
5. Udělat shortlist 2 až 3 nejlepších variant.
6. Připravit finální srovnání shortlistu pro rozhodnutí.

## Poznámka k filtrům

Výchozí cílové rozměry podle prvního kandidáta:

- šířka okolo 90 cm
- výška okolo 180 cm
- hloubka okolo 50 cm

Praktický filtr pro další průzkum:

- šířka 70 až 95 cm
- výška 160 až 185 cm
- hloubka 40 až 55 cm
- hloubka je důležitá pro porovnání a musí se evidovat co nejpřesněji
- zrcadlo: ano
- zásuvky: ano
- bílá barva: výhoda, ne povinná podmínka

## Struktura

- `kandidati/`: jednotliví noví kandidáti
- `comparison/`: výstupy pro srovnání a HTML prezentaci
- `templates/`: šablony a pomocné podklady
