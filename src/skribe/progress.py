from __future__ import annotations

from typing import TYPE_CHECKING

from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

if TYPE_CHECKING:
    from collections.abc import Iterable

    from rich.progress import TaskID

    from .contract import Signature


class FuzzProgress(Progress):
    fuzz_tasks: list[FuzzTask]

    def __init__(self, signatures: Iterable[Signature], max_examples: int):
        super().__init__(
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TextColumn('{task.fields[status]}'),
        )

        self.fuzz_tasks = []

        # Add all tests to the progress display before running them
        for signature in signatures:
            description = signature.qualified_name
            task_id = self.add_task(description, total=max_examples, start=False, status='Waiting')
            self.fuzz_tasks.append(FuzzTask(signature, task_id, self))


class FuzzTask:
    signature: Signature
    task_id: TaskID
    progress: FuzzProgress

    def __init__(self, signature: Signature, task_id: TaskID, progress: FuzzProgress):
        self.signature = signature
        self.task_id = task_id
        self.progress = progress

    def start(self) -> None:
        self.progress.start_task(self.task_id)
        self.progress.update(self.task_id, status='[bold]Running')

    def end(self) -> None:
        self.progress.update(
            self.task_id, total=self.progress._tasks[self.task_id].completed, status='[bold green]Passed'
        )

    def advance(self) -> None:
        self.progress.advance(self.task_id)

    def fail(self) -> None:
        self.progress.update(self.task_id, status='[bold red]Failed')
        self.progress.stop_task(self.task_id)
