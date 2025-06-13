"""Views for WandB TUI application."""

from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Header, LoadingIndicator


class RunsTableView(DataTable):
    """WandB実行データを表示するテーブルビュー"""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="runs-table", **kwargs)
        self.add_columns("ID", "Name", "State", "Created At")

    def add_run_row(self, run_id: str, name: str, state: str, created_at: str) -> None:
        """テーブルに実行データの行を追加"""
        self.add_row(run_id, name, state, created_at)

    def clear_table(self) -> None:
        """テーブルをクリア"""
        self.clear()
        self.add_columns("ID", "Name", "State", "Created At")


class LoadingView(LoadingIndicator):
    """ローディング表示のビュー"""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="loading", **kwargs)

    def show_loading(self) -> None:
        """ローディングを表示"""
        self.display = True

    def hide_loading(self) -> None:
        """ローディングを非表示"""
        self.display = False


class MainView(Widget):
    """メインビューコンテナ"""

    def compose(self):
        """ビューを構成"""
        yield Header()
        with Vertical():
            yield RunsTableView()
            yield LoadingView()
        yield Footer()

    def get_runs_table(self) -> RunsTableView:
        """実行テーブルビューを取得"""
        return self.query_one("#runs-table", RunsTableView)

    def get_loading_view(self) -> LoadingView:
        """ローディングビューを取得"""
        return self.query_one("#loading", LoadingView)
