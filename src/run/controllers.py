"""Controllers for WandB TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import DataObserver, RunData, WandbRunsModel

if TYPE_CHECKING:
    from .app import RunApp
    from .views import MainView


class RunsController(DataObserver):
    """WandB実行データの表示を制御するコントローラー"""

    def __init__(self, model: WandbRunsModel, view: MainView, app: RunApp) -> None:
        self.model = model
        self.view = view
        self.app = app
        self.runs_table = view.get_runs_table()
        self.loading_view = view.get_loading_view()

        # モデルのオブザーバーとして登録
        self.model.add_observer(self)

    def toggle_filter(self) -> None:
        """フィルターを切り替える"""
        self.model.toggle_filter()

    def on_data_loading_started(self) -> None:
        """データ読み込み開始時の処理"""
        self.app.call_from_thread(self._show_loading_and_clear)

    def on_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時の処理"""
        if self.model.filter_run(run_data):
            self.app.call_from_thread(
                self._add_run_row,
                run_data.id,
                run_data.name,
                run_data.state,
                str(run_data.created_at),
            )

    def on_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時の処理"""
        self.app.call_from_thread(self._hide_loading)

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時の処理"""
        self.app.call_from_thread(self._hide_loading)
        self.app.call_from_thread(
            self.app.notify, f"Failed to load data: {str(error)}", severity="error"
        )

    def on_filter_changed(self, filtered_runs: list[RunData]) -> None:
        """フィルターが変更された時の処理"""
        # self.app.call_from_thread(self._show_loading_and_clear)
        self.runs_table.clear_table()
        for run in filtered_runs:
            self._add_run_row(
                run.id,
                run.name,
                run.state,
                str(run.created_at),
            )

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
