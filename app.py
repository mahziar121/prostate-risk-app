import streamlit as st

# ============================================================
# Page config / app metadata
# ============================================================

APP_NAME = "Prostate Risk Navigator"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Mahziar Khazaali, MD"
APP_YEAR = "2025"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide",
)

# ============================================================
# Constants / defaults
# ============================================================

DEFAULT_T_STAGE = "cT1c"
DEFAULT_N_STAGE = "cN0"
DEFAULT_M_STAGE = "cM0"
DEFAULT_PSA = 6.5

DEFAULT_PRIMARY_PATTERN = 3
DEFAULT_SECONDARY_PATTERN = 3
DEFAULT_CORE_PERCENT = 10  # integer for slider

# Standard 12-core template (A–L)
CORE_SITES = [
    ("A", "LEFT LATERAL BASE"),
    ("B", "LEFT LATERAL MID"),
    ("C", "LEFT LATERAL APEX"),
    ("D", "LEFT MEDIAL BASE"),
    ("E", "LEFT MEDIAL MID"),
    ("F", "LEFT MEDIAL APEX"),
    ("G", "RIGHT MEDIAL BASE"),
    ("H", "RIGHT MEDIAL MID"),
    ("I", "RIGHT MEDIAL APEX"),
    ("J", "RIGHT LATERAL BASE"),
    ("K", "RIGHT LATERAL MID"),
    ("L", "RIGHT LATERAL APEX"),
]

TOTAL_SYSTEMATIC_CORES = len(CORE_SITES)

# Optional targeted biopsy cores (up to 3)
TARGETED_SITES = [
    ("T1", "Targeted core 1"),
    ("T2", "Targeted core 2"),
    ("T3", "Targeted core 3"),
]

# ============================================================
# AJCC cT, cN, cM definitions (8th ed.)
# ============================================================

T_STAGE_DEFINITIONS = {
    "cTX": "Primary tumor cannot be assessed",
    "cT0": "No evidence of primary tumor",

    "cT1a": "Tumor incidental histologic finding in 5% or less of tissue resected",
    "cT1b": "Tumor incidental histologic finding in more than 5% of tissue resected",
    "cT1c": "Tumor identified by needle biopsy found in one or both sides, but not palpable",

    "cT2a": "Tumor is palpable and confined within prostate; involves one-half of one side or less",
    "cT2b": "Tumor is palpable and confined within prostate; involves more than one-half of one side but not both sides",
    "cT2c": "Tumor is palpable and confined within prostate; involves both sides",

    "cT3a": "Extraprostatic extension (unilateral or bilateral), not fixed and not invading adjacent structures",
    "cT3b": "Tumor invades seminal vesicle(s)",

    "cT4": "Tumor is fixed or invades adjacent structures other than seminal vesicles "
            "such as external sphincter, rectum, bladder, levator muscles, and/or pelvic wall",
}
T_STAGE_OPTIONS = list(T_STAGE_DEFINITIONS.keys())

N_STAGE_DEFINITIONS = {
    "cNX": "Regional lymph nodes cannot be assessed",
    "cN0": "No regional lymph node metastasis",
    "cN1": "Metastasis in regional lymph node(s)",
}
N_STAGE_OPTIONS = list(N_STAGE_DEFINITIONS.keys())

M_STAGE_DEFINITIONS = {
    "cM0": "No distant metastasis",
    "cM1": "Distant metastasis present",
    "cM1a": "Nonregional lymph node(s)",
    "cM1b": "Bone(s)",
    "cM1c": "Other site(s) with or without bone disease",
}
M_STAGE_OPTIONS = list(M_STAGE_DEFINITIONS.keys())

# ============================================================
# Helper functions: normalize TNM
# ============================================================

def _normalize_stage(stage: str, letter: str) -> str:
    s = stage.strip().lower()
    if s.startswith("c"):
        s = s[1:]
    if not s.startswith(letter):
        raise ValueError(
            f"{letter.upper()} stage must start with {letter.upper()} or c{letter.upper()}, "
            f"e.g. 'c{letter.upper()}2a'"
        )
    return s


