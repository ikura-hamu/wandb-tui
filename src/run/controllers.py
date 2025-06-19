"""Controllers for WandB TUI application."""

from __future__ import annotations

from textual import on
from textual.widget import Widget

from run.views import FilterEditor, LoadingView, MainView, RunsTableView

from .models import DataObserver, RunData, WandbRunsModel


class DataObserverImpl(DataObserver):
    """データオブザーバーの実装"""

    def __init__(self, controller: RunsController) -> None:
        self.controller = controller

    def on_data_loading_started(self) -> None:
        """データ読み込み開始時の処理"""
        self.controller.app.call_from_thread(self.controller._show_loading_and_clear)
        self.controller.app.call_from_thread(
            self.controller.view.table_status_bar.update_status, "🌀 Loading runs..."
        )

    def on_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時の処理"""
        if self.controller.model.filter_run(run_data):
            self.controller.app.call_from_thread(
                self.controller._add_run_row,
                run_data.id,
                run_data.name,
                run_data.state,
                str(run_data.created_at),
            )

    def on_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時の処理"""
        self.controller.app.call_from_thread(self.controller._hide_loading)
        self.controller.app.call_from_thread(
            self.controller.view.table_status_bar.update_status, "✅ Loading completed"
        )

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時の処理"""
        self.controller.app.call_from_thread(self.controller._hide_loading)
        self.controller.app.call_from_thread(
            self.controller.app.notify,
            f"Failed to load data: {str(error)}",
            severity="error",
        )

    def on_filter_changed(
        self, filtered_runs: list[RunData], error: Exception | None
    ) -> None:
        """フィルターが変更された時の処理"""
        if error:
            self.controller.view.editor_status_bar.update_status(str(error))
            return
        self.controller.runs_table.clear_table()
        for run in filtered_runs:
            self.controller._add_run_row(
                run.id,
                run.name,
                run.state,
                str(run.created_at),
            )
        self.controller.view.editor_status_bar.update_status()


class RunsController(Widget):
    """WandB実行データの表示を制御するコントローラー"""

    def __init__(self, model: WandbRunsModel, **kwargs) -> None:
        super().__init__(**kwargs)
        self.model = model
        self.view: MainView | None = None
        self.runs_table: RunsTableView | None = None  # MainViewから取得するテーブル
        self.loading_view: LoadingView | None = (
            None  # MainViewから取得するローディングビュー
        )
        # self.loading_view = view.get_loading_view()
        self._observer = DataObserverImpl(self)

        # モデルのオブザーバーとして登録
        self.model.add_observer(self._observer)

    def compose(self):
        yield MainView(id="main-view")

    def on_mount(self) -> None:
        """マウント時の初期化処理"""
        self.view = self.query_one("#main-view", MainView)
        self.runs_table = self.view.get_runs_table
        self.loading_view = self.view.get_loading_view

    def _show_loading_and_clear(self) -> None:
        """ローディング表示とテーブルクリア（UIスレッド用）"""
        self.loading_view.show_loading()
        self.runs_table.clear_table()

    def _add_run_row(self, run_id: str, name: str, state: str, created_at: str) -> None:
        """テーブルに行を追加（UIスレッド用）"""
        self.runs_table.add_run_row(run_id, name, state, created_at)

    def _hide_loading(self) -> None:
        """ローディング非表示（UIスレッド用）"""
        self.loading_view.hide_loading()

    def load_runs(self, project_name: str) -> None:
        """実行データの読み込みを開始"""
        self.model.load_runs(project_name)

    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.model.remove_observer(self)

    @on(FilterEditor.Changed)
    def on_filter_editor_changed(self, event: FilterEditor.Changed) -> None:
        """フィルターエディタの変更イベントハンドラ"""
        self.model.edit_filter(event.text_area.text)

    @on(RunsTableView.ReqCopyUrl)
    def on_req_copy_url(self, event: RunsTableView.ReqCopyUrl) -> None:
        """URLコピー要求イベントハンドラ"""
        run_id = event.run_id
        run_data = self.model.find_run_by_id(run_id)
        if run_data:
            self.app.copy_to_clipboard(run_data.url)
            self.app.notify(f"Copied URL for run {run_id} to clipboard.")
        else:
            self.app.notify(f"Run {run_id} not found.", severity="error")

    @on(RunsTableView.ReqCopyPath)
    def on_req_copy_path(self, event: RunsTableView.ReqCopyPath) -> None:
        """パスコピー要求イベントハンドラ"""
        run_id = event.run_id
        run_data = self.model.find_run_by_id(run_id)
        if run_data:
            self.app.copy_to_clipboard(run_data.path)
            self.app.notify(f"Copied path for run {run_id} to clipboard.")
        else:
            self.app.notify(f"Run {run_id} not found.", severity="error")

    @on(RunsTableView.RowSelected)
    def on_row_selected(self, event: RunsTableView.RowSelected) -> None:
        """行選択イベントハンドラ"""
        run_id = event.row_key
        run_data = self.model.find_run_by_id(run_id)
        if run_data:
            self.view.run_view.show(run_data.dict())
