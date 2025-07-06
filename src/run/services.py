"""Service layer containing business logic."""

from __future__ import annotations

from .filter import Filter, FilterError
from .models import RunData, WandbRunsModel
from .repositories import RunRepository


class RunService:
    """
    Service to handle business logic related to WandB runs.
    """

    def __init__(self, repository: RunRepository) -> None:
        self._repository = repository
        self._filter = Filter("")

    def load_runs(self, project_name: str, model: WandbRunsModel) -> None:
        """
        Loads all runs from a project into the provided model.
        Notifies observers attached to the model about the progress.
        """
        model.clear_runs()
        model.notify_data_loading_started()
        try:
            count = 0
            for run_data in self._repository.get_all(project_name):
                model.add_run(run_data)  # Add to the main list
                # Notify the controller, which will then decide to show it or not
                model.notify_data_loaded(run_data)
                count += 1
            model.notify_data_loading_completed(count)
        except Exception as e:
            model.notify_data_loading_failed(e)

    def update_filter(self, filter_text: str, model: WandbRunsModel) -> None:
        """
        Updates the filter query and notifies observers with the filtered list of runs.
        """
        try:
            self._filter.update_query(filter_text)
            filtered_runs = [
                run for run in model.get_all_runs() if self.run_matches_filter(run)
            ]
            model.notify_filter_changed(filtered_runs, error=None)
        except FilterError as e:
            # Pass all runs back, but with an error message.
            model.notify_filter_changed(model.get_all_runs(), error=e)

    def run_matches_filter(self, run_data: RunData) -> bool:
        """Checks if a given run matches the current filter."""
        return self._filter.matches(run_data.dict())