def normalize_t_stage(t_stage: str) -> str:
    return _normalize_stage(t_stage, "t")


def normalize_n_stage(n_stage: str) -> str:
    return _normalize_stage(n_stage, "n")


def normalize_m_stage(m_stage: str) -> str:
    return _normalize_stage(m_stage, "m")


def is_t1(t_stage: str) -> bool:
    s = normalize_t_stage(t_stage)
    return s.startswith("t1")


def is_t2(t_stage: str) -> bool:
    s = normalize_t_stage(t_stage)
    return s.startswith("t2")


def is_t2a(t_stage: str) -> bool:
    s = normalize_t_stage(t_stage)
    return s.startswith("t2a")


def is_t2b_to_t2c(t_stage: str) -> bool:
    s = normalize_t_stage(t_stage)
    return s.startswith("t2b") or s.startswith("t2c")


def is_t3_to_t4(t_stage: str) -> bool:
    s = normalize_t_stage(t_stage)
    return s.startswith("t3") or s.startswith("t4")


def has_regional_nodes(n_stage: str) -> bool:
    s = normalize_n_stage(n_stage)
    return s.startswith("n1")


def has_distant_metastasis(m_stage: str) -> bool:
    s = normalize_m_stage(m_stage)
    return s.startswith("m1")


# ============================================================
# Gleason patterns -> Grade Group
# ============================================================

def gleason_to_grade_group(primary: int, secondary: int):
    score = primary + secondary
    pattern = f"{primary}+{secondary}"

    if primary == 3 and secondary == 3:
        return 1, score, f"Gleason {pattern}={score} → Grade Group 1"
    elif primary == 3 and secondary == 4:
        return 2, score, f"Gleason {pattern}={score} → Grade Group 2"
    elif primary == 4 and secondary == 3:
        return 3, score, f"Gleason {pattern}={score} → Grade Group 3"
    elif (primary == 4 and secondary == 4) or (primary == 3 and secondary == 5) or (primary == 5 and secondary == 3):
        return 4, score, f"Gleason {pattern}={score} → Grade Group 4"
    elif (primary == 4 and secondary == 5) or (primary == 5 and secondary == 4) or (primary == 5 and secondary == 5):
        return 5, score, f"Gleason {pattern}={score} → Grade Group 5"
    else:
        return None, score, f"Gleason {pattern}={score} → pattern not in standard Grade Group table"


# ============================================================
# NCCN risk groups for clinically localized disease
# ============================================================

def classify_nccn_risk(t_stage: str,
                       n_stage: str,
                       m_stage: str,
                       grade_group: int,
                       psa: float,
                       cores_positive: int,
                       cores_total: int):
    details = []
    details.append(f"Clinical TNM: {t_stage}, {n_stage}, {m_stage}")
    details.append(f"PSA {psa:.1f} ng/mL, highest biopsy Grade Group {grade_group}")

    if cores_total <= 0:
        raise ValueError("Total cores must be > 0")

    percent_cores = 100.0 * cores_positive / cores_total
    details.append(f"Systematic cores positive for cancer: {cores_positive}/{cores_total} ({percent_cores:.1f}%)")

    if has_regional_nodes(n_stage) or has_distant_metastasis(m_stage):
        details.append("N1 and/or M1 present → outside clinically localized NCCN risk groups.")
        return "Metastatic/regional disease (outside localized risk groups)", None, details

    very_high_flags = [
        is_t3_to_t4(t_stage),
        grade_group in (4, 5),
        psa > 40.0,
    ]
    if sum(very_high_flags) >= 2:
        details.append("≥2 of: T3–T4, Grade Group 4–5, PSA >40 → Very high-risk.")
        return "Very high", None, details

    high_flag = is_t3_to_t4(t_stage) or (grade_group in (4, 5)) or (psa > 20.0)
    if high_flag:
        details.append("At least one of: T3–T4, Grade Group 4–5, PSA >20 → High-risk.")
        return "High", None, details

    irfs = []
    if is_t2b_to_t2c(t_stage):
        irfs.append("T2b–T2c")
    if grade_group in (2, 3):
        irfs.append("Grade Group 2–3")
    if 10.0 <= psa <= 20.0:
        irfs.append("PSA 10–20")

    if irfs:
        details.append(f"Intermediate-risk factors: {', '.join(irfs)}")
        if (len(irfs) == 1) and (grade_group in (1, 2)) and (percent_cores < 50.0):
            details.append("Favorable intermediate: 1 IRF, GG 1–2, <50% cores positive.")
            return "Intermediate", "Favorable", details
        else:
            details.append("Unfavorable intermediate: ≥2 IRFs and/or GG 3 and/or ≥50% cores positive.")
            return "Intermediate", "Unfavorable", details

    if (is_t1(t_stage) or is_t2a(t_stage)) and grade_group == 1 and psa < 10.0:
        details.append("T1–T2a, Grade Group 1, PSA <10 → Low-risk.")
        return "Low", None, details

    details.append("Does not meet NCCN low/intermediate/high/very-high criteria with given data.")
    return "Unclassifiable", None, details


