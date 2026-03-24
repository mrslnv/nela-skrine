# Metadata schema

Každý kandidát by měl mít alespoň tato data:

- `name`
- `store`
- `source_url`
- `downloaded_at`
- `price_czk`
- `availability`
- `dimensions_cm.width`
- `dimensions_cm.height`
- `dimensions_cm.depth`
- `dimensions_cm.depth_note`, pokud se rozměr na stránce liší nebo je nejasný
- `mirror`
- `drawer_count`
- `door_count`
- `color`
- `white_preferred`
- `ean` nebo `part_number`, pokud je k dispozici
- `materials`
- `features`
- `assets.images`
- `notes`

## Důležité pro srovnání

Tyto položky budeme později porovnávat v HTML:

- cena
- rozměry
- hloubka jako samostatně sledovaný parametr
- počet zásuvek
- zrcadlo
- typ dveří
- materiál
- dostupnost
- bílá varianta jako plusový bod
- hlavní výhody
- nejasnosti nebo rozpory v datech
