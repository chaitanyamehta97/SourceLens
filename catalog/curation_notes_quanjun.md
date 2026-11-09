# W5 curation notes — Quanjun's 4 records

File: `catalog/curation_quanjun.json` (append to `catalog.json` after the schema freeze).
4 products, 20 evidence items, all from manufacturer sources (no review excerpts). Checked on 7 Nov 2026. Every type, connection and feature tag has its own evidence item.

| product_id | Type / connection | Tags | price_usd | price_basis | Price source |
|---|---|---|---|---|---|
| soundcore-space-one | over-ear / both | ANC, microphone, multipoint, foldable | 99.99 | manufacturer_list | soundcore US product page |
| beats-powerbeats-pro-2 | in-ear / wireless | ANC, microphone, water-resistant | 249.99 | launch_msrp | Beats press release, 11 Feb 2025: "$249.99 (US)" |
| sony-wf-c510 | in-ear / wireless | microphone, water-resistant, multipoint | 69.99 | manufacturer_list | Sony US product page (list price; $59.99 shown on 7 Nov was a sale) |
| beats-solo-4 | on-ear / both | microphone, foldable | 199.99 | launch_msrp | Beats press release, 30 Apr 2024: "$199.99 (US)" |

## Price rule (SRS §9.2 sourcing policy, owner: Quanjun)

Use the manufacturer's **official list price, never a sale price**, recorded in two optional fields:

- `price_source_url`: the official page the price came from
- `price_basis`: `manufacturer_list` (regular price on the manufacturer's US store page) or `launch_msrp` (US price in the manufacturer's launch press release, used when the US store page cannot be checked)

Why: every price can be traced to an official page, and sale prices do not leak into tests or the demo. Price stays informational, not evidence (FR-18).

Note: this refines the "launch MSRP" rule announced in Teams. Sony's US page shows only the current list price ($69.99), which differs from the $60 reported at launch, so a strict launch-MSRP rule would have forced a non-official source.

## Sources

1. **soundcore Space One** — https://www.soundcore.com/products/space-one-a3035011
   Design over-ear; Bluetooth 5.3 plus AUX-in; Adaptive ANC; 3 mics with AI enhancement; multipoint; ear cups rotate and fold. Listed at $99.99 with no sale marking.
2. **Powerbeats Pro 2** — https://www.businesswire.com/news/home/20250211896520/en (press release issued by Beats)
   Redesigned earhook; Class 1 Bluetooth; Active Noise Cancellation; three microphones and a voice accelerometer per earbud; IPX4 (case not rated); $249.99 (US).
3. **Sony WF-C510** — https://electronics.sony.com/audio/headphones/all-headphones/p/wfc510-b
   "Closed-type truly wireless earbuds", designed from Sony's in-ear earbud ear-shape data; Bluetooth 5.3; "high-quality built-in microphone" for hands-free calling; IPX4 (case not water resistant); Multipoint Connection; FAQ confirms no active noise cancelling. List $69.99, sale $59.99 on 7 Nov 2026.
4. **Beats Solo 4** — https://www.apple.com/ca/shop/product/muw23dn/a/beats-solo-4-on-ear-wireless-headphones-matt-black
   Form factor on-ear; Class 1 Bluetooth; lossless audio via USB-C or 3.5 mm cable; multiple digital beam-forming microphones; compact foldable design. US price from the Beats press release: https://www.businesswire.com/news/home/20240430448719/en/Introducing-Beats-Solo-Buds-Looks-Tiny-Sounds-Huge

## Decisions made while curating

- **No ANC on WF-C510 or Solo 4.** Sony's FAQ states the WF-C510 has no active noise cancelling; Beats describes only passive isolation for Solo 4.
- **No multipoint on Powerbeats Pro 2 or Solo 4.** Their official sources describe automatic switching between Apple devices, not multipoint. Same rule Shuonan applied to AirPods Pro 3.
- **Beats Solo 4 is on-ear.** One tech site calls it over-ear; Apple and Beats both say on-ear. Manufacturer wording wins.
- **"Superior sound quality" is not microphone evidence.** Sony's line "vocals are natural and clear" describes music playback, not calls. The microphone tag rests only on the "built-in microphone" hands-free calling section.
- **Beats uses Apple and Business Wire pages.** beatsbydre.com could not be opened during drafting; Apple sells and documents Beats, and the press releases are issued by Beats.
- **Space One and Solo 4 are "both".** Each supports Bluetooth plus a wired cable.

## Coverage this adds (with Shuonan's 4)

Prices spread across $49.95–$449.99; every type has at least two products; ANC and non-ANC options exist at the low, mid and high price tiers; three products use connection "both".

## AI assistance

Product selection, source search and first-draft evidence wording were done with Anthropic Claude (Claude Opus 5.5) on 7 Nov 2026. Quanjun opened the Sony US page herself and supplied its content, which replaced the earlier Sony Australia sources; every evidence item is checked against its source before merge.