# ============================================================
# AJCC 8th prognostic stage groups
# ============================================================

def classify_ajcc_stage(t_stage: str,
                        n_stage: str,
                        m_stage: str,
                        psa: float,
                        grade_group: int):
    details = []
    details.append(f"TNM: {t_stage}, {n_stage}, {m_stage}")
    details.append(f"PSA {psa:.1f} ng/mL, highest biopsy Grade Group {grade_group}")

    if has_distant_metastasis(m_stage):
        details.append("Any T, any N, M1 → Stage IVB.")
        return "Stage IVB", details

    if has_regional_nodes(n_stage):
        details.append("Any T, N1, M0 → Stage IVA.")
        return "Stage IVA", details

    sT = normalize_t_stage(t_stage)
    if sT in ("tx", "t0"):
        details.append("Primary tumor TX/T0 → Stage group cannot be assigned.")
        return "Stage cannot be determined (TX/T0)", details

    is_T1 = sT.startswith("t1")
    is_T2 = sT.startswith("t2")
    is_T2a_ = sT.startswith("t2a")
    is_T2b_c = sT.startswith("t2b") or sT.startswith("t2c")
    is_T3_4 = sT.startswith("t3") or sT.startswith("t4")

    if grade_group == 5:
        details.append("Any T, N0/NX, M0, Grade Group 5 → Stage IIIC.")
        return "Stage IIIC", details

    if is_T3_4 and grade_group in (1, 2, 3, 4):
        details.append("T3–T4, N0/NX, M0, Grade Group 1–4 → Stage IIIB.")
        return "Stage IIIB", details

    if (is_T1 or is_T2) and grade_group in (1, 2, 3, 4) and psa >= 20:
        details.append("T1–T2, N0/NX, M0, Grade Group 1–4, PSA ≥20 → Stage IIIA.")
        return "Stage IIIA", details

    if (is_T1 or is_T2) and grade_group in (3, 4) and psa < 20:
        details.append("T1–T2, N0/NX, M0, Grade Group 3–4, PSA <20 → Stage IIC.")
        return "Stage IIC", details

    if (is_T1 or is_T2) and grade_group == 2 and psa < 20:
        details.append("T1–T2, N0/NX, M0, Grade Group 2, PSA <20 → Stage IIB.")
        return "Stage IIB", details

    if grade_group == 1 and psa < 20:
        if ((is_T1 or is_T2a_) and 10 <= psa < 20) or (is_T2b_c and psa < 20):
            details.append("Grade Group 1, N0/NX, M0, PSA <20 with appropriate T → Stage IIA.")
            return "Stage IIA", details

    if grade_group == 1 and (is_T1 or is_T2a_) and psa < 10:
        details.append("cT1–cT2a, N0/NX, M0, Grade Group 1, PSA <10 → Stage I.")
        return "Stage I", details

    details.append("Does not fit standard AJCC 8th prognostic groups with the provided data.")
    return "Stage group cannot be determined", details


