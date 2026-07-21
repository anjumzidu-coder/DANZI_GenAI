from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Dict, List

import pandas as pd
from openai import OpenAI


@dataclass
class RequirementCandidate:
    category: str
    priority: str
    requirement: str
    rationale: str
    evidence: str
    source_sheet: str
    source_row: int
    review_status: str = "Draft"


_CATEGORY_TEMPLATES = {
    "product information": (
        "High",
        "Provide complete product identification, service naming, lifecycle context, and release metadata before service readiness sign-off.",
        "Service teams need a stable product identity baseline to create accurate support content, entitlements, and downstream readiness plans.",
    ),
    "services spares": (
        "High",
        "Define service spare parts scope, stocking model, replacement rules, and field logistics ownership before launch.",
        "Spares readiness directly affects break-fix execution, field repair speed, and customer downtime exposure.",
    ),
    "volume forecast": (
        "High",
        "Publish a support volume forecast covering install base, expected case volumes, and capacity assumptions for the initial support horizon.",
        "Forecast data is needed to plan staffing, parts, tooling, and service operations capacity.",
    ),
    "support documentation": (
        "High",
        "Deliver support documentation with issue isolation steps, service procedures, escalation paths, and revision ownership.",
        "Support teams require trusted documentation to handle incidents consistently and reduce dependence on tribal knowledge.",
    ),
    "support automation": (
        "Medium",
        "Identify support automation opportunities, required telemetry inputs, and the process for deploying automated support workflows.",
        "Automation improves response speed, consistency, and scale for recurring support scenarios.",
    ),
    "connectivity, remote access": (
        "High",
        "Document remote connectivity methods, access prerequisites, security controls, and approved support access workflows.",
        "Remote access readiness is critical for proactive support, diagnostics, and secure issue resolution.",
    ),
    "product discovery & classification": (
        "Medium",
        "Establish how the product is discovered, classified, and represented across service management and support systems.",
        "Consistent classification is needed for entitlement, routing, analytics, and downstream automation.",
    ),
    "product alerts": (
        "Medium",
        "Define alert sources, thresholds, alert ownership, and the response model for support-relevant product events.",
        "Alert readiness enables earlier detection of support issues and better proactive case handling.",
    ),
    "service level entitlement": (
        "High",
        "Map supported service levels, entitlement rules, exclusions, and service delivery boundaries for the product.",
        "Clear entitlements prevent support ambiguity and ensure the delivery model matches sold services.",
    ),
    "product & solution identification": (
        "High",
        "Maintain a consistent product and solution identification model across documentation, tools, and service records.",
        "Accurate identification improves support routing, entitlement checks, and solution-level service readiness.",
    ),
    "technical product documentation": (
        "High",
        "Provide technical documentation for architecture, dependencies, service procedures, troubleshooting, and known limitations.",
        "Technical documentation is foundational for repeatable support and knowledge transfer.",
    ),
    "knowledge transfer for services": (
        "Medium",
        "Run a formal knowledge transfer plan for service teams, with named owners, training evidence, and completion checkpoints.",
        "Institutionalizing product knowledge reduces ramp-up time and support variability.",
    ),
    "iur hardware available": (
        "Medium",
        "Confirm internal-use or lab hardware availability for validation, training, and service readiness testing.",
        "Hands-on validation environments improve readiness confidence and enable pre-launch issue discovery.",
    ),
    "install training content": (
        "Medium",
        "Prepare installation training content with prerequisites, standard procedures, and common failure scenarios.",
        "Install quality affects early customer experience and downstream support demand.",
    ),
    "compatibility matrix": (
        "High",
        "Publish a compatibility matrix covering supported hardware, software, firmware, and integration dependencies.",
        "Compatibility clarity reduces deployment risk and support escalations caused by unsupported combinations.",
    ),
    "firmware/software version updates": (
        "High",
        "Define the update policy for firmware and software versions, including cadence, validation, rollback, and communication steps.",
        "Version governance is essential for supportability, consistency, and customer risk reduction.",
    ),
    "sw/fw, tools, lifecycle management": (
        "High",
        "Document the tools, software, firmware, and lifecycle management controls required for support execution.",
        "Lifecycle management ensures service teams can support the product across release changes and support milestones.",
    ),
    "solution sizing tools": (
        "Medium",
        "Provide solution sizing guidance and approved tools for service planning, deployment, and support estimation.",
        "Sizing accuracy reduces delivery risk and improves resource planning quality.",
    ),
    "integrated solutions lifecycle mgmt": (
        "Medium",
        "Define lifecycle management responsibilities and dependencies for integrated solutions and bundled components.",
        "Integrated offerings need clear ownership and lifecycle alignment across all components.",
    ),
    "bu product support through lifecycle": (
        "High",
        "Assign lifecycle support ownership for the business unit, including transition points, sustainment, and end-of-support planning.",
        "Long-term support accountability is required for continuity, escalation handling, and customer confidence.",
    ),
    "service advisories post launch": (
        "Medium",
        "Establish the post-launch advisory process, including trigger criteria, authorship, approval, and communication channels.",
        "Advisories are a critical control for communicating service-impacting issues after launch.",
    ),
}


