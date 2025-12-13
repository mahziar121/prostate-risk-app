import streamlit as st

# ============================================================
# Page config / app metadata
# ============================================================

APP_NAME = "Prostate Risk Navigator"
APP_VERSION = "1.3.2"  # updated UI version
APP_AUTHOR = "Mahziar Khazaali, MD"
APP_YEAR = "2025"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide",
)


# ============================================================
# Helper for links/buttons
# ============================================================

def link_button_or_markdown(label: str, url: str):
    """Use st.link_button if available, otherwise fall back to a markdown link."""
    if hasattr(st, "link_button"):
        st.link_button(label, url)
    else:
        st.markdown(f"[{label}]({url})")


# ============================================================
# Constants / defaults
# ============================================================

DEFAULT_CT_STAGE = "cT1c"
DEFAULT_CN_STAGE = "cN0"
DEFAULT_CM_STAGE = "cM0"

DEFAULT_PT_STAGE = "pT2"
DEFAULT_PN_STAGE = "pN0"

DEFAULT_PSA = 6.5

DEFAULT_PRIMARY_PATTERN = 3
DEFAULT_SECONDARY_PATTERN = 3
DEFAULT_CORE_PERCENT = 10  # integer slider

DEFAULT_STAGE_CONTEXT = "Clinical staging (cTNM)"

DEFAULT_MARGIN = "Unknown / not applicable"
MARGIN_OPTIONS = [
    DEFAULT_MARGIN,
    "Negative margin (R0)",
    "Focally positive margin (R1, focal)",
    "Extensively positive margin (R1, extensive)",
]
MARGIN_EXPLANATIONS = {
    DEFAULT_MARGIN: "Margin status not available or not applicable (no radical prostatectomy data entered).",
    "Negative margin (R0)": "No tumor at the inked surgical margin.",
    "Focally positive margin (R1, focal)": "Limited tumor at the inked margin; recurrence risk depends on location and length.",
    "Extensively positive margin (R1, extensive)": "Extensive tumor at the inked margin; associated with higher risk of biochemical recurrence.",
}

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

TARGETED_SITES = [
    ("T1", "Targeted core 1"),
    ("T2", "Targeted core 2"),
    ("T3", "Targeted core 3"),
]


# ============================================================
# TNM definitions (AJCC 8th) – clinical & pathologic
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
    "cT3a": "Extraprostatic tumor that is not fixed and does not invade adjacent structures",
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

# Pathologic T & N (post–radical prostatectomy)
PT_STAGE_DEFINITIONS = {
    "pT2": "Organ confined (including apex and capsule involvement, but not beyond prostate)",
    "pT3a": "Extraprostatic extension (unilateral or bilateral) and/or microscopic bladder neck invasion",
    "pT3b": "Tumor invades seminal vesicle(s)",
    "pT4": "Tumor is fixed or invades structures other than seminal vesicles "
            "(external sphincter, rectum, bladder, levator muscles, and/or pelvic wall)",
}
PT_STAGE_OPTIONS = list(PT_STAGE_DEFINITIONS.keys())

PN_STAGE_DEFINITIONS = {
    "pNX": "Regional lymph nodes cannot be assessed pathologically",
    "pN0": "No positive regional lymph nodes on pathology",
    "pN1": "Metastases in regional lymph node(s) on pathology",
}
PN_STAGE_OPTIONS = list(PN_STAGE_DEFINITIONS.keys())


# ============================================================
# Helper functions: normalize TNM (accepts cT/pT, cN/pN)
# ============================================================