# ============================================================
# LAYOUT: header and sidebar
# ============================================================

st.markdown(f"### {APP_NAME}")
st.caption(
    "Clinical decision-support tool for prostate cancer TNM (AJCC 8th), "
    "AJCC prognostic stage, and NCCN risk category based on systematic and targeted biopsy data. "
    "For clinician use only; not a substitute for independent medical judgment."
)

with st.sidebar:
    st.header(APP_NAME)
    st.write(
        "A prostate cancer staging and risk stratification helper that combines:\n"
        "- Clinical TNM (AJCC 8th edition)\n"
        "- Systematic 12-core biopsy\n"
        "- Optional targeted cores\n"
        "- PSA and Grade Group\n\n"
        "Outputs:\n"
        "- AJCC prognostic stage group\n"
        "- NCCN risk category (including favorable vs unfavorable intermediate)\n"
        "- A compact summary line for documentation."
    )

    st.markdown("---")
    st.subheader("Designer")
    st.write(APP_AUTHOR)

    st.markdown("---")
    st.subheader("Usage & Privacy")
    st.write(
        "- Do **not** enter patient identifiers (name, MRN, DOB, etc.).\n"
        "- Use de-identified clinical and pathology data only.\n"
        "- This tool is for **educational and decision-support** use by clinicians."
    )
    st.markdown("---")
    st.subheader("Version")
    st.write(f"{APP_NAME} v{APP_VERSION}")

st.markdown("---")

with st.expander("How to use Prostate Risk Navigator", expanded=False):
    st.markdown(
        "1. Enter **clinical TNM** and **PSA**.\n"
        "2. For each systematic core (A–L), select Benign / Cancer / ASAP and, if cancer, add Gleason and % involvement.\n"
        "3. Optionally add up to 3 **targeted cores** (e.g., MRI lesions).\n"
        "4. Click **“Classify AJCC Stage and NCCN Risk”** to see staging, risk group, and a summary line.\n"
        "5. Use **“Download full report”** or copy the compact summary into your note.\n"
        "6. Click **“Reset form for next patient”** between patients."
    )

# ============================================================
# MAIN UI: TNM & PSA
# ============================================================

st.subheader("Clinical TNM (AJCC 8th ed.)")

c1, c2, c3 = st.columns(3)

with c1:
    t_stage = st.selectbox(
        "T stage",
        T_STAGE_OPTIONS,
        index=T_STAGE_OPTIONS.index(DEFAULT_T_STAGE),
        key="t_stage",
    )
    st.caption(f"**T definition:** {T_STAGE_DEFINITIONS[t_stage]}")

with c2:
    n_stage = st.selectbox(
        "N stage",
        N_STAGE_OPTIONS,
        index=N_STAGE_OPTIONS.index(DEFAULT_N_STAGE),
        key="n_stage",
    )
    st.caption(f"**N definition:** {N_STAGE_DEFINITIONS[n_stage]}")

with c3:
    m_stage = st.selectbox(
        "M stage",
        M_STAGE_OPTIONS,
        index=M_STAGE_OPTIONS.index(DEFAULT_M_STAGE),
        key="m_stage",
    )
    st.caption(f"**M definition:** {M_STAGE_DEFINITIONS[m_stage]}")

st.subheader("PSA")

psa = st.number_input(
    "PSA (ng/mL)",
    min_value=0.0,
    step=0.1,
    value=DEFAULT_PSA,
    key="psa",
)

# ============================================================
# Systematic 12-core biopsy
# ============================================================

st.subheader("Systematic 12-Core Biopsy (Core-Level Pathology)")

st.caption(
    "For each core, choose **Benign**, **Cancer**, or **ASAP**. "
    "If **Cancer** is selected, enter the Gleason primary/secondary patterns and the % of that core involved."
)

