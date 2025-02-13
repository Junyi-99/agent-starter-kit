from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Generic, List, TypeVar

T = TypeVar("T")


class ConcurrentTaskManager(Generic[T]):
    def __init__(self, max_workers: int | None = None):
        self.max_workers = max_workers
        self.executor = None
        self.futures: list[Future[T]] = []
        self.completed_futures: set[Future[T]] = set()

    def __enter__(self):
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown()

    def submit_task(self, func: Callable[..., T], *args, **kwargs) -> "ConcurrentTaskManager":
        """Submit a task to be executed concurrently"""
        if self.executor is None:
            raise RuntimeError("Executor is not initialized")
        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        return self

    def get_results(self) -> List[Any]:
        """Get all results from completed tasks"""
        results = []
        for future in as_completed(self.futures):
            results.append(future.result())
        return results

    def get_new_results(self) -> List[Any]:
        """Get results of tasks that have been processed since the last call"""
        new_results = []
        for future in self.futures:
            if future not in self.completed_futures and future.done():
                try:
                    result = future.result()
                    new_results.append(result)
                    self.completed_futures.add(future)
                except Exception as e:
                    print(f"Task generated an exception: {e}")
        return new_results

    def wait(self):
        """Wait for all tasks to complete"""
        for future in as_completed(self.futures):
            pass
