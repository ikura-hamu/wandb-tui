"""Controllers for the WandB TUI application."""

from __future__ import annotations

from textual import on
from textual.widget import Widget

from .models import DataObserver, RunData, WandbRunsModel
from .services import RunService
from .views import FilterEditor, LoadingView, MainView, RunsTableView


class DataObserverImpl(DataObserver):
    """Concrete implementation of the DataObserver protocol."""

    def __init__(self, controller: "RunsController") -> None:
        self.controller = controller

    def on_data_loading_started(self) -> None:
        """Handles the start of the data loading process."""
        self.controller.app.call_from_thread(self.controller._show_loading_and_clear)
        self.controller.app.call_from_thread(
            self.controller.view.table_status_bar.update_status, "🌀 Loading runs..."
        )

    def on_data_loaded(self, run_data: RunData) -> None:
        """Handles a new run being loaded."""
        # The service decides if the run matches the filter
        if self.controller.service.run_matches_filter(run_data):
            self.controller.app.call_from_thread(
                self.controller._add_run_row,
                run_data.id,
                run_data.name,
                run_data.state,
                str(run_data.created_at),
            )

    def on_data_loading_completed(self, total_count: int) -> None:
        """Handles the completion of the data loading process."""
        self.controller.app.call_from_thread(self.controller._hide_loading)
        self.controller.app.call_from_thread(
            self.controller.view.table_status_bar.update_status, "✅ Loading completed"
        )

    def on_data_loading_failed(self, error: Exception) -> None:
        """Handles a failure in the data loading process."""
        self.controller.app.call_from_thread(self.controller._hide_loading)
        self.controller.app.call_from_thread(
            self.controller.app.notify,
            f"Failed to load data: {str(error)}",
            severity="error",
        )

    def on_filter_changed(
        self, filtered_runs: list[RunData], error: Exception | None
    ) -> None:
        """Handles a change in the filter, updating the table."""
        if error:
            self.controller.view.editor_status_bar.update_status(str(error))
        else:
            self.controller.view.editor_status_bar.update_status()

        self.controller.runs_table.clear_table()
        for run in filtered_runs:
            self.controller._add_run_row(
                run.id,
                run.name,
                run.state,
                str(run.created_at),
            )


class RunsController(Widget):
    """The controller for handling run data and view interactions."""

    def __init__(self, model: WandbRunsModel, service: RunService, **kwargs) -> None:
        super().__init__(**kwargs)
        self.model = model
        self.service = service
        self.view: MainView | None = None
        self.runs_table: RunsTableView | None = None
        self.loading_view: LoadingView | None = None
        self._observer = DataObserverImpl(self)

        self.model.add_observer(self._observer)

    def compose(self):
        yield MainView(id="main-view")

    def on_mount(self) -> None:
        """Initial setup when the widget is mounted."""
        self.view = self.query_one("#main-view", MainView)
        self.runs_table = self.view.get_runs_table
        self.loading_view = self.view.get_loading_view

    def _show_loading_and_clear(self) -> None:
        """(UI thread) Shows loading indicator and clears the table."""
        self.loading_view.show_loading()
        self.runs_table.clear_table()

    def _add_run_row(self, run_id: str, name: str, state: str, created_at: str) -> None:
        """(UI thread) Adds a row to the runs table."""
        self.runs_table.add_run_row(run_id, name, state, created_at)

    def _hide_loading(self) -> None:
        """(UI thread) Hides the loading indicator."""
        self.loading_view.hide_loading()

    def load_runs(self, project_name: str) -> None:
        """Initiates the loading of runs via the service."""
        self.service.load_runs(project_name, self.model)

    def cleanup(self) -> None:
        """Cleans up resources, like removing the observer."""
        self.model.remove_observer(self._observer)

    @on(FilterEditor.Changed)
    def on_filter_editor_changed(self, event: FilterEditor.Changed) -> None:
        """Handles changes in the filter editor."""
        self.service.update_filter(event.text_area.text, self.model)

    @on(RunsTableView.ReqCopyUrl)
    def on_req_copy_url(self, event: RunsTableView.ReqCopyUrl) -> None:
        """Handles the request to copy a run's URL."""
        run_data = self.model.find_run_by_id(event.run_id)
        if run_data:
            self.app.copy_to_clipboard(run_data.url)
            self.app.notify(f"Copied URL for run {event.run_id} to clipboard.")
        else:
            self.app.notify(f"Run {event.run_id} not found.", severity="error")

    @on(RunsTableView.ReqCopyPath)
    def on_req_copy_path(self, event: RunsTableView.ReqCopyPath) -> None:
        """Handles the request to copy a run's path."""
        run_data = self.model.find_run_by_id(event.run_id)
        if run_data:
            self.app.copy_to_clipboard(run_data.path)
            self.app.notify(f"Copied path for run {event.run_id} to clipboard.")
        else:
            self.app.notify(f"Run {event.run_id} not found.", severity="error")

    @on(RunsTableView.RowSelected)
    def on_row_selected(self, event: RunsTableView.RowSelected) -> None:
        """Handles the selection of a row in the table."""
        run_data = self.model.find_run_by_id(event.row_key.value)
        if run_data:
            self.view.run_view.show(run_data.to_dict())