for code, label in CORE_SITES:
    with st.expander(f"{code}: {label}", expanded=False):
        type_key = f"{code}_type"
        p_key = f"{code}_p"
        s_key = f"{code}_s"
        pct_key = f"{code}_pct"

        biopsy_type = st.selectbox(
            "Pathology result",
            ["Benign", "Cancer", "ASAP"],
            key=type_key,
            index=0,
        )

        if biopsy_type == "Cancer":
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.selectbox(
                    "Primary Gleason pattern",
                    [3, 4, 5],
                    index=[3, 4, 5].index(DEFAULT_PRIMARY_PATTERN),
                    key=p_key,
                )
            with col_b:
                st.selectbox(
                    "Secondary Gleason pattern",
                    [3, 4, 5],
                    index=[3, 4, 5].index(DEFAULT_SECONDARY_PATTERN),
                    key=s_key,
                )
            with col_c:
                st.slider(
                    "% of core involved by cancer",
                    min_value=1,
                    max_value=100,
                    value=DEFAULT_CORE_PERCENT,
                    key=pct_key,
                )
        elif biopsy_type == "ASAP":
            st.info(
                "ASAP = atypical small acinar proliferation (suspicious but not diagnostic of cancer). "
                "Repeat biopsy is typically recommended in 3–6 months."
            )
        else:
            st.caption("No cancer identified in this core.")

# ============================================================
# Targeted biopsy
# ============================================================

st.subheader("Targeted Biopsy Cores (Optional, e.g. MRI lesions)")

st.caption(
    "Up to **3 targeted cores**. If no targeted cores were taken, leave them as 'Not taken'. "
    "Targeted cores contribute to the **highest Grade Group** but **do not change** the % positive "
    "systematic core calculation for NCCN risk."
)

for code, label in TARGETED_SITES:
    with st.expander(f"{code}: {label}", expanded=False):
        type_key = f"{code}_type"
        p_key = f"{code}_p"
        s_key = f"{code}_s"
        pct_key = f"{code}_pct"
        desc_key = f"{code}_desc"

        biopsy_type = st.selectbox(
            "Pathology result",
            ["Not taken", "Benign", "Cancer", "ASAP"],
            key=type_key,
            index=0,
        )

        st.text_input(
            "Description / site (optional)",
            key=desc_key,
            placeholder="e.g. PIRADS 4 lesion, left anterior apex",
        )

        if biopsy_type == "Cancer":
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.selectbox(
                    "Primary Gleason pattern",
                    [3, 4, 5],
                    index=[3, 4, 5].index(DEFAULT_PRIMARY_PATTERN),
                    key=p_key,
                )
            with col_b:
                st.selectbox(
                    "Secondary Gleason pattern",
                    [3, 4, 5],
                    index=[3, 4, 5].index(DEFAULT_SECONDARY_PATTERN),
                    key=s_key,
                )
            with col_c:
                st.slider(
                    "% of core involved by cancer",
                    min_value=1,
                    max_value=100,
                    value=DEFAULT_CORE_PERCENT,
                    key=pct_key,
                )
        elif biopsy_type == "ASAP":
            st.info("ASAP in targeted core – suspicious, consider repeat biopsy.")
        elif biopsy_type == "Benign":
            st.caption("No cancer identified in this targeted core.")
        else:
            st.caption("Targeted core not obtained.")

# ============================================================
# Classification button
# ============================================================

st.markdown("---")

