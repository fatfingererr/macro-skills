"""
Google Trend ATH Detector - Hypothesis Builder

Generates testable hypotheses based on signal type and driver terms,
and maps each hypothesis to verification data sources.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Hypothesis:
    """Testable hypothesis structure"""
    id: str
    hypothesis: str
    trigger_terms: List[str]
    evidence_in_trends: List[str]
    verify_with: List[str]
    confidence: str = "medium"


# Hypothesis templates by topic category
HYPOTHESIS_TEMPLATES = {
    "health_insurance": [
        Hypothesis(
            id="H1",
            hypothesis="保費/自付額壓力上升造成注意力結構性抬升",
            trigger_terms=["premium", "premium increase", "deductible", "cost",
                          "expensive", "rate hike", "price"],
            evidence_in_trends=["premium/cost 類詞在 rising queries", "去季節化殘差偏高"],
            verify_with=[
                "FRED: CUSR0000SAM (Medical Care CPI)",
                "FRED: CUSR0000SAM2 (Health Insurance CPI)",
                "州級保費公告 (rate filings)",
                "KFF Health Insurance Marketplace Calculator"
            ]
        ),
        Hypothesis(
            id="H2",
            hypothesis="就業/雇主保險變動導致搜尋上升",
            trigger_terms=["COBRA", "lose coverage", "lost job", "layoff",
                          "unemployment", "job loss", "employer"],
            evidence_in_trends=["就業相關詞在 rising queries", "與 Unemployment 搜尋共振"],
            verify_with=[
                "FRED: ICSA (Initial Claims)",
                "FRED: PAYEMS (Nonfarm Payrolls)",
                "BLS: Layoffs and Discharges",
                "FRED: LNU02026620 (Job losers)"
            ]
        ),
        Hypothesis(
            id="H3",
            hypothesis="政策/資格變動（Medicaid/ACA）引發搜尋",
            trigger_terms=["Medicaid", "Medicaid renewal", "eligibility", "ACA",
                          "Obamacare", "marketplace", "subsidy", "qualify"],
            evidence_in_trends=["政策相關詞上升", "與政策公告時間對齊"],
            verify_with=[
                "CMS Medicaid enrollment data",
                "Healthcare.gov 公告",
                "州級 Medicaid eligibility 變更時間表"
            ]
        ),
        Hypothesis(
            id="H4",
            hypothesis="開放投保期季節性造成週期性尖峰",
            trigger_terms=["open enrollment", "sign up", "deadline", "enroll",
                          "enrollment period"],
            evidence_in_trends=["每年固定月份上升（11-12月）", "去季節化後殘差不顯著"],
            verify_with=[
                "Open Enrollment 官方日期",
                "比較過去 5 年同週期分位數"
            ]
        )
    ],

    "economic_general": [
        Hypothesis(
            id="E1",
            hypothesis="通膨壓力導致生活成本焦慮上升",
            trigger_terms=["inflation", "cost of living", "prices", "expensive",
                          "afford", "rising prices"],
            evidence_in_trends=["inflation/cost 類詞上升"],
            verify_with=[
                "FRED: CPIAUCSL (CPI All Items)",
                "FRED: PCEPILFE (Core PCE)",
                "FRED: UMCSENT (Consumer Sentiment)"
            ]
        ),
        Hypothesis(
            id="E2",
            hypothesis="就業市場變動引發經濟不安",
            trigger_terms=["layoff", "unemployment", "job search", "hiring freeze",
                          "recession", "fired", "laid off"],
            evidence_in_trends=["就業相關詞上升"],
            verify_with=[
                "FRED: UNRATE (Unemployment Rate)",
                "FRED: ICSA (Initial Claims)",
                "FRED: JTSJOL (Job Openings)"
            ]
        ),
        Hypothesis(
            id="E3",
            hypothesis="利率上升影響財務決策搜尋",
            trigger_terms=["interest rate", "mortgage", "refinance", "loan",
                          "Fed", "rate hike"],
            evidence_in_trends=["利率相關詞上升"],
            verify_with=[
                "FRED: FEDFUNDS (Federal Funds Rate)",
                "FRED: MORTGAGE30US (30-Year Mortgage Rate)"
            ]
        )
    ]
}


def get_topic_category(topic: str) -> str:
    """
    Determine topic category for hypothesis template selection.
    """
    topic_lower = topic.lower()

    if any(term in topic_lower for term in ["health", "insurance", "medical",
                                             "medicare", "medicaid"]):
        return "health_insurance"

    return "economic_general"


def calculate_match_score(
    drivers: List[Dict],
    trigger_terms: List[str]
) -> float:
    """
    Calculate how well drivers match a hypothesis's trigger terms.
    """
    if not drivers or not trigger_terms:
        return 0.0

    trigger_lower = [t.lower() for t in trigger_terms]
    matches = 0

    for driver in drivers:
        term = driver.get('term', '').lower()
        for trigger in trigger_lower:
            if trigger in term or term in trigger:
                matches += 1
                break

    return matches / len(trigger_terms)


def find_evidence(
    drivers: List[Dict],
    hypothesis: Hypothesis
) -> List[str]:
    """
    Find evidence in drivers that supports a hypothesis.
    """
    evidence = []
    trigger_lower = [t.lower() for t in hypothesis.trigger_terms]

    for driver in drivers:
        term = driver.get('term', '').lower()
        driver_type = driver.get('type', '')

        for trigger in trigger_lower:
            if trigger in term or term in trigger:
                evidence.append(
                    f"'{driver['term']}' 在 {driver_type} queries 中出現"
                )
                break

    return evidence


def calculate_confidence(
    match_score: float,
    evidence_count: int,
    signal_type: str
) -> str:
    """
    Calculate confidence level for a hypothesis.
    """
    score = match_score * 0.4 + min(evidence_count * 0.15, 0.4)

    # Adjust by signal type
    if signal_type == "regime_shift":
        score += 0.1
    elif signal_type == "seasonal_spike":
        score -= 0.1

    if score >= 0.6:
        return "high"
    elif score >= 0.35:
        return "medium"
    else:
        return "low"


def build_testable_hypotheses(
    topic: str,
    drivers: List[Dict],
    signal_type: str,
    max_hypotheses: int = 4
) -> List[Dict]:
    """
    Build testable hypotheses based on topic, drivers, and signal type.

    Args:
        topic: The analyzed topic
        drivers: List of driver terms from related queries
        signal_type: Classified signal type
        max_hypotheses: Maximum number of hypotheses to return

    Returns:
        List of hypothesis dicts
    """
    category = get_topic_category(topic)
    templates = HYPOTHESIS_TEMPLATES.get(category, [])

    # Also include general economic hypotheses if not already included
    if category != "economic_general":
        templates = templates + HYPOTHESIS_TEMPLATES.get("economic_general", [])

    hypotheses = []

    for template in templates:
        match_score = calculate_match_score(drivers, template.trigger_terms)

        if match_score > 0.1:  # At least some match
            evidence = find_evidence(drivers, template)
            confidence = calculate_confidence(match_score, len(evidence), signal_type)

            hypotheses.append({
                'id': template.id,
                'hypothesis': template.hypothesis,
                'match_score': round(match_score, 2),
                'evidence_in_trends': evidence if evidence else template.evidence_in_trends,
                'verify_with': template.verify_with,
                'confidence': confidence
            })

    # Sort by match score and confidence
    confidence_order = {'high': 3, 'medium': 2, 'low': 1}
    hypotheses.sort(
        key=lambda x: (confidence_order.get(x['confidence'], 0), x['match_score']),
        reverse=True
    )

    return hypotheses[:max_hypotheses]


def propose_next_data(hypotheses: List[Dict]) -> List[str]:
    """
    Collect unique verification data sources from hypotheses.
    """
    data_sources = []
    seen = set()

    for h in hypotheses:
        for source in h.get('verify_with', []):
            if source not in seen:
                data_sources.append(source)
                seen.add(source)

    return data_sources[:10]  # Limit to 10


def generate_verification_checklist(
    hypotheses: List[Dict],
    signal_type: str
) -> Dict[str, List[Dict]]:
    """
    Generate prioritized verification checklist.
    """
    checklist = {
        'immediate': [],
        'short_term': [],
        'ongoing': []
    }

    for h in hypotheses:
        priority = "high" if h['confidence'] == "high" else "medium"

        for i, source in enumerate(h.get('verify_with', [])[:2]):
            task = {
                'task': f"檢查 {source}",
                'hypothesis_id': h['id'],
                'priority': priority if i == 0 else "medium"
            }

            if i == 0:
                checklist['immediate'].append(task)
            else:
                checklist['short_term'].append(task)

    # Add ongoing monitoring based on signal type
    if signal_type == "regime_shift":
        checklist['ongoing'].append({
            'task': "每週追蹤趨勢是否持續上升",
            'priority': "medium",
            'frequency': "weekly"
        })
    elif signal_type == "event_driven_shock":
        checklist['ongoing'].append({
            'task': "監控相關新聞事件發展",
            'priority': "medium",
            'frequency': "daily"
        })

    return checklist


def build_complete_hypothesis_report(
    topic: str,
    geo: str,
    signal_type: str,
    drivers: List[Dict],
    is_ath: bool,
    zscore: float,
    seasonal_strength: float
) -> Dict[str, Any]:
    """
    Build complete hypothesis report.
    """
    # Generate hypotheses
    hypotheses = build_testable_hypotheses(topic, drivers, signal_type)

    # Generate checklist
    checklist = generate_verification_checklist(hypotheses, signal_type)

    # Collect data sources
    next_data = propose_next_data(hypotheses)

    # Build report
    report = {
        'topic': topic,
        'geo': geo,
        'signal_summary': {
            'signal_type': signal_type,
            'is_all_time_high': is_ath,
            'anomaly_score': zscore,
            'seasonal_strength': seasonal_strength
        },
        'testable_hypotheses': hypotheses,
        'verification_checklist': checklist,
        'next_data_to_pull': next_data,
        'primary_hypothesis': hypotheses[0]['id'] if hypotheses else None,
        'overall_confidence': hypotheses[0]['confidence'] if hypotheses else "low"
    }

    return report


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build testable hypotheses from Google Trends analysis"
    )
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--geo", type=str, default="US")
    parser.add_argument("--signal-type", type=str, default="event_driven_shock",
                        choices=["seasonal_spike", "event_driven_shock",
                                 "regime_shift", "normal"])
    parser.add_argument("--drivers", type=str, default="",
                        help="Comma-separated driver terms")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    # Parse drivers
    drivers = []
    if args.drivers:
        for term in args.drivers.split(","):
            drivers.append({'term': term.strip(), 'type': 'rising', 'value': 'N/A'})

    # Build report
    report = build_complete_hypothesis_report(
        topic=args.topic,
        geo=args.geo,
        signal_type=args.signal_type,
        drivers=drivers,
        is_ath=True,
        zscore=2.5,
        seasonal_strength=0.4
    )

    output_json = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Report written to: {args.output}")
    else:
        print(output_json)
