"""Native CI integration evidence. Calls actual Ollama; never a response fixture."""
import json
import os
from pathlib import Path
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from reviewwise.config import MODEL
from reviewwise.pipeline import analyze_reviews, complaint_rows, reviews_from_text, make_reviews
from reviewwise.report import render_report

OUTPUT = ROOT / 'docs/verification'
OUTPUT.mkdir(parents=True, exist_ok=True)


def encode(result):
    return json.loads(json.dumps(asdict(result), default=lambda value: value.model_dump()))


def write_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def main():
    evidence = {
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'source_commit': os.environ.get('GITHUB_SHA', ''),
        'workflow_run': os.environ.get('GITHUB_RUN_ID', ''),
        'platform': platform.platform(), 'python': platform.python_version(),
        'model': MODEL, 'live_ai': False, 'live_ai_attempted': True,
        'input_provenance': 'Fictional evaluation sentences and the preserved fictional M2 sample; not customer data.',
        'passed': False,
    }
    path = OUTPUT / 'windows-ai.json'
    write_json(path, evidence)
    try:
        smoke = analyze_reviews(reviews_from_text('The coffee was cold and the service was slow.'))
        evidence['live_ai'] = smoke.ai_requests > 0
        evidence['smoke'] = encode(smoke)
        categories = {row['category'] for row in complaint_rows(smoke.analyses)}
        if not smoke.complete or not {'cold_coffee', 'slow_service'} <= categories:
            raise RuntimeError('The real smoke input did not produce both expected complaint categories.')
        texts = json.loads((ROOT / 'experiments/reviews.json').read_text(encoding='utf-8'))
        cache = {}
        result = analyze_reviews(make_reviews(texts), cache=cache,
                                 on_update=lambda item: write_json(path, {**evidence, 'sample': encode(item)}))
        evidence['sample'] = encode(result)
        evidence['counts'] = complaint_rows(result.analyses)
        if not result.complete:
            raise RuntimeError('The multilingual sample did not finish with validated coverage.')
        repeated = analyze_reviews(make_reviews(texts), cache=cache)
        evidence['repeat'] = encode(repeated)
        if not repeated.complete or repeated.reused_reviews != len(texts) or repeated.ai_requests != 0:
            raise RuntimeError('The real-model repeat did not reuse all matching validated results.')
        document = {
            'schema_version': 1, 'recorded_at': evidence['recorded_at'],
            'reporting_day': datetime.now(timezone.utc).date().isoformat(),
            'title': 'Recorded AI example — fictional multilingual café reviews',
            'provenance': 'Real Ollama execution in Windows CI on fictional M2 input; dates are demonstration metadata.',
            'model': MODEL, 'result': encode(result),
            'source_commit': evidence['source_commit'], 'workflow_run': evidence['workflow_run'],
        }
        write_json(OUTPUT / 'recorded-ai-report.json', document)
        (OUTPUT / 'recorded-ai-report.txt').write_text(render_report(result), encoding='utf-8')
        evidence['passed'] = True
        print(f'Real AI check passed: {len(result.analyses)} validated reviews, {result.ai_requests} requests, {result.elapsed_seconds:.2f}s; repeat {repeated.elapsed_seconds:.2f}s.')
    except Exception as error:
        evidence['error'] = str(error)
        raise
    finally:
        write_json(path, evidence)


if __name__ == '__main__':
    main()