if st.button("Classify AJCC Stage and NCCN Risk"):
    # Summarize systematic cores
    systematic_cancer_cores = []
    systematic_asap_cores = []
    systematic_benign_cores = []

    high_volume_core = False
    high_grade_cores_gg4_5 = 0

    for code, label in CORE_SITES:
        t_key = f"{code}_type"
        core_type = st.session_state.get(t_key, "Benign")

        if core_type == "Cancer":
            p = int(st.session_state.get(f"{code}_p", DEFAULT_PRIMARY_PATTERN))
            s = int(st.session_state.get(f"{code}_s", DEFAULT_SECONDARY_PATTERN))
            pct = int(st.session_state.get(f"{code}_pct", DEFAULT_CORE_PERCENT))

            gg, gleason_score, desc = gleason_to_grade_group(p, s)

            systematic_cancer_cores.append(
                {
                    "code": code,
                    "label": label,
                    "primary": p,
                    "secondary": s,
                    "gleason_score": gleason_score,
                    "grade_group": gg,
                    "percent": pct,
                    "desc": desc,
                    "systematic": True,
                }
            )

            if pct >= 50:
                high_volume_core = True
            if gg in (4, 5):
                high_grade_cores_gg4_5 += 1

        elif core_type == "ASAP":
            systematic_asap_cores.append((code, label))
        else:
            systematic_benign_cores.append((code, label))

    # Summarize targeted cores
    targeted_cancer_cores = []
    targeted_asap_cores = []
    targeted_benign_cores = []
    targeted_not_taken = []

    for code, label in TARGETED_SITES:
        t_key = f"{code}_type"
        core_type = st.session_state.get(t_key, "Not taken")

        if core_type == "Cancer":
            p = int(st.session_state.get(f"{code}_p", DEFAULT_PRIMARY_PATTERN))
            s = int(st.session_state.get(f"{code}_s", DEFAULT_SECONDARY_PATTERN))
            pct = int(st.session_state.get(f"{code}_pct", DEFAULT_CORE_PERCENT))
            desc_txt = st.session_state.get(f"{code}_desc", "")

            gg, gleason_score, desc = gleason_to_grade_group(p, s)

            targeted_cancer_cores.append(
                {
                    "code": code,
                    "label": label,
                    "desc_txt": desc_txt,
                    "primary": p,
                    "secondary": s,
                    "gleason_score": gleason_score,
                    "grade_group": gg,
                    "percent": pct,
                    "desc": desc,
                    "systematic": False,
                }
            )

            if pct >= 50:
                high_volume_core = True
            if gg in (4, 5):
                high_grade_cores_gg4_5 += 1

        elif core_type == "ASAP":
            targeted_asap_cores.append((code, label))
        elif core_type == "Benign":
            targeted_benign_cores.append((code, label))
        else:
            targeted_not_taken.append((code, label))

    positive_systematic = len(systematic_cancer_cores)
    positive_targeted = len(targeted_cancer_cores)
    total_cancer_cores = positive_systematic + positive_targeted
    asap_count = len(systematic_asap_cores) + len(targeted_asap_cores)

    # No cancer anywhere
    if total_cancer_cores == 0:
        percent_sys_pos = (
            100.0 * positive_systematic / TOTAL_SYSTEMATIC_CORES
            if TOTAL_SYSTEMATIC_CORES > 0 else 0.0
        )

        summary_line = (
            f"No adenocarcinoma identified on biopsy. Systematic cores with cancer: 0/"
            f"{TOTAL_SYSTEMATIC_CORES} (0.0%). ASAP in {asap_count} core(s). "
            f"TNM {t_stage} {n_stage} {m_stage}, PSA {psa:.1f} ng/mL. "
            "AJCC prognostic stage and NCCN risk group are not assigned without confirmed cancer."
        )

        st.subheader("Biopsy Summary")
        st.warning(
            f"No cores with confirmed adenocarcinoma.\n\n"
            f"- Systematic benign cores: {len(systematic_benign_cores)}/{TOTAL_SYSTEMATIC_CORES}\n"
            f"- Targeted benign cores: {len(targeted_benign_cores)}/{len(TARGETED_SITES)}\n"
            f"- ASAP cores (systematic + targeted): {asap_count}\n\n"
            "Risk group and stage require a confirmed cancer diagnosis."
        )

        st.subheader("Compact Summary (copy into note)")
        st.text_area("Summary", value=summary_line, height=80)

        report_text = summary_line + "\n"
        st.download_button(
            "Download summary as .txt",
            data=report_text,
            file_name="prostate_biopsy_summary.txt",
            mime="text/plain",
        )

    else:
        # At least one cancer core
        all_cancer_cores = systematic_cancer_cores + targeted_cancer_cores
        highest_gg = max(c["grade_group"] for c in all_cancer_cores if c["grade_group"] is not None)
        highest_cores = [c for c in all_cancer_cores if c["grade_group"] == highest_gg]
        example_core = highest_cores[0]

        percent_sys_pos = 100.0 * positive_systematic / TOTAL_SYSTEMATIC_CORES

        st.subheader("Biopsy Summary")

        st.markdown(
            f"- Systematic cores with cancer: **{positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
            f"({percent_sys_pos:.1f}%)**.\n"
            f"- Targeted cores with cancer: **{positive_targeted}/{len(TARGETED_SITES)}**.\n"
            f"- Highest Grade Group across all cores: **GG {highest_gg}**, example "
            f"{example_core['code']} {example_core['label']} "
            f"Gleason {example_core['primary']}+{example_core['secondary']}="
            f"{example_core['gleason_score']}."
        )

        if high_volume_core:
            st.markdown("- At least one core has **≥50% involvement** (high-volume core).")
        else:
            st.markdown("- No core with ≥50% involvement recorded.")

        if high_grade_cores_gg4_5 > 0:
            st.markdown(f"- Number of cores with **Grade Group 4–5**: {high_grade_cores_gg4_5}.")
        else:
            st.markdown("- No cores with Grade Group 4–5.")

        if asap_count > 0:
            st.markdown(f"- ASAP present in {asap_count} core(s).")

        st.write("**Cancer cores (per-core detail)**")
        for c in all_cancer_cores:
            origin = "Systematic" if c["systematic"] else "Targeted"
            extra = ""
            if not c["systematic"] and c.get("desc_txt"):
                extra = f" ({c['desc_txt']})"
            st.markdown(
                f"- **{origin} {c['code']} – {c['label']}{extra}**: Gleason "
                f"{c['primary']}+{c['secondary']}={c['gleason_score']} "
                f"(Grade Group {c['grade_group']}), ~{c['percent']:.0f}% of core."
            )

        # AJCC Stage and NCCN risk use highest GG and systematic cores for % positive
        ajcc_stage, ajcc_info = classify_ajcc_stage(
            t_stage=t_stage,
            n_stage=n_stage,
            m_stage=m_stage,
            psa=float(psa),
            grade_group=int(highest_gg),
        )

        st.subheader("AJCC Prognostic Stage Group")
        st.info(f"**{ajcc_stage}**")
        for line in ajcc_info:
            st.markdown(f"- {line}")

        risk_group, subcategory, risk_info = classify_nccn_risk(
            t_stage=t_stage,
            n_stage=n_stage,
            m_stage=m_stage,
            grade_group=int(highest_gg),
            psa=float(psa),
            cores_positive=positive_systematic,
            cores_total=TOTAL_SYSTEMATIC_CORES,
        )

        st.subheader("NCCN Risk Group (Clinically Localized Disease)")
        if subcategory:
            st.success(f"**{risk_group} – {subcategory} intermediate**")
        else:
            st.success(f"**{risk_group}**")
        for line in risk_info:
            st.markdown(f"- {line}")

        # Compact summary line
        risk_text = risk_group
        if subcategory:
            risk_text += f" ({subcategory} intermediate)"

        summary_line = (
            f"{t_stage} {n_stage} {m_stage}, PSA {psa:.1f} ng/mL, highest biopsy GG {highest_gg} "
            f"(Gleason {example_core['primary']}+{example_core['secondary']}="
            f"{example_core['gleason_score']}), AJCC {ajcc_stage}, NCCN {risk_text}; "
            f"systematic cancer cores {positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
            f"({percent_sys_pos:.1f}%), targeted cancer cores {positive_targeted}/{len(TARGETED_SITES)}."
        )

        st.subheader("Compact Summary (copy into note)")
        st.text_area("Summary", value=summary_line, height=80)

        # Full text report (more detailed)
        lines = []
        lines.append(f"{APP_NAME} – Prostate cancer staging summary")
        lines.append("")
        lines.append(f"TNM: {t_stage}, {n_stage}, {m_stage}")
        lines.append(f"PSA: {psa:.1f} ng/mL")
        lines.append(
            "Highest biopsy Grade Group: "
            f"{highest_gg} (example {example_core['code']} {example_core['label']} "
            f"Gleason {example_core['primary']}+{example_core['secondary']}="
            f"{example_core['gleason_score']})"
        )
        lines.append("")
        lines.append(
            f"Systematic cores with cancer: {positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
            f"({percent_sys_pos:.1f}%)"
        )
        lines.append(f"Targeted cores with cancer: {positive_targeted}/{len(TARGETED_SITES)}")
        if high_volume_core:
            lines.append("At least one core has ≥50% involvement.")
        if high_grade_cores_gg4_5 > 0:
            lines.append(f"Cores with Grade Group 4–5: {high_grade_cores_gg4_5}")
        if asap_count > 0:
            lines.append(f"ASAP present in {asap_count} core(s).")
        lines.append("")
        lines.append(f"AJCC prognostic stage group: {ajcc_stage}")
        for l in ajcc_info:
            lines.append(f"- {l}")
        lines.append("")
        lines.append(f"NCCN risk group: {risk_text}")
        for l in risk_info:
            lines.append(f"- {l}")
        lines.append("")
        lines.append("Per-core cancer details:")
        for c in all_cancer_cores:
            origin = "Systematic" if c["systematic"] else "Targeted"
            extra = ""
            if not c["systematic"] and c.get("desc_txt"):
                extra = f" ({c['desc_txt']})"
            lines.append(
                f"- {origin} {c['code']} – {c['label']}{extra}: "
                f"Gleason {c['primary']}+{c['secondary']}={c['gleason_score']} "
                f"(Grade Group {c['grade_group']}), approx. {c['percent']}% of core."
            )

        report_text = "\n".join(lines)

        st.download_button(
            "Download full report as .txt",
            data=report_text,
            file_name="prostate_cancer_staging_report.txt",
            mime="text/plain",
        )

