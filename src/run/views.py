"""Views for WandB TUI application."""

from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    LoadingIndicator,
    Static,
    TextArea,
)


class RunsTableView(DataTable):
    """WandB実行データを表示するテーブルビュー"""

    BINDINGS = [
        ("c", "copy_url", "Copy run URL"),
    ]

    class ReqCopyUrl(Message):
        """URLコピーのメッセージ"""

        def __init__(self, run_id: str) -> None:
            super().__init__()
            self.run_id = run_id

    def __init__(self, **kwargs) -> None:
        super().__init__(cursor_type="row", **kwargs)
        self.add_columns("id", "name", "state", "created_at")

    def add_run_row(self, run_id: str, name: str, state: str, created_at: str) -> None:
        """テーブルに実行データの行を追加"""
        self.add_row(run_id, name, state, created_at, key=run_id)

    def clear_table(self) -> None:
        """テーブルをクリア"""
        self.clear()

    def action_copy_url(self):
        run_id = self.get_row_at(self.cursor_row)[0]
        self.post_message(self.ReqCopyUrl(run_id))


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


class StatusBar(Static):
    """ステータスバー"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def update_status(self, message: str | None = None) -> None:
        """ステータスメッセージを更新"""
        if message is None:
            message = ""
        self.update(message)
        self.refresh()


class MainView(Widget):
    """メインビューコンテナ"""

    def compose(self):
        """ビューを構成"""
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                with Vertical():
                    yield RunsTableView(id="runs-table")
                    yield LoadingView(id="loading")
                yield StatusBar(id="left-status-bar")
            with Vertical(id="right-panel"):
                yield FilterEditor(id="filter-editor")
                yield StatusBar(id="right-status-bar", markup=False)
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

    @property
    def table_status_bar(self) -> StatusBar:
        """テーブルのステータスバーを取得"""
        return self.query_one("#left-status-bar", StatusBar)

    @property
    def editor_status_bar(self) -> StatusBar:
        """フィルターエディタのステータスバーを取得"""
        return self.query_one("#right-status-bar", StatusBar)
