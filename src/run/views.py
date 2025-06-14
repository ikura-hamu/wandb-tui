"""Views for WandB TUI application."""

from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Header, LoadingIndicator, TextArea


class RunsTableView(DataTable):
    """WandB実行データを表示するテーブルビュー"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.add_columns("ID", "Name", "State", "Created At")

    def add_run_row(self, run_id: str, name: str, state: str, created_at: str) -> None:
        """テーブルに実行データの行を追加"""
        self.add_row(run_id, name, state, created_at)

    def clear_table(self) -> None:
        """テーブルをクリア"""
        self.clear()


class LoadingView(LoadingIndicator):
    """ローディング表示のビュー"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def show_loading(self) -> None:
        """ローディングを表示"""
        self.display = True

    def hide_loading(self) -> None:
        """ローディングを非表示"""
        self.display = False


class FilterEditor(TextArea):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class MainView(Widget):
    """メインビューコンテナ"""

    def compose(self):
        """ビューを構成"""
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                yield RunsTableView(id="runs-table")
                yield LoadingView(id="loading")
            yield FilterEditor(id="filter-editor")
        yield Footer()

    def on_mount(self) -> None:
        """マウント時の初期化処理"""
        self.query_one("#left-panel", Vertical).styles.width = "70%"

    @property
    def get_runs_table(self) -> RunsTableView:
        """実行テーブルビューを取得"""
        return self.query_one("#runs-table", RunsTableView)

    @property
    def get_loading_view(self) -> LoadingView:
        """ローディングビューを取得"""
        return self.query_one("#loading", LoadingView)

    @property
    def filter_editor(self) -> FilterEditor:
        """フィルターエディタを取得"""
        return self.query_one("#filter-editor", FilterEditor)