# ============================================================
# Reset button using a callback
# ============================================================

st.markdown("---")

def reset_form():
    # TNM + PSA
    st.session_state["t_stage"] = DEFAULT_T_STAGE
    st.session_state["n_stage"] = DEFAULT_N_STAGE
    st.session_state["m_stage"] = DEFAULT_M_STAGE
    st.session_state["psa"] = DEFAULT_PSA

    # Systematic cores
    for code, _ in CORE_SITES:
        st.session_state[f"{code}_type"] = "Benign"
        st.session_state[f"{code}_p"] = DEFAULT_PRIMARY_PATTERN
        st.session_state[f"{code}_s"] = DEFAULT_SECONDARY_PATTERN
        st.session_state[f"{code}_pct"] = DEFAULT_CORE_PERCENT

    # Targeted cores
    for code, _ in TARGETED_SITES:
        st.session_state[f"{code}_type"] = "Not taken"
        st.session_state[f"{code}_p"] = DEFAULT_PRIMARY_PATTERN
        st.session_state[f"{code}_s"] = DEFAULT_SECONDARY_PATTERN
        st.session_state[f"{code}_pct"] = DEFAULT_CORE_PERCENT
        st.session_state[f"{code}_desc"] = ""

st.button("Reset form for next patient", on_click=reset_form)

# ============================================================
# Footer with copyright
# ============================================================

st.markdown(
    f"""
    <div style="text-align:center; font-size:0.8rem; color:#888; padding-top:1.5rem;">
        © {APP_YEAR} {APP_AUTHOR}. {APP_NAME}. All rights reserved.<br/>
        This tool is provided for educational and decision-support purposes and is not a medical device.
    </div>
    """,
    unsafe_allow_html=True,
)
