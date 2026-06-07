import argparse
import asyncio
import os
import json
from datetime import datetime, timezone
from backend.app.database import SessionLocal
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.pipeline import InvestigationPipeline
from backend.app.events.store import EventStore
from backend.app.providers.llm import FallbackLLMRouter, MockLLMProvider, AnthropicProvider, GeminiProvider, OpenAIProvider
from backend.app.config.settings import settings
from pydantic import BaseModel, Field

class RCANarrative(BaseModel):
    summary: str = Field(..., description="High-level summary of the incident and root cause")
    steps: list[str] = Field(..., description="Step-by-step chronological propagation sequence of the failure")
    recommendations: list[str] = Field(..., description="Actionable recommendations to prevent recurrence")

def get_llm_provider():
    if settings.API_ENV == "development":
        preset = RCANarrative(
            summary="Incident analysis: CPU spike on auth-service causing Redis connection pool exhaustion.",
            steps=[
                "1. CPU utilization on auth-service reached 95%.",
                "2. Connection limits to Redis exceeded pool capacity.",
                "3. K8s readiness probe failed for Pod auth-service-xyz."
            ],
            recommendations=["Increase Redis pool size.", "Set CPU resource limits."]
        )
        return MockLLMProvider(preset_responses={"RCANarrative": preset})
        
    providers = {
        "anthropic": AnthropicProvider(),
        "gemini": GeminiProvider(),
        "openai": OpenAIProvider()
    }
    return FallbackLLMRouter(providers, settings.LLM_FALLBACK_CHAIN)

async def run_investigate(investigation_id: str):
    db = SessionLocal()
    try:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            inv = Investigation(id=investigation_id, status=InvestigationStatus.QUEUED)
            db.add(inv)
            db.commit()
            print(f"Created new investigation: {investigation_id}")
            
        print(f"Running OpenSRE investigation pipeline for {investigation_id}...")
        pipeline = InvestigationPipeline(db)
        await pipeline.execute(investigation_id)
        
        store = EventStore()
        hypotheses_path = os.path.join(store.base_dir, investigation_id, "hypotheses.json")
        if os.path.exists(hypotheses_path):
            with open(hypotheses_path, "r") as f:
                hypotheses = json.load(f)
            print("\nTop Root Cause Candidates:")
            for idx, hyp in enumerate(hypotheses[:3]):
                print(f"  #{idx+1} Confidence: {hyp['confidence_score'] * 100:.1f}% | Keys: {', '.join(hyp['keys'])}")
                print(f"     Explanation: {hyp['explanation']}")
                print(f"     Evidence Snippets:")
                for snippet in hyp['evidence']:
                    print(f"       - {snippet}")
        else:
            print("No hypotheses generated.")
    finally:
        db.close()

async def run_explain(investigation_id: str):
    store = EventStore()
    report_path = os.path.join(store.base_dir, investigation_id, "report.json")
    if not os.path.exists(report_path):
        print(f"No report found for {investigation_id}. Please run investigate command first.")
        return

    with open(report_path, "r") as f:
        report_data = json.load(f)

    prompt = f"""
    Analyze the following incident report and explain the root cause and failure sequence.
    Incident Report Data:
    {json.dumps(report_data, indent=2)}
    """
    
    print(f"Generating root cause narrative for {investigation_id}...")
    llm = get_llm_provider()
    try:
        narrative = await llm.generate_structured(prompt, RCANarrative)
        print("\n=== Root Cause Explanation Narrative ===")
        print(f"Summary:\n{narrative.summary}\n")
        print("Chronological Propagation Steps:")
        for step in narrative.steps:
            print(f"  {step}")
        print("\nActionable Recommendations:")
        for rec in narrative.recommendations:
            print(f"  - {rec}")
    except Exception as e:
        print(f"Failed to generate narrative explanation: {e}")

def main():
    parser = argparse.ArgumentParser(description="OpenSRE Incident Investigation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inv_parser = subparsers.add_parser("investigate", help="Execute incident investigation pipeline")
    inv_parser.add_argument("investigation_id", type=str, help="Investigation identifier")

    exp_parser = subparsers.add_parser("explain", help="Generate explanation narrative using LLM router")
    exp_parser.add_argument("investigation_id", type=str, help="Investigation identifier")

    args = parser.parse_args()

    if args.command == "investigate":
        asyncio.run(run_investigate(args.investigation_id))
    elif args.command == "explain":
        asyncio.run(run_explain(args.investigation_id))

if __name__ == "__main__":
    main()
