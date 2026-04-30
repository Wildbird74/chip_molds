import base64
import random
from pathlib import Path
from statistics import median

import streamlit as st

CHIPS = [
    {"name": "Fire-control algorithm", "slug": "fire_control", "icon": "🔥"},
    {"name": "Circuit overload", "slug": "circuit_overload", "icon": "⚡"},
    {"name": "Multi-target tracking", "slug": "multi_target", "icon": "🎯"},
    {"name": "Orbital link", "slug": "orbital_link", "icon": "🛰️"},
    {"name": "Guardian protocol", "slug": "guardian", "icon": "🛡️"},
]
ASSETS = Path(__file__).resolve().parent / "assets" / "chips"

NUM_TYPES = 5

# Cumulative probability boundaries for one chip-mold roll.
# Per-type rates: lvl1 16.7%, lvl2 3%, lvl3 0.3%. Five types total.
P_TARGET_L1 = 0.167
P_ANY_L1 = 0.835
P_TARGET_L2_HI = 0.865
P_ANY_L2 = 0.985
P_TARGET_L3_HI = 0.988

BLESSING_TRIGGER = (
    79  # Counter range is 0..79; on a pull where b == 79, the next tick would hit 80 and forces a lvl3 instead.
)

# Combining is 3:1 everywhere except the final step into the target chip, which is 2:1.
# Sub-target chips are therefore worth 3^(K-1) in lvl1-equivalents.
INVENTORY_LVL1 = {k: 3 ** (k - 1) for k in range(1, 9)}
PULL_L1, PULL_L2, PULL_L3 = 1, 3, 9


def target_cost(level: int) -> int:
    if level <= 1:
        return 1
    return 2 * 3 ** (level - 2)


@st.cache_data(show_spinner=False)
def simulate(deficit: int, blessing_start: int, mode: str, n_sims: int = 1000, seed: int = 42) -> list[int]:
    """mode in {"lucky", "real", "unlucky"}. Type roll is always 1/5 per mode."""
    rng = random.Random(seed)
    results: list[int] = []
    for _ in range(n_sims):
        progress = 0
        b = blessing_start
        molds = 0
        while progress < deficit:
            molds += 1
            if b >= BLESSING_TRIGGER:
                if rng.randrange(NUM_TYPES) == 0:
                    progress += PULL_L3
                b = 0
                continue

            if mode == "lucky":
                if rng.randrange(NUM_TYPES) == 0:
                    progress += PULL_L3
                b = 0
                continue
            if mode == "unlucky":
                if rng.randrange(NUM_TYPES) == 0:
                    progress += PULL_L1
                b += 1
                continue

            r = rng.random()
            if r < P_TARGET_L1:
                progress += PULL_L1
                b += 1
            elif r < P_ANY_L1:
                b += 1
            elif r < P_TARGET_L2_HI:
                progress += PULL_L2
                b += 1
            elif r < P_ANY_L2:
                b += 1
            elif r < P_TARGET_L3_HI:
                progress += PULL_L3
                b = 0
            else:
                b = 0
        results.append(molds)
    return results


def _chip_visual_html(chip: dict, selected: bool) -> str:
    border = "3px solid red" if selected else "3px solid transparent"
    img_path = ASSETS / f"{chip['slug']}.png"
    if img_path.exists():
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        body = f'<img src="data:image/png;base64,{b64}" style="width:100%; display:block;"/>'
    else:
        body = f'<div style="text-align:center; font-size:54px; padding:18px 0;">{chip["icon"]}</div>'
    return (
        f'<div class="chip-card" style="border:{border}; border-radius:12px; padding:6px; box-sizing:border-box;">'
        f"{body}</div>"
    )


def _select_chip(slug: str) -> None:
    st.session_state.selected_chip_slug = slug


st.set_page_config(page_title="Chip-Mold Calculator")
st.markdown(
    """
    <style>
    [data-testid="stHorizontalBlock"]:has(.chip-card) {
        flex-wrap: nowrap !important;
        gap: 0.35rem !important;
    }
    [data-testid="stHorizontalBlock"]:has(.chip-card) > [data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
        width: 20% !important;
    }
    [data-testid="stHorizontalBlock"]:has(.chip-card) button {
        padding: 0.2rem 0.15rem !important;
        font-size: 0.7rem !important;
        line-height: 1.05 !important;
        min-height: 0 !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Chip-Mold Calculator")

if "selected_chip_slug" not in st.session_state:
    st.session_state.selected_chip_slug = CHIPS[0]["slug"]

st.subheader("Target chip type")
chip_cols = st.columns(len(CHIPS))
for col, chip in zip(chip_cols, CHIPS):
    with col:
        is_selected = st.session_state.selected_chip_slug == chip["slug"]
        st.markdown(_chip_visual_html(chip, is_selected), unsafe_allow_html=True)
        st.button(
            chip["name"],
            key=f"chip_btn_{chip['slug']}",
            on_click=_select_chip,
            args=(chip["slug"],),
            use_container_width=True,
        )

target_chip = next(c for c in CHIPS if c["slug"] == st.session_state.selected_chip_slug)
target_type = target_chip["name"]

target_level = st.slider("Target level", min_value=5, max_value=8, value=5)

st.subheader(f"Inventory: {target_type}")
st.caption("Count of chips you currently have at each sub-target level.")
counts: dict[int, int] = {}
GRID_COLS = 3
for row_start in range(1, target_level, GRID_COLS):
    row_levels = list(range(row_start, min(row_start + GRID_COLS, target_level)))
    cols = st.columns(GRID_COLS)
    for j, lvl in enumerate(row_levels):
        with cols[j]:
            counts[lvl] = st.number_input(f"Lvl {lvl}", min_value=0, value=0, step=1, key=f"inv_{lvl}")

res_c1, res_c2 = st.columns(2)
with res_c1:
    molds_have = st.number_input("Chip-molds you have", min_value=0, value=0, step=1)
with res_c2:
    blessing = st.number_input("Blessing level (0–79)", min_value=0, max_value=BLESSING_TRIGGER, value=0, step=1)

if st.button("Calculate", type="primary"):
    cost = target_cost(target_level)
    progress = sum(c * INVENTORY_LVL1[lvl] for lvl, c in counts.items())
    deficit = max(0, cost - progress)

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Target cost (lvl1-eq.)", f"{cost:,}")
    m2.metric("You have (lvl1-eq.)", f"{progress:,}")
    m3.metric("Deficit (lvl1-eq.)", f"{deficit:,}")

    if deficit == 0:
        st.success("You already have enough — no molds needed.")
    else:
        with st.spinner("Simulating..."):
            sims_lucky = simulate(deficit, blessing, "lucky")
            sims_real = simulate(deficit, blessing, "real")
            sims_unlucky = simulate(deficit, blessing, "unlucky")
        lucky = int(median(sims_lucky))
        most_likely = int(median(sims_real))
        unlucky = int(median(sims_unlucky))

        st.subheader("Chip-molds you still need")
        a1, a2, a3 = st.columns(3)
        a1.metric(
            "Puchi's luck",
            f"{max(0, lucky - molds_have):,}",
            help="Every mold rolls lvl3, type is random (1/5 target).",
        )
        a2.metric(
            "Most likely",
            f"{max(0, most_likely - molds_have):,}",
            help=f"Median of {len(sims_real)} simulations with real probabilities.",
        )
        a3.metric(
            "Grimmy's luck",
            f"{max(0, unlucky - molds_have):,}",
            help="Every mold rolls lvl1 (1/5 target type); blessing fires every 80 pulls for a lvl3 (also 1/5 target).",
        )
