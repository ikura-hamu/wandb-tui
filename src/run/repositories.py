"""Repository layer for data access."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import wandb
from wandb.apis.public import Runs

from .models import RunData


class RunRepository(ABC):
    """Abstract base class for a repository that handles RunData objects."""

    @abstractmethod
    def get_all(self, project_name: str, per_page: int = 50) -> Iterable[RunData]:
        """Fetches all runs from a project."""
        ...


class WandbRunRepository(RunRepository):
    """Implementation of RunRepository using the WandB public API."""

    def __init__(self) -> None:
        self.api = wandb.Api()

    def get_all(self, project_name: str, per_page: int = 50) -> Iterable[RunData]:
        """
        Fetches all runs from the specified WandB project and yields them
        as RunData objects.
        """
        try:
            runs_iterator: Runs = self.api.runs(
                project_name, per_page=per_page, order="-created_at"
            )

            for run in runs_iterator:
                yield RunData.from_wandb_run(run)

        except Exception as e:
            # In a real app, you might want more specific exception handling
            # and logging here.
            print(f"Failed to fetch runs from WandB: {e}")
            raise
