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

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時の処理"""
        self.controller.app.call_from_thread(self.controller._hide_loading)
        self.controller.app.call_from_thread(
            self.controller.app.notify,
            f"Failed to load data: {str(error)}",
            severity="error",
        )

    def on_filter_changed(self, filtered_runs: list[RunData]) -> None:
        """フィルターが変更された時の処理"""
        self.controller.runs_table.clear_table()
        for run in filtered_runs:
            self.controller._add_run_row(
                run.id,
                run.name,
                run.state,
                str(run.created_at),
            )


class RunsController(Widget):
    """WandB実行データの表示を制御するコントローラー"""

    BINDINGS = [
        ("f", "toggle_filter", "Toggle finished runs"),
    ]

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

    def toggle_filter(self) -> None:
        """フィルターを切り替える"""
        self.model.toggle_filter()

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

    def action_toggle_filter(self) -> None:
        """フィルターを切り替え"""
        self.model.toggle_filter()

    @on(FilterEditor.Changed)
    def on_filter_editor_changed(self, event: FilterEditor.Changed) -> None:
        """フィルターエディタの変更イベントハンドラ"""
        self.model.edit_filter(event.text_area.text)
