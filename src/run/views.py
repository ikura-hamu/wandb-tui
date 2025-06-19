"""Views for WandB TUI application."""

from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    LoadingIndicator,
    Pretty,
    Static,
    TextArea,
    Tree,
)
from textual.widgets.data_table import RowDoesNotExist


class RunsTableView(DataTable):
    """WandB実行データを表示するテーブルビュー"""

    BINDINGS = [
        ("C", "copy_url", "Copy run URL"),
        ("c", "copy_path", "Copy run path"),
    ]

    class ReqCopyUrl(Message):
        """URLコピーのメッセージ"""

        def __init__(self, run_id: str) -> None:
            super().__init__()
            self.run_id = run_id

    class ReqCopyPath(Message):
        """pathコピーのメッセージ"""

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

    def action_copy_path(self):
        try:
            run_id = self.get_row_at(self.cursor_row)[0]
        except RowDoesNotExist:
            return
        # Assuming the path is just the run ID for simplicity
        self.post_message(self.ReqCopyPath(run_id))


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


class RunView(Widget):
    BINDINGS = [
        ("q", "hide", "Hide run view"),
    ]

    def __init__(
        self,
        *children,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        markup=True,
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.display = False
        self.content: Pretty | None = None
        self.obj_tree: Tree | None = None

    def compose(self):
        # with VerticalScroll():
        yield Tree(label="Run")

    def on_mount(self) -> None:
        self.obj_tree = self.query_one(Tree)

    def show(self, obj: object | None = None):
        self.display = True

        if obj is not None:
            self.obj_tree.focus()
            self.obj_tree.clear()
            self.obj_tree.add_json(obj)
            root_node = self.obj_tree.root.expand()
            for child in root_node.children:
                child.expand()

    def _hide(self):
        self.display = False

    def action_hide(self):
        """Hide the run view when 'q' is pressed."""
        self._hide()


class MainView(Widget):
    """メインビューコンテナ"""

    def compose(self):
        """ビューを構成"""
        yield Header()
        with Horizontal():
            with Horizontal(id="left-panel"):
                with Vertical(id="table-section"):
                    yield RunsTableView(id="runs-table")
                    yield LoadingView(id="loading")
                    yield StatusBar(id="left-status-bar")
                yield RunView(id="run-view")
            with Vertical(id="right-panel"):
                yield FilterEditor(id="filter-editor")
                yield StatusBar(id="right-status-bar", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        """マウント時の初期化処理"""
        # 初期状態でRunViewを非表示にする
        run_view = self.query_one("#run-view", RunView)
        run_view.display = False

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

    @property
    def run_view(self) -> RunView:
        """実行ビューを取得"""
        return self.query_one("#run-view", RunView)
