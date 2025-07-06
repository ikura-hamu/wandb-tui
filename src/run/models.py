"""Data models for WandB TUI."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

import wandb.apis.public


@dataclass
class RunData:
    """A data class representing a single WandB run."""

    id: str
    name: str
    state: str
    created_at: datetime
    url: str
    path: str
    config: dict[str, Any]

    @classmethod
    def from_wandb_run(cls, run: wandb.apis.public.Run) -> "RunData":
        """Creates a RunData object from a wandb.apis.public.Run object."""
        raw_config: dict[str, Any] = json.loads(run.json_config)
        config = {k: v.get("value") for k, v in raw_config.items()}
        path = "/".join(run.path)

        return cls(
            id=run.id,
            name=run.name,
            state=run.state,
            created_at=run.created_at,
            url=run.url,
            path=path,
            config=config,
        )

    def dict(self) -> dict[str, Any]:
        """Returns a dictionary representation of the run data."""
        return self.__dict__


class DataObserver(Protocol):
    """
    A protocol for observers that react to changes in the application's data.
    """

    def on_data_loading_started(self) -> None:
        """Called when the data loading process begins."""
        ...

    def on_data_loaded(self, run_data: RunData) -> None:
        """Called when a new piece of data (a run) is loaded."""
        ...

    def on_data_loading_completed(self, total_count: int) -> None:
        """Called when the entire data loading process is finished."""
        ...

    def on_data_loading_failed(self, error: Exception) -> None:
        """Called if an error occurs during data loading."""
        ...

    def on_filter_changed(
        self, filtered_runs: list[RunData], error: Exception | None
    ) -> None:
        """Called when the filter is updated."""
        ...


class WandbRunsModel:
    """
    The model responsible for holding the application's state (the list of runs)
    and managing observers.
    """

    def __init__(self) -> None:
        self._runs: list[RunData] = []
        self._observers: list[DataObserver] = []

    def add_observer(self, observer: DataObserver) -> None:
        """Adds an observer to the list."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: DataObserver) -> None:
        """Removes an observer from the list."""
        if observer in self._observers:
            self._observers.remove(observer)

    def add_run(self, run: RunData) -> None:
        """Adds a single run to the model's state."""
        self._runs.append(run)

    def clear_runs(self) -> None:
        """Clears all runs from the model's state."""
        self._runs.clear()

    def get_all_runs(self) -> list[RunData]:
        """Returns all runs currently held by the model."""
        return self._runs

    def find_run_by_id(self, run_id: str) -> RunData | None:
        """Finds a run by its ID."""
        for run in self._runs:
            if run.id == run_id:
                return run
        return None

    # Methods to notify observers
    def notify_data_loading_started(self) -> None:
        """Notifies all observers that data loading has started."""
        for obs in self._observers:
            obs.on_data_loading_started()

    def notify_data_loaded(self, run_data: RunData) -> None:
        """Notifies all observers that a new run has been loaded."""
        for obs in self._observers:
            obs.on_data_loaded(run_data)

    def notify_data_loading_completed(self, total_count: int) -> None:
        """Notifies all observers that data loading is complete."""
        for obs in self._observers:
            obs.on_data_loading_completed(total_count)

    def notify_data_loading_failed(self, error: Exception) -> None:
        """Notifies all observers that data loading has failed."""
        for obs in self._observers:
            obs.on_data_loading_failed(error)

    def notify_filter_changed(
        self, filtered_runs: list[RunData], error: Exception | None
    ) -> None:
        """Notifies all observers that the filter has changed."""
        for obs in self._observers:
            obs.on_filter_changed(filtered_runs, error)
