"""SourceLens Streamlit UI: preference form and recommendation list.

Run:  streamlit run app.py   (after python scripts/build_catalog.py)

What this version does:
    FR-02  budget, optional type / connection / features, and a must-have
           toggle beside each selected criterion
    FR-03  budget validated before any ranking, with a message under the field
    FR-06  up to three recommendations from recommender.py
    FR-10  "No matches found" with the active hard filters, none relaxed
    FR-16  if the catalog fails to load, a nontechnical error and no submit
    FR-17  persistent notice that results come from fixed rules, not generative AI
    FR-19  for each result, which wanted items are met, not met or not verified
    SEC-01 catalog text is escaped before display
    NFR-07 every control has a visible label

Not yet (W13): evidence panel with sources (FR-08, FR-15), comparison
(FR-11), Reset (FR-12) and price notes (FR-18).

The UI never reads the catalog file itself: it calls catalog_loader and
recommender, so the storage choice (ADR-0003) does not affect this file.
"""

import re
from pathlib import Path

import streamlit as st

import catalog_loader
from preferences import (
    build_request,
    connection_options,
    feature_options,
    label,
    type_options,
)
from recommender import Recommender

ROOT = Path(__file__).parent
CATALOG_PATH = (
    ROOT / "catalog.json"
)  # fixed, read-only; never taken from user input (SEC-05)
WEIGHTS_PATH = ROOT / "weights.json"  # ranking weights config (FR-05)

TRANSPARENCY_NOTICE = (
    "SourceLens recommendations come from fixed rules and a curated catalog, "
    "not from a generative AI model. Every reason links to the source behind it."
)
NOT_MET, NOT_VERIFIED = "not met", "not met (not verified)"  # shared.py FR-19 values

_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()<>#+\-.!|~])")


def plain(text: str) -> str:
    """Escape Markdown so catalog text always shows as literal text (SEC-01)."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", str(text))


# ---------- catalog and recommender ----------


@st.cache_resource
def _load_catalog_and_recommender() -> tuple[list, Recommender]:
    """Load once and cache only a success. A failure raises, so it is never cached
    and the app recovers as soon as a valid catalog is available (FR-16).
    """
    records = catalog_loader.load_catalog(CATALOG_PATH)  # raises CatalogLoadError
    return records, Recommender(records, WEIGHTS_PATH)


def load_catalog_state() -> dict:
    """Return {"status": "ready" | "failed", "records": [...], "recommender": ...}."""
    try:
        records, recommender = _load_catalog_and_recommender()
    except Exception:  # any load failure reaches the user as FR-16, never a traceback
        return {"status": "failed", "records": [], "recommender": None}
    return {"status": "ready", "records": records, "recommender": recommender}


# ---------- form callbacks ----------


def _submit() -> None:
    """Validate on click, before the page redraws, so errors appear under each field."""
    state = st.session_state
    selected = [state.get("type"), state.get("connection"), *state.get("features", [])]
    must_have = {v: bool(state.get(f"must_{v}")) for v in selected if v}
    request, errors = build_request(
        state.get("budget"),
        state.get("type"),
        state.get("connection"),
        state.get("features", []),
        must_have,
    )
    state["errors"] = errors
    state["request"] = request


def _field_error(name: str) -> None:
    message = st.session_state.get("errors", {}).get(name)
    if message:
        st.error(message, icon=":material/error:")


def attribute_label(attribute: str, request) -> str:
    """Readable label for a recommender attribute name, e.g. TYPE -> In-ear."""
    if attribute == "TYPE":
        return label(request.value_of("type"))
    if attribute == "CONNECTION":
        return label(request.value_of("connection"))
    return label(attribute)


def show_results(results: list, request) -> None:
    if not results:  # FR-10
        st.warning("No matches found.", icon=":material/search_off:")
        filters = [f"budget up to ${request.budget}"]
        filters += [f"must have {label(c.value)}" for c in request.hard()]
        st.write("Active filters (none were relaxed): " + "; ".join(filters) + ".")
        return

    for rank, result in enumerate(results, start=1):
        product = result["product"]
        with st.container(border=True):
            st.markdown(
                f"**#{rank} {plain(product['name'])}** · ${product['price_usd']:,.2f}"
            )
            matched = [
                attribute_label(a, request) for a in result["matched_attributes"]
            ]
            if matched:
                st.markdown("**Matches:** " + plain(", ".join(matched)))
            not_met = [
                attribute_label(a, request)
                for a, status in result["match_summary"].items()
                if status == NOT_MET
            ]
            unverified = [
                attribute_label(a, request)
                for a, status in result["match_summary"].items()
                if status == NOT_VERIFIED
            ]
            if not_met:
                st.markdown("**Doesn't have:** " + plain(", ".join(not_met)))
            if unverified:
                st.markdown("**Not verified:** " + plain(", ".join(unverified)))
    st.caption("Sources for each reason will open here in the next update (W13).")


# ---------- page ----------

st.set_page_config(
    page_title="SourceLens", page_icon=":material/search:", layout="centered"
)

st.title("SourceLens")
st.caption("Headphone recommendations where every reason links to its source.")
st.info(TRANSPARENCY_NOTICE, icon=":material/info:")  # FR-17, shown on every load

catalog = load_catalog_state()
if catalog["status"] == "failed":
    st.error(
        "The product catalog couldn't be loaded, so recommendations are unavailable "
        "right now. Please try again later.",
        icon=":material/error:",
    )
else:
    st.caption(f"{len(catalog['records'])} products in the catalog.")

st.subheader("Your preferences")

st.text_input("Maximum budget (USD)", key="budget", placeholder="e.g. 150")
_field_error("budget")

st.selectbox(
    "Headphone type",
    options=[None, *type_options()],
    format_func=lambda v: "No preference" if v is None else label(v),
    key="type",
)
_field_error("type")

st.selectbox(
    "Connection",
    options=[None, *connection_options()],
    format_func=lambda v: "No preference" if v is None else label(v),
    key="connection",
)
_field_error("connection")

st.multiselect(
    "Features",
    options=feature_options(),
    format_func=label,
    key="features",
    placeholder="Choose any features you want",
)
_field_error("features")

selected = [
    v for v in (st.session_state.get("type"), st.session_state.get("connection")) if v
]
selected += st.session_state.get("features", [])
if selected:
    st.markdown("**Must-haves**")
    st.caption(
        "Turn on a toggle to require that item. Items left off only affect the ranking."
    )
    for value in selected:
        st.toggle(f"Must-have: {label(value)}", key=f"must_{value}")

st.button(
    "Get recommendations",
    type="primary",
    on_click=_submit,
    disabled=catalog["status"] == "failed",  # FR-16: block requests
)

# ---------- results ----------

request = st.session_state.get("request")
if (
    request is not None
    and not st.session_state.get("errors")
    and catalog["recommender"]
):
    st.divider()
    st.subheader("Recommendations")
    try:
        results = catalog["recommender"].recommend(request.to_recommender_prefs())
    except Exception:  # a recommender bug must not show a traceback (FR-16 spirit)
        st.error(
            "Something went wrong while ranking. Please try again.",
            icon=":material/error:",
        )
    else:
        show_results(results, request)
