# W5 curation notes — Shuonan's 4 records

File: `catalog/curation_shuonan.json`. 4 products, 18 evidence items, all from manufacturer sources (no review excerpts). Checked on 7 Nov 2026. Every type, connection and feature tag has its own evidence item.

| product_id | Type / connection | Tags | price_usd | price_basis | Price source |
|---|---|---|---|---|---|
| sony-wh1000xm6 | OVER_EAR / BOTH | NOISE_CANCELLING, MICROPHONE, MULTIPOINT, FOLDABLE | 459.99 | MANUFACTURER_LIST | Sony US store page (list $459.99; the $379.99 sale was ignored) |
| apple-airpods-pro-3 | IN_EAR / WIRELESS | NOISE_CANCELLING, MICROPHONE, WATER_RESISTANT | 249.00 | LAUNCH_MSRP | Apple press release, Sep 2025: start at $249 (US) |
| jbl-tune-520bt | ON_EAR / WIRELESS | MICROPHONE, MULTIPOINT, FOLDABLE | 59.95 | MANUFACTURER_LIST | JBL US store page, no sale shown |
| sennheiser-hd560s | OVER_EAR / WIRED | (none) | 279.95 | MANUFACTURER_LIST | Sennheiser US store page, no sale shown |

## Decisions made while curating

- **AirPods Pro 3 stays LAUNCH_MSRP.** The price was confirmed through a search result, not Apple's own store page, so it does not qualify as MANUFACTURER_LIST.
- **Store prices drift from launch.** Sony $449.99 to $459.99, JBL $49.95 to $59.95, Sennheiser $199.95 to $279.95, which is why the team rule prefers the store page.
- **Sony sources.** Type, connection and multipoint come from Sony's Asia Pacific spec page; noise cancelling, microphone and foldable from Sony's US press release. Both are Sony.
- **Tags left off on purpose.** AirPods Pro 3: no MULTIPOINT; Apple's spec page does not claim it (device switching is Apple-only). Sony: no WATER_RESISTANT, not claimed. Sennheiser: no tags; it has no microphone and does not fold.
- **A trap.** One JBL support page for the Tune 520BT also shows text for the wired Tune 520C, so the evidence uses the global.jbl.com product page, which describes only the 520BT.

## AI assistance

Product selection, source search and first-draft evidence wording were done with Anthropic Claude on 7–8 Nov 2026; store-page prices were checked from Shuonan's own browser. Converted to the constants.py vocabulary on 22 Nov 2026.