def _normalize_stage(stage: str, letter: str) -> str:
    """
    Normalize TNM strings to lowercase 't2a', 'n1', 'm1b', etc.
    Accepts cT2a, pT3a, T2b, etc.
    """
    s = stage.strip().lower()
    if s.startswith(("c", "p")):
        s = s[1:]
    if not s.startswith(letter):
        raise ValueError(
            f"{letter.upper()} stage must start with {letter.upper()}, c{letter.upper()}, or p{letter.upper()}, "
            f"e.g. 'c{letter.upper()}2a' or 'p{letter.upper()}3a'"
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
# NCCN risk groups (clinically localized disease)
# ============================================================

def classify_nccn_risk(
    t_stage: str,
    n_stage: str,
    m_stage: str,
    grade_group: int,
    psa: float,
    cores_positive: int,
    cores_total: int,
):
    details = []
    details.append(f"Clinical TNM: {t_stage}, {n_stage}, {m_stage}")
    details.append(f"PSA {psa:.1f} ng/mL, highest biopsy Grade Group {grade_group}")

    if cores_total <= 0:
        raise ValueError("Total cores must be > 0")

    percent_cores = 100.0 * cores_positive / cores_total
    details.append(
        f"Systematic cores positive for cancer: {cores_positive}/{cores_total} "
        f"({percent_cores:.1f}%)"
    )

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
# Additional Evaluation recommendations (simplified NCCN-style)
# ============================================================

def get_additional_evaluation_recommendations(risk_group: str | None, subcategory: str | None):
    if risk_group is None:
        return None, []

    rg = risk_group.strip()
    sub = (subcategory or "").strip()

    if rg == "Low":
        title = "Low-risk localized prostate cancer"
        items = [
            "If active surveillance is being considered, confirm that the patient is an appropriate candidate.",
            "Consider confirmatory testing such as repeat biopsy, multiparametric MRI, and/or validated biomarkers.",
        ]
        return title, items

    if rg == "Intermediate" and sub == "Favorable":
        title = "Favorable intermediate-risk localized prostate cancer"
        items = [
            "If active surveillance or conservative treatment is being considered, confirm that criteria are met.",
            "Consider confirmatory testing (repeat biopsy, mpMRI, and/or biomarkers) to refine risk assessment.",
        ]
        return title, items

    if rg == "Intermediate" and sub == "Unfavorable":
        title = "Unfavorable intermediate-risk localized prostate cancer"
        items = [
            "Obtain pelvic soft-tissue imaging (CT or MRI).",
            "Consider bone imaging (bone scan or PSMA PET/CT), especially with higher PSA or multiple risk factors.",
            "If regional metastases are found, follow node-positive (cN1) pathways.",
            "If distant metastases are found, use metastatic castration-sensitive prostate cancer pathways.",
        ]
        return title, items

    if rg == "High":
        title = "High-risk localized prostate cancer"
        items = [
            "Obtain pelvic CT or MRI.",
            "Obtain bone imaging (bone scan or PSMA PET/CT).",
            "If regional lymph node metastases are detected, manage as node-positive disease.",
            "If distant metastases are detected, manage as metastatic castration-sensitive prostate cancer.",
        ]
        return title, items

    if rg == "Very high":
        title = "Very high-risk localized prostate cancer"
        items = [
            "Obtain pelvic CT or MRI.",
            "Obtain bone imaging (bone scan or PSMA PET/CT); there is a high probability of metastatic disease.",
            "If regional lymph node metastases are detected, manage as node-positive disease.",
            "If distant metastases are detected, follow metastatic castration-sensitive pathways and consider clinical trials.",
        ]
        return title, items

    if "Metastatic/regional" in rg:
        title = "Regional or metastatic disease"
        items = [
            "Ensure complete staging with cross-sectional imaging and bone imaging (or PSMA PET/CT).",
            "Classify disease volume and distribution (node-only vs bone vs visceral) to guide therapy choices.",
        ]
        return title, items

    return None, []


# ============================================================
# Disease category & treatment options (educational)
# ============================================================

def classify_disease_category(n_stage: str, m_stage: str) -> str:
    if has_distant_metastasis(m_stage):
        return "Metastatic CSPC (M1)"
    if has_regional_nodes(n_stage) and not has_distant_metastasis(m_stage):
        return "Node-positive (N1, M0)"
    if (not has_regional_nodes(n_stage)) and not has_distant_metastasis(m_stage):
        return "Localized"
    return "Uncertain"


def get_treatment_options(disease_category: str,
                          risk_group: str | None,
                          subcategory: str | None):
    sections: list[tuple[str, list[str]]] = []

    if disease_category.startswith("Metastatic"):
        title = "Metastatic castration-sensitive prostate cancer (M1)"
        sections.append((
            "Systemic backbone",
            [
                "Androgen deprivation therapy (ADT) is the backbone for all patients.",
                "ADT monotherapy is generally avoided in fit patients; intensification improves survival.",
            ],
        ))
        sections.append((
            "Intensification options (examples)",
            [
                "ADT + a next-generation AR-targeted agent (e.g., abiraterone, apalutamide, enzalutamide, darolutamide), "
                "considering comorbidities and interactions.",
                "ADT + docetaxel in selected patients (often higher-volume disease).",
                "ADT + docetaxel + AR-targeted agent in very fit patients according to contemporary trials.",
            ],
        ))
        sections.append((
            "Additional considerations",
            [
                "Stratify by disease volume (low vs high; oligometastatic vs polymetastatic).",
                "Consider prostate-directed RT in selected low-volume metastatic cases.",
                "Discuss clinical trials when available.",
            ],
        ))
        return title, sections

    if disease_category.startswith("Node-positive"):
        title = "Clinically node-positive, non-metastatic prostate cancer (N1, M0)"
        sections.append((
            "Typical management frameworks",
            [
                "Definitive radiotherapy to the prostate ± pelvic nodes plus long-term ADT.",
                "Systemic intensification (e.g., addition of an AR-targeted agent) may be appropriate; check current guidelines.",
            ],
        ))
        sections.append((
            "Other options / special situations",
            [
                "Selected patients may undergo radical prostatectomy with extended lymph node dissection in high-volume centers, "
                "usually within a multimodal plan.",
                "Consider multidisciplinary tumor board discussion and clinical trials.",
            ],
        ))
        sections.append((
            "Supportive / follow-up care",
            [
                "Monitor PSA and testosterone to confirm castration levels on ADT.",
                "Address bone health, cardiovascular risk, and quality-of-life issues from long-term ADT.",
            ],
        ))
        return title, sections

    if disease_category == "Localized" and risk_group:
        rg = risk_group.strip()
        sub = (subcategory or "").strip()
        title = f"Treatment options for localized {rg.lower()} risk prostate cancer"

        if rg == "Low":
            sections.append((
                "Conservative / surveillance",
                [
                    "Active surveillance is appropriate for many patients with low-risk disease and adequate life expectancy.",
                    "Watchful waiting may be considered in men with limited life expectancy or major comorbidities.",
                ],
            ))
            sections.append((
                "Definitive local therapy",
                [
                    "Radical prostatectomy with pelvic lymph node assessment in selected patients.",
                    "External beam radiotherapy (EBRT) with modern dose-escalated techniques.",
                    "Low- or high-dose-rate brachytherapy in centers with expertise.",
                ],
            ))
            return title, sections

        if rg == "Intermediate" and sub == "Favorable":
            sections.append((
                "Conservative options (selected patients)",
                [
                    "Active surveillance may be considered in very carefully selected favorable intermediate-risk men "
                    "(e.g., limited volume, GG 1–2, low PSA density).",
                ],
            ))
            sections.append((
                "Definitive local therapy",
                [
                    "Radical prostatectomy ± pelvic lymph node dissection.",
                    "EBRT alone, or EBRT with short-term ADT.",
                    "Brachytherapy-based approaches in experienced centers.",
                ],
            ))
            return title, sections

        if rg == "Intermediate" and sub == "Unfavorable":
            sections.append((
                "Definitive local therapy (typical)",
                [
                    "Radical prostatectomy with pelvic lymph node dissection as part of a multimodal plan.",
                    "EBRT + short-term ADT (e.g., 4–6 months).",
                    "EBRT + brachytherapy boost + ADT in selected, fit patients.",
                ],
            ))
            sections.append((
                "Other considerations",
                [
                    "Discuss risks and benefits of combined-modality vs single-modality treatment.",
                    "Consider clinical trials in appropriate candidates.",
                ],
            ))
            return title, sections

        if rg in ("High", "Very high"):
            sections.append((
                "Multimodal therapy",
                [
                    "EBRT to prostate/pelvis + long-term ADT (e.g., 18–36 months) is a standard backbone.",
                    "Systemic intensification (e.g., docetaxel or an AR-targeted agent) may be considered in selected patients.",
                ],
            ))
            sections.append((
                "Surgical options",
                [
                    "Radical prostatectomy with extended pelvic lymph node dissection in carefully selected men, "
                    "usually within a multimodal strategy.",
                ],
            ))
            sections.append((
                "Additional points",
                [
                    "Consider clinical trials for high and very high-risk disease.",
                    "Discuss potential need for adjuvant or early-salvage radiotherapy after surgery.",
                ],
            ))
            return title, sections

    return None, []


# ============================================================
# AJCC 8th prognostic stage groups
# ============================================================

def classify_ajcc_stage(
    t_stage: str,
    n_stage: str,
    m_stage: str,
    psa: float,
    grade_group: int | None,
):
    details: list[str] = []
    details.append(f"TNM used for staging: {t_stage}, {n_stage}, {m_stage}")
    details.append(f"PSA {psa:.1f} ng/mL")

    if grade_group is None:
        details.append(
            "Grade Group not provided. AJCC 8th prognostic grouping requires Grade Group; "
            "stage group cannot be assigned without it."
        )
        return "Stage group cannot be determined (Grade Group unknown)", details

    details.append(f"Grade Group {grade_group}")

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
# AJCC prognostic context (with approximate population numbers)
# ============================================================

def get_ajcc_stage_explanation(ajcc_stage: str):
    parts = ajcc_stage.split()
    stage_code = parts[1] if len(parts) > 1 else ""

    short = None
    bullets: list[str] = []

    if stage_code == "I":
        short = "Very favorable, low-volume localized disease."
        bullets = [
            "Tumor is organ-confined with low PSA and Grade Group 1.",
            "Roughly corresponds to 'localized' disease in registry datasets.",
            "Recent US registry data show ≈100% 10-year relative survival for localized prostate cancer.",
        ]

    elif stage_code.startswith("II"):
        short = "Localized disease with increasing biologic risk."
        bullets = [
            "Cancer is still confined to the prostate but has higher PSA and/or Grade Group than Stage I.",
            "Also falls within the 'localized' category in large registries.",
            "For localized prostate cancer overall, 5-year relative survival is >99% and 10-year is around 100% in recent cohorts.",
        ]

    elif stage_code.startswith("III"):
        short = "Locally advanced or biologically high-risk localized disease."
        bullets = [
            "Includes extraprostatic extension (T3–T4) and/or very high PSA or Grade Group 5 even if organ-confined.",
            "Most of these cases align with 'regional' stage (spread outside prostate but not distant).",
            "For regional prostate cancer, 5-year relative survival remains >99%, and 10-year relative survival is ≈96% in US data.",
        ]

    elif stage_code.startswith("IVA"):
        short = "Node-positive, non-metastatic prostate cancer."
        bullets = [
            "Cancer has spread to regional lymph nodes but not to distant organs.",
            "Also counted as 'regional' disease in summary-stage statistics.",
            "Population data show regional prostate cancer with >99% 5-year and ≈96% 10-year relative survival, "
            "though prognosis is worse than purely organ-confined disease.",
        ]

    elif stage_code.startswith("IVB"):
        short = "Metastatic prostate cancer (distant disease)."
        bullets = [
            "Cancer has spread beyond the pelvis (e.g., bone, distant lymph nodes, or visceral organs).",
            "This corresponds to 'distant' stage in registry reports.",
            "In large cohorts, distant metastatic prostate cancer has ≈30–40% 5-year relative survival and roughly 18–20% 10-year relative survival, "
            "although outcomes are improving with modern treatment intensification.",
        ]

    if short is not None:
        bullets += [
            "These percentages are approximate population averages from historical registry data, "
            "not specific to any individual patient or AJCC substage.",
            "They do not account for age, comorbidities, treatment choice, genomic classifiers, or treatment response.",
            "For patient-specific estimates, use validated nomograms (e.g., PREDICT Prostate, MSKCC) together with clinical judgment.",
        ]

    return short, bullets


# ============================================================
# Helper: render biopsy input UI (used in both clinical & pathologic modes)
# ============================================================

def render_biopsy_inputs():
    """
    Renders systematic and targeted biopsy input widgets.
    Used in both clinical and pathologic modes; in pathologic mode
    it will be wrapped inside an expander (historical data).
    """
    st.subheader("Systematic 12-Core Biopsy (Core-Level Pathology)")
    st.caption(
        "For each core, choose **Benign**, **Cancer**, or **ASAP**. "
        "If **Cancer** is selected, enter Gleason patterns, % involvement, and whether "
        "extraprostatic extension (EPE) or perineural invasion (PNI) is seen in that core."
    )

    for code, label in CORE_SITES:
        with st.expander(f"{code}: {label}", expanded=False):
            type_key = f"{code}_type"
            p_key = f"{code}_p"
            s_key = f"{code}_s"
            pct_key = f"{code}_pct"
            epe_key = f"{code}_epe"
            pni_key = f"{code}_pni"

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
                st.checkbox(
                    "Extraprostatic extension (EPE) in this core",
                    key=epe_key,
                    value=False,
                )
                st.checkbox(
                    "Perineural invasion (PNI) in this core",
                    key=pni_key,
                    value=False,
                )
            elif biopsy_type == "ASAP":
                st.info(
                    "ASAP = atypical small acinar proliferation (suspicious but not diagnostic of cancer). "
                    "Repeat biopsy is typically recommended in 3–6 months."
                )
            else:
                st.caption("No cancer identified in this core.")

    st.subheader("Targeted Biopsy Cores (Optional, e.g. MRI lesions)")

    st.caption(
        "Up to **3 targeted cores**. If no targeted cores were taken, leave them as 'Not taken'. "
        "Targeted cores contribute to the **highest Grade Group** but do **not** change the % positive "
        "systematic core calculation for NCCN risk."
    )

    for code, label in TARGETED_SITES:
        with st.expander(f"{code}: {label}", expanded=False):
            type_key = f"{code}_type"
            p_key = f"{code}_p"
            s_key = f"{code}_s"
            pct_key = f"{code}_pct"
            epe_key = f"{code}_epe"
            pni_key = f"{code}_pni"
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
                st.checkbox(
                    "Extraprostatic extension (EPE) in this targeted core",
                    key=epe_key,
                    value=False,
                )
                st.checkbox(
                    "Perineural invasion (PNI) in this targeted core",
                    key=pni_key,
                    value=False,
                )
            elif biopsy_type == "ASAP":
                st.info("ASAP in targeted core – suspicious, consider repeat biopsy.")
            elif biopsy_type == "Benign":
                st.caption("No cancer identified in this targeted core.")
            else:
                st.caption("Targeted core not obtained.")


# ============================================================
# LAYOUT: header and sidebar
# ============================================================

st.markdown(f"### {APP_NAME}")
st.caption(
    "Clinical decision-support tool for prostate cancer TNM (AJCC 8th), "
    "AJCC prognostic stage, NCCN risk category (clinical setting), and biopsy-level features. "
    "For clinician use only; not a substitute for independent medical judgment."
)

with st.sidebar:
    st.header(APP_NAME)
    st.write(
        "Combines:\n"
        "- Clinical TNM (cTNM)\n"
        "- Optional pathologic TNM (pTNM, post-RP)\n"
        "- Systematic 12-core and targeted biopsy data\n"
        "- PSA and Grade Group\n\n"
        "Outputs:\n"
        "- AJCC prognostic stage (clinical or pathologic basis)\n"
        "- NCCN risk group (when clinical + biopsy data are available)\n"
        "- Compact summary line for documentation."
    )
    st.markdown("---")
    st.subheader("Designer")
    st.write(APP_AUTHOR)
    st.markdown("---")
    st.subheader("Usage & Privacy")
    st.write(
        "- Do **not** enter patient identifiers (name, MRN, DOB, etc.).\n"
        "- Use de-identified clinical and pathology data only.\n"
        "- Educational / decision-support only; not a medical device."
    )
    st.markdown("---")
    st.subheader("Version")
    st.write(f"{APP_NAME} v{APP_VERSION}")

st.markdown("---")

with st.expander("How to use Prostate Risk Navigator", expanded=False):
    st.markdown(
        "1. Choose whether you are staging on a **clinical** or **pathologic (post-RP)** basis.\n"
        "2. Enter TNM, PSA, and (if no biopsy data) an overall **Grade Group**.\n"
        "3. If you have biopsy details, check the box and fill out systematic/targeted cores "
        "including Gleason patterns, % involvement, EPE and PNI.\n"
        "4. Click **“Classify AJCC Stage and NCCN Risk”**.\n"
        "5. Review:\n"
        "   - AJCC prognostic stage + context\n"
        "   - NCCN risk group (when applicable)\n"
        "   - Treatment options and additional evaluation\n"
        "   - Biopsy summary and adverse features\n"
        "6. Use **“Download full report”** or copy the compact summary into your note.\n"
        "7. Click **“Reset form for next patient”** between cases."
    )


# ============================================================
# TNM & PSA + staging context
# ============================================================

st.subheader("Staging context and TNM")

stage_context = st.radio(
    "Staging basis for AJCC prognostic group:",
    ["Clinical staging (cTNM)", "Pathologic staging after radical prostatectomy (pTNM)"],
    index=0,
    key="stage_context",
)

if stage_context.startswith("Clinical"):
    st.markdown("**Clinical TNM (cTNM)**")
    c1, c2, c3 = st.columns(3)
    with c1:
        ct_stage = st.selectbox(
            "Clinical T stage (cT)",
            T_STAGE_OPTIONS,
            index=T_STAGE_OPTIONS.index(DEFAULT_CT_STAGE),
            key="ct_stage",
        )
        st.caption(f"**Clinical T definition:** {T_STAGE_DEFINITIONS[ct_stage]}")
    with c2:
        cn_stage = st.selectbox(
            "Clinical N stage (cN)",
            N_STAGE_OPTIONS,
            index=N_STAGE_OPTIONS.index(DEFAULT_CN_STAGE),
            key="cn_stage",
        )
        st.caption(f"**Clinical N definition:** {N_STAGE_DEFINITIONS[cn_stage]}")
    with c3:
        cm_stage = st.selectbox(
            "M stage (clinical M)",
            M_STAGE_OPTIONS,
            index=M_STAGE_OPTIONS.index(DEFAULT_CM_STAGE),
            key="cm_stage",
        )
        st.caption(f"**M definition:** {M_STAGE_DEFINITIONS[cm_stage]}")

else:
    st.markdown("**Pathologic TNM (pTNM) with clinical M**")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        pt_stage_widget = st.selectbox(
            "Pathologic T stage (pT)",
            PT_STAGE_OPTIONS,
            index=PT_STAGE_OPTIONS.index(DEFAULT_PT_STAGE),
            key="pt_stage",
        )
        st.caption(f"**Pathologic T definition:** {PT_STAGE_DEFINITIONS[pt_stage_widget]}")
    with pc2:
        pn_stage_widget = st.selectbox(
            "Pathologic N stage (pN)",
            PN_STAGE_OPTIONS,
            index=PN_STAGE_OPTIONS.index(DEFAULT_PN_STAGE),
            key="pn_stage",
        )
        st.caption(f"**Pathologic N definition:** {PN_STAGE_DEFINITIONS[pn_stage_widget]}")
    with pc3:
        cm_stage = st.selectbox(
            "M stage (clinical M)",
            M_STAGE_OPTIONS,
            index=M_STAGE_OPTIONS.index(DEFAULT_CM_STAGE),
            key="cm_stage",
        )
        st.caption(f"**M definition:** {M_STAGE_DEFINITIONS[cm_stage]}")

    margin_option = st.selectbox(
        "Surgical margin status (radical prostatectomy)",
        MARGIN_OPTIONS,
        index=MARGIN_OPTIONS.index(DEFAULT_MARGIN),
        key="rp_margin",
    )
    st.caption(MARGIN_EXPLANATIONS[margin_option])

st.subheader("PSA and overall Grade Group")

psa = st.number_input(
    "PSA (ng/mL)",
    min_value=0.0,
    step=0.1,
    value=DEFAULT_PSA,
    key="psa",
)

manual_gg_option = st.selectbox(
    "Overall Grade Group (if biopsy / RP grade is known but detailed cores are not entered)",
    ["Unknown", 1, 2, 3, 4, 5],
    index=0,
    key="manual_gg",
)
manual_grade_group = None if manual_gg_option == "Unknown" else int(manual_gg_option)

# ============================================================
# Biopsy toggle + display mode
# ============================================================

has_biopsy_details = st.checkbox(
    "I have detailed systematic and/or targeted biopsy data",
    value=True,
    key="has_biopsy_details",
)

if has_biopsy_details:
    if stage_context.startswith("Clinical"):
        # Normal display in clinical mode
        render_biopsy_inputs()
    else:
        # In pathologic mode, biopsy is historical and shown collapsed by default
        with st.expander(
            "Pre-operative biopsy (historical – does not affect pathologic AJCC stage)",
            expanded=False,
        ):
            st.caption(
                "These biopsy findings are pre-operative and used for context (e.g. upgrade/downgrade, "
                "% positive cores, EPE/PNI on biopsy). Pathologic AJCC staging is determined by the "
                "radical prostatectomy specimen (pT, pN, margins) rather than biopsy."
            )
            render_biopsy_inputs()

st.markdown("---")

# ============================================================
# Classification
# ============================================================

if st.button("Classify AJCC Stage and NCCN Risk"):
    # ---------- Collect biopsy data (if present) ----------
    systematic_cancer_cores = []
    targeted_cancer_cores = []
    systematic_asap_cores = []
    targeted_asap_cores = []
    systematic_benign_cores = []
    targeted_benign_cores = []

    high_volume_core = False
    high_grade_cores_gg4_5 = 0
    asap_count = 0

    epe_count_any = 0
    pni_count_any = 0
    any_epe_high_gg = False  # EPE in GG ≥3
    any_pni_high_gg = False  # PNI in GG ≥3

    if has_biopsy_details:
        # Systematic cores
        for code, label in CORE_SITES:
            t_key = f"{code}_type"
            core_type = st.session_state.get(t_key, "Benign")

            if core_type == "Cancer":
                p = int(st.session_state.get(f"{code}_p", DEFAULT_PRIMARY_PATTERN))
                s = int(st.session_state.get(f"{code}_s", DEFAULT_SECONDARY_PATTERN))
                pct = int(st.session_state.get(f"{code}_pct", DEFAULT_CORE_PERCENT))
                epe = bool(st.session_state.get(f"{code}_epe", False))
                pni = bool(st.session_state.get(f"{code}_pni", False))

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
                        "epe": epe,
                        "pni": pni,
                    }
                )

                if pct >= 50:
                    high_volume_core = True
                if gg in (4, 5):
                    high_grade_cores_gg4_5 += 1
                if epe:
                    epe_count_any += 1
                    if gg is not None and gg >= 3:
                        any_epe_high_gg = True
                if pni:
                    pni_count_any += 1
                    if gg is not None and gg >= 3:
                        any_pni_high_gg = True

            elif core_type == "ASAP":
                systematic_asap_cores.append((code, label))
                asap_count += 1
            else:
                systematic_benign_cores.append((code, label))

        # Targeted cores
        for code, label in TARGETED_SITES:
            t_key = f"{code}_type"
            core_type = st.session_state.get(t_key, "Not taken")

            if core_type == "Cancer":
                p = int(st.session_state.get(f"{code}_p", DEFAULT_PRIMARY_PATTERN))
                s = int(st.session_state.get(f"{code}_s", DEFAULT_SECONDARY_PATTERN))
                pct = int(st.session_state.get(f"{code}_pct", DEFAULT_CORE_PERCENT))
                epe = bool(st.session_state.get(f"{code}_epe", False))
                pni = bool(st.session_state.get(f"{code}_pni", False))
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
                        "epe": epe,
                        "pni": pni,
                    }
                )

                if pct >= 50:
                    high_volume_core = True
                if gg in (4, 5):
                    high_grade_cores_gg4_5 += 1
                if epe:
                    epe_count_any += 1
                    if gg is not None and gg >= 3:
                        any_epe_high_gg = True
                if pni:
                    pni_count_any += 1
                    if gg is not None and gg >= 3:
                        any_pni_high_gg = True

            elif core_type == "ASAP":
                targeted_asap_cores.append((code, label))
                asap_count += 1
            elif core_type == "Benign":
                targeted_benign_cores.append((code, label))
            else:
                # Not taken
                pass

    # Summaries derived from biopsy data (if any)
    all_cancer_cores = systematic_cancer_cores + targeted_cancer_cores
    positive_systematic = len(systematic_cancer_cores)
    positive_targeted = len(targeted_cancer_cores)

    percent_sys_pos = (
        100.0 * positive_systematic / TOTAL_SYSTEMATIC_CORES
        if TOTAL_SYSTEMATIC_CORES > 0
        else 0.0
    )

    any_epe_any = epe_count_any > 0
    any_pni_any = pni_count_any > 0

    # Determine Grade Group to use for staging
    if all_cancer_cores:
        highest_gg = max(
            c["grade_group"] for c in all_cancer_cores if c["grade_group"] is not None
        )
        highest_cores = [c for c in all_cancer_cores if c["grade_group"] == highest_gg]
        example_core = highest_cores[0]
        grade_for_stage = highest_gg
    else:
        highest_gg = None
        example_core = None
        grade_for_stage = manual_grade_group

    # Retrieve TNM & margin from session state (works in both modes)
    ct_stage_ss = st.session_state.get("ct_stage", DEFAULT_CT_STAGE)
    cn_stage_ss = st.session_state.get("cn_stage", DEFAULT_CN_STAGE)
    cm_stage_ss = st.session_state.get("cm_stage", DEFAULT_CM_STAGE)
    pt_stage_ss = st.session_state.get("pt_stage", DEFAULT_PT_STAGE)
    pn_stage_ss = st.session_state.get("pn_stage", DEFAULT_PN_STAGE)
    rp_margin = st.session_state.get("rp_margin", DEFAULT_MARGIN)

    # Choose which TNM to use for AJCC
    if stage_context.startswith("Pathologic"):
        t_for_stage = pt_stage_ss
        n_for_stage = pn_stage_ss
        staging_basis_label = "AJCC stage based on pathologic pTNM (post–radical prostatectomy)."
    else:
        t_for_stage = ct_stage_ss
        n_for_stage = cn_stage_ss
        staging_basis_label = "AJCC stage based on clinical cTNM."

    m_for_stage = cm_stage_ss

    # ---------- AJCC Stage ----------
    ajcc_stage, ajcc_info = classify_ajcc_stage(
        t_stage=t_for_stage,
        n_stage=n_for_stage,
        m_stage=m_for_stage,
        psa=float(psa),
        grade_group=grade_for_stage,
    )

    st.subheader("AJCC 8th Prognostic Stage Group")
    st.info(f"**{ajcc_stage}**")
    st.caption(staging_basis_label)
    for line in ajcc_info:
        st.markdown(f"- {line}")

    short_label, ajcc_bullets = get_ajcc_stage_explanation(ajcc_stage)
    if short_label:
        with st.expander("Prognostic context (population-level, not individualized)", expanded=False):
            st.markdown(f"**{short_label}**")
            for b in ajcc_bullets:
                st.markdown(f"- {b}")

    # ---------- Pathologic summary (if RP data) ----------
    if stage_context.startswith("Pathologic") or rp_margin != DEFAULT_MARGIN:
        st.subheader("Pathologic summary (post–radical prostatectomy)")
        st.markdown(f"- **pT:** {pt_stage_ss} – {PT_STAGE_DEFINITIONS[pt_stage_ss]}")
        st.markdown(f"- **pN:** {pn_stage_ss} – {PN_STAGE_DEFINITIONS[pn_stage_ss]}")
        st.markdown(f"- **Margin status:** {rp_margin}")
        st.caption(
            "Pathologic T and N are determined on the radical prostatectomy specimen. "
            "Biopsy findings (including EPE/PNI) are important but **do not replace** the prostatectomy specimen "
            "for assigning AJCC pT/pN. Positive surgical margins increase the risk of biochemical recurrence "
            "but do not alter the AJCC T or N category."
        )

    # ---------- Biopsy adverse features (EPE / PNI – GG ≥3 emphasis) ----------
    if has_biopsy_details and (any_epe_high_gg or any_pni_high_gg):
        with st.expander("Biopsy adverse features (EPE / PNI)", expanded=False):
            if any_epe_high_gg:
                st.markdown("**Extraprostatic extension (EPE) on high-grade biopsy cores**")
                st.markdown(
                    f"- EPE was identified in at least one core with Grade Group ≥3 (total EPE-positive cores: {epe_count_any}).\n"
                    "- This finding is strongly associated with pT3 disease and higher risk of adverse pathology.\n"
                    "- By AJCC definition, however, pT is formally assigned using the **radical prostatectomy specimen**, not biopsy alone."
                )
            if any_pni_high_gg:
                st.markdown("**Perineural invasion (PNI) on high-grade biopsy cores**")
                st.markdown(
                    f"- PNI was identified in at least one core with Grade Group ≥3 (total PNI-positive cores: {pni_count_any}).\n"
                    "- PNI is associated with higher-grade disease and a higher likelihood of extraprostatic extension and recurrence.\n"
                    "- PNI does **not** by itself change the TNM T category and should be interpreted in the context of other risk factors."
                )

    # ---------- Disease category & treatment options ----------
    disease_category = classify_disease_category(
        n_stage=n_for_stage,
        m_stage=m_for_stage,
    )
    treat_title, treat_sections = get_treatment_options(
        disease_category=disease_category,
        risk_group=None,  # filled later if NCCN clinical risk is available
        subcategory=None,
    )

    # ---------- Biopsy Summary (if any biopsy data) ----------
    if has_biopsy_details:
        st.subheader("Biopsy Summary")
        if stage_context.startswith("Pathologic"):
            st.caption(
                "Pre-operative biopsy summary for historical context (upgrade/downgrade, volume, adverse features). "
                "This does not change the AJCC pathologic stage."
            )

        if all_cancer_cores:
            st.markdown(
                f"- Systematic cores with cancer: **{positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
                f"({percent_sys_pos:.1f}%)**.\n"
                f"- Targeted cores with cancer: **{positive_targeted}/{len(TARGETED_SITES)}**."
            )
            st.markdown(
                f"- Highest Grade Group across all cores: **GG {highest_gg}**, example "
                f"{example_core['code']} {example_core['label']} "
                f"Gleason {example_core['primary']}+{example_core['secondary']}="
                f"{example_core['gleason_score']}."
            )
            if high_volume_core:
                st.markdown("- At least one core has **≥50% involvement** (high-volume core).")
            if high_grade_cores_gg4_5 > 0:
                st.markdown(f"- Number of cores with **Grade Group 4–5**: {high_grade_cores_gg4_5}.")
            if asap_count > 0:
                st.markdown(f"- ASAP present in {asap_count} core(s).")
            if any_epe_any:
                st.markdown(f"- **EPE** identified in {epe_count_any} cancer core(s).")
            if any_pni_any:
                st.markdown(f"- **PNI** identified in {pni_count_any} cancer core(s).")

            st.write("**Cancer cores (per-core detail)**")
            for c in all_cancer_cores:
                origin = "Systematic" if c["systematic"] else "Targeted"
                extra = ""
                if not c["systematic"] and c.get("desc_txt"):
                    extra = f" ({c['desc_txt']})"
                flags = []
                if c.get("epe"):
                    flags.append("EPE")
                if c.get("pni"):
                    flags.append("PNI")
                flag_txt = f" [{' / '.join(flags)}]" if flags else ""
                st.markdown(
                    f"- **{origin} {c['code']} – {c['label']}{extra}{flag_txt}**: Gleason "
                    f"{c['primary']}+{c['secondary']}={c['gleason_score']} "
                    f"(Grade Group {c['grade_group']}), ~{c['percent']:.0f}% of core."
                )

        else:
            st.warning(
                "No cores with confirmed adenocarcinoma were entered. "
                "If a biopsy has not yet been done or was benign, AJCC staging relies on "
                "clinical TNM and (when available) an overall Grade Group."
            )

    # ---------- NCCN Risk Group (only for clinical + biopsy data) ----------
    can_compute_nccn = (
        stage_context.startswith("Clinical")
        and has_biopsy_details
        and all_cancer_cores
        and grade_for_stage is not None
    )

    risk_group = None
    subcategory = None

    if can_compute_nccn:
        risk_group, subcategory, risk_info = classify_nccn_risk(
            t_stage=ct_stage_ss,
            n_stage=cn_stage_ss,
            m_stage=cm_stage_ss,
            grade_group=int(grade_for_stage),
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

        # Additional evaluation
        add_title, add_items = get_additional_evaluation_recommendations(risk_group, subcategory)
        if add_title:
            st.subheader("Suggested Additional Evaluation (NCCN-style, simplified)")
            st.info(add_title)
            for item in add_items:
                st.markdown(f"- {item}")

        # Treatment options now can use risk group
        treat_title, treat_sections = get_treatment_options(
            disease_category=disease_category,
            risk_group=risk_group,
            subcategory=subcategory,
        )

    else:
        st.subheader("NCCN Risk Group")
        # Different explanation depending on why NCCN was not calculated
        if not stage_context.startswith("Clinical"):
            # Pathologic staging mode
            if has_biopsy_details and all_cancer_cores:
                st.info(
                    "You entered biopsy data, but NCCN **initial** risk groups are defined using "
                    "**clinical TNM (cTNM)**. Because the staging basis above is set to "
                    "**pathologic staging (pTNM)**, the app does not calculate an NCCN risk group "
                    "in this mode.\n\n"
                    "If you want to see the NCCN risk group, change the staging basis at the top "
                    "to **Clinical staging (cTNM)** and run the calculation again."
                )
            else:
                st.info(
                    "NCCN initial risk groups are defined using **clinical TNM and biopsy findings**. "
                    "Because the staging basis above is **pathologic staging (pTNM)**, NCCN risk is "
                    "not calculated in this mode. Switch to **Clinical staging (cTNM)** to view NCCN risk."
                )
        else:
            # Clinical staging basis, but something else is missing
            msg_parts = [
                "NCCN initial risk groups are defined using **clinical TNM and biopsy findings**."
            ]
            if not has_biopsy_details or not all_cancer_cores:
                msg_parts.append(
                    "In the current inputs, there are no cancerous biopsy cores entered, "
                    "so a formal NCCN risk group is not calculated."
                )
            if grade_for_stage is None:
                msg_parts.append(
                    "A Grade Group is also required; please enter an overall Grade Group "
                    "if detailed biopsy data are not available."
                )
            st.info(" ".join(msg_parts))

    # ---------- Treatment options (educational summary) ----------
    if treat_title:
        st.subheader("Treatment Options (educational summary – verify with current guidelines)")
        st.info(treat_title)
        for sec_title, bullets in treat_sections:
            st.markdown(f"**{sec_title}**")
            for b in bullets:
                st.markdown(f"- {b}")
            st.markdown("")

    # ---------- External tools ----------
    with st.expander("External prognosis tools and patient guidelines", expanded=False):
        st.write(
            "These links open external tools based on large population datasets. "
            "Use them for shared decision-making, not as a substitute for clinical judgment. "
            "Do not enter patient identifiers."
        )
        link_button_or_markdown(
            "Open PREDICT Prostate (survival & treatment benefit)",
            "https://prostate.predict.cam/",
        )
        link_button_or_markdown(
            "Open MSKCC prostate cancer nomograms",
            "https://www.mskcc.org/nomograms/prostate",
        )
        link_button_or_markdown(
            "Open NCCN patient guidelines for prostate cancer",
            "https://www.nccn.org/patientresources/patient-resources/guidelines-for-patients",
        )

    # ---------- Compact summary ----------
    st.subheader("Compact Summary (copy into note)")

    if all_cancer_cores and has_biopsy_details:
        risk_text = "NCCN risk not calculated"
        if risk_group:
            risk_text = risk_group
            if subcategory:
                risk_text += f" ({subcategory} intermediate)"

        summary_line = (
            f"{t_for_stage} {n_for_stage} {m_for_stage}, PSA {psa:.1f} ng/mL, "
            f"Grade Group {grade_for_stage if grade_for_stage is not None else 'unknown'}; "
            f"AJCC {ajcc_stage}, NCCN {risk_text}; "
            f"systematic cancer cores {positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
            f"({percent_sys_pos:.1f}%), targeted cancer cores {positive_targeted}/{len(TARGETED_SITES)}."
        )
    else:
        summary_line = (
            f"{t_for_stage} {n_for_stage} {m_for_stage}, PSA {psa:.1f} ng/mL, "
            f"Grade Group {grade_for_stage if grade_for_stage is not None else 'unknown'}; "
            f"AJCC {ajcc_stage}. "
            "Detailed biopsy-based summary not available."
        )

    st.text_area("Summary", value=summary_line, height=80)

    # ---------- Full text report ----------
    lines: list[str] = []
    lines.append(f"{APP_NAME} – Prostate cancer staging summary")
    lines.append("")
    lines.append(f"Staging basis: {stage_context}")
    lines.append(f"TNM used: {t_for_stage}, {n_for_stage}, {m_for_stage}")
    lines.append(f"PSA: {psa:.1f} ng/mL")
    lines.append(
        f"Grade Group used for staging: {grade_for_stage if grade_for_stage is not None else 'unknown'}"
    )
    if stage_context.startswith("Pathologic") or rp_margin != DEFAULT_MARGIN:
        lines.append(
            f"Pathologic summary (post-RP): {pt_stage_ss}, {pn_stage_ss}; margin status: {rp_margin}."
        )
    lines.append("")
    lines.append(f"AJCC 8th prognostic stage group: {ajcc_stage}")
    for l in ajcc_info:
        lines.append(f"- {l}")
    lines.append("")

    if has_biopsy_details:
        lines.append("Biopsy summary:")
        if all_cancer_cores:
            lines.append(
                f"- Systematic cores with cancer: {positive_systematic}/{TOTAL_SYSTEMATIC_CORES} "
                f"({percent_sys_pos:.1f}%)"
            )
            lines.append(
                f"- Targeted cores with cancer: {positive_targeted}/{len(TARGETED_SITES)}"
            )
            if high_volume_core:
                lines.append("- At least one core has ≥50% involvement.")
            if high_grade_cores_gg4_5 > 0:
                lines.append(f"- Cores with Grade Group 4–5: {high_grade_cores_gg4_5}")
            if asap_count > 0:
                lines.append(f"- ASAP present in {asap_count} core(s).")
            if any_epe_any:
                lines.append(f"- EPE identified in {epe_count_any} cancer core(s).")
            if any_pni_any:
                lines.append(f"- PNI identified in {pni_count_any} cancer core(s).")
            if any_epe_high_gg or any_pni_high_gg:
                lines.append(
                    "- Note: At least one high-grade core (Grade Group ≥3) shows EPE and/or PNI."
                )
            lines.append("")
            lines.append("Per-core cancer details:")
            for c in all_cancer_cores:
                origin = "Systematic" if c["systematic"] else "Targeted"
                extra = ""
                if not c["systematic"] and c.get("desc_txt"):
                    extra = f" ({c['desc_txt']})"
                flags = []
                if c.get("epe"):
                    flags.append("EPE")
                if c.get("pni"):
                    flags.append("PNI")
                flag_txt = f" [{' / '.join(flags)}]" if flags else ""
                lines.append(
                    f"- {origin} {c['code']} – {c['label']}{extra}{flag_txt}: "
                    f"Gleason {c['primary']}+{c['secondary']}={c['gleason_score']} "
                    f"(Grade Group {c['grade_group']}), approx. {c['percent']}% of core."
                )
        else:
            lines.append("- No detailed cancer cores entered.")
        lines.append("")

    if risk_group:
        risk_text = risk_group
        if subcategory:
            risk_text += f" ({subcategory} intermediate)"
        lines.append(f"NCCN risk group (clinical setting): {risk_text}")
        for l in risk_info:
            lines.append(f"- {l}")
        lines.append("")

    if treat_title and treat_sections:
        lines.append("Treatment options (educational summary):")
        lines.append(f"- {treat_title}")
        for sec_title, bullets in treat_sections:
            lines.append(f"  • {sec_title}")
            for b in bullets:
                lines.append(f"    - {b}")
        lines.append("")

    report_text = "\n".join(lines)

    st.download_button(
        "Download full report as .txt",
        data=report_text,
        file_name="prostate_cancer_staging_report.txt",
        mime="text/plain",
    )

# ============================================================
# Reset button
# ============================================================

st.markdown("---")

def reset_form():
    """
    Clear relevant keys from Session State so that widgets fall back
    to their own default `value`/`index` arguments on the next run.
    """
    top_level_keys = [
        "stage_context", "ct_stage", "cn_stage", "cm_stage",
        "pt_stage", "pn_stage", "rp_margin", "psa",
        "manual_gg", "has_biopsy_details",
    ]
    for k in top_level_keys:
        if k in st.session_state:
            del st.session_state[k]

    # Systematic cores
    for code, _ in CORE_SITES:
        for suffix in ["type", "p", "s", "pct", "epe", "pni"]:
            key = f"{code}_{suffix}"
            if key in st.session_state:
                del st.session_state[key]

    # Targeted cores
    for code, _ in TARGETED_SITES:
        for suffix in ["type", "p", "s", "pct", "epe", "pni", "desc"]:
            key = f"{code}_{suffix}"
            if key in st.session_state:
                del st.session_state[key]

st.button("Reset form for next patient", on_click=reset_form)

# ============================================================
# Footer
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