_GENERIC_OBJECTIVE_TEMPLATES = [
    (
        "Requirement Traceability",
        "High",
        "Each generated S&S requirement must include source evidence, rationale, and a traceable link to the originating product or customer input.",
        "The project objective explicitly calls for recommended and traceable requirements.",
    ),
    (
        "Product-Specific Requirement Generation",
        "High",
        "The tool must generate product-specific S&S requirements rather than reusing generic templates without adaptation.",
        "The objective emphasizes product-specific requirement generation and reduced reliance on generic requirements.",
    ),
    (
        "Institutional Knowledge Reuse",
        "Medium",
        "Lessons learned, prior maturity assessments, and historical service issues should be reusable inputs for requirement generation.",
        "The project objective highlights reuse of institutional knowledge as a key outcome.",
    ),
    (
        "Human Review Workflow",
        "High",
        "Generated requirements must support user review, approval, and refinement before downstream use.",
        "The project risks and assumptions indicate human review is required for quality and governance.",
    ),
]


def _clean_label(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value or "").strip()
    if not text or text.lower().startswith("unnamed"):
        return ""
    return text.replace("\u2212", "-").replace("?", "").strip("- ")


def _extract_categories_from_product_sheet(df: pd.DataFrame) -> List[RequirementCandidate]:
    candidates: List[RequirementCandidate] = []
    if df.empty:
        return candidates

    first_col = df.iloc[:, 0].tolist()
    status_col = df.iloc[:, 4].tolist() if df.shape[1] > 4 else [""] * len(df)

    for idx, raw_label in enumerate(first_col):
        label = _clean_label(raw_label)
        if not label:
            continue

        lower = label.lower()
        if lower in {"project", "product 1", "bu overall assessment", "general requirements", "support detail", "technical training", "post-mfg support"}:
            continue

        matched_key = next((key for key in _CATEGORY_TEMPLATES if key in lower), None)
        if not matched_key:
            continue

        priority, requirement, rationale = _CATEGORY_TEMPLATES[matched_key]
        status_hint = _clean_label(status_col[idx])
        evidence = f"Row {idx + 1} in Product 1 contains category '{label}'"
        if status_hint:
            evidence += f" with current status hint '{status_hint}'"

        candidates.append(
            RequirementCandidate(
                category=label,
                priority=priority,
                requirement=requirement,
                rationale=rationale,
                evidence=evidence,
                source_sheet="Product 1",
                source_row=idx + 1,
            )
        )

    return candidates


def _extract_objective_requirements(sheets: Dict[str, pd.DataFrame]) -> List[RequirementCandidate]:
    candidates: List[RequirementCandidate] = []
    for sheet_name, df in sheets.items():
        if df.empty:
            continue

        text_blob = " ".join(
            str(value)
            for value in df.fillna("").astype(str).to_numpy().flatten().tolist()
            if str(value).strip()
        ).lower()

        if "serviceability" in text_blob and "supportability" in text_blob:
            for category, priority, requirement, rationale in _GENERIC_OBJECTIVE_TEMPLATES:
                candidates.append(
                    RequirementCandidate(
                        category=category,
                        priority=priority,
                        requirement=requirement,
                        rationale=rationale,
                        evidence=f"Derived from document text in sheet '{sheet_name}' referencing serviceability/supportability objectives.",
                        source_sheet=sheet_name,
                        source_row=1,
                    )
                )
            break
    return candidates


def generate_requirement_candidates(sheets: Dict[str, pd.DataFrame]) -> List[Dict[str, object]]:
    candidates = []

    if "Product 1" in sheets:
        candidates.extend(_extract_categories_from_product_sheet(sheets["Product 1"]))

    if not candidates:
        candidates.extend(_extract_objective_requirements(sheets))

    seen = set()
    unique: List[RequirementCandidate] = []
    for item in candidates:
        key = (item.category, item.requirement)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return [asdict(item) for item in unique]


def refine_requirements_with_ai(requirements: List[Dict[str, object]], workbook_summary: List[Dict[str, object]]) -> List[Dict[str, object]]:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    if provider != "openai" or not api_key or not requirements:
        return requirements

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are refining draft Serviceability and Supportability requirements. "
        "Keep them structured, concise, and product-specific. "
        "Return JSON list with the same fields as input.\n\n"
        f"Workbook summary: {workbook_summary}\n\n"
        f"Draft requirements: {requirements}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Refine S&S requirements without inventing unsupported evidence."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    try:
        import json

        parsed = json.loads(content)
        refined = parsed.get("requirements")
        if isinstance(refined, list) and refined:
            return refined
    except Exception:
        return requirements

    return requirements
