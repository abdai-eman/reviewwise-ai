"""One cancellable background analysis; workers never call Streamlit."""
from dataclasses import replace
from threading import Event, Lock, Thread

from reviewwise.pipeline import ReviewWiseError

_guard = Lock()
_active = None


class AnalysisJob:
    def __init__(self, reviews, cache):
        self.reviews = list(reviews)
        self._cache = dict(cache)
        self._cache_snapshot = dict(cache)
        self._lock = Lock()
        self._cancel = Event()
        self._done = Event()
        self._result = None
        self._error = None

    @property
    def running(self):
        return not self._done.is_set()

    def cancel(self):
        self._cancel.set()

    def snapshot(self):
        with self._lock:
            return self._result, self._error, dict(self._cache_snapshot), self.running, self._cancel.is_set()

    def _update(self, result):
        with self._lock:
            self._result = result
            self._cache_snapshot = dict(self._cache)

    def _run(self):
        global _active
        from reviewwise.pipeline import analyze_reviews
        try:
            result = analyze_reviews(self.reviews, cache=self._cache, on_update=self._update, should_stop=self._cancel.is_set)
            self._update(result)
        except Exception as error:
            with self._lock:
                self._error = error
                if self._result:
                    self._result = replace(self._result, running=False, stop_reason=str(error))
        finally:
            self._done.set()
            with _guard:
                if _active is self:
                    _active = None


def is_busy():
    with _guard:
        return _active is not None and _active.running


def start_job(reviews, cache):
    global _active
    with _guard:
        if _active is not None and _active.running:
            raise ReviewWiseError("Another report is already being analysed. Return to its tab and stop or finish it before starting a new one.")
        job = AnalysisJob(reviews, cache)
        _active = job
        job.thread = Thread(target=job._run, name="reviewwise-analysis", daemon=True)
        job.thread.start()
        return job
