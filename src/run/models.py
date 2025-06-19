"""Data models and business logic for WandB TUI."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

import wandb.apis.public.runs

from .filter import Filter, FilterError


@dataclass
class RunData:
    """WandB実行データを表すモデル"""

    id: str
    name: str
    state: str
    created_at: datetime
    url: str
    path: str
    config: dict[str, Any]

    @classmethod
    def from_wandb_run(cls, run: wandb.apis.public.runs.Run) -> RunData:
        raw_config: dict[str, Any] = json.loads(run.json_config)
        config = {k: v["value"] for k, v in raw_config.items()}

        path = "/".join(run.path)

        """WandB RunオブジェクトからRunDataを作成"""
        return cls(
            id=run.id,
            name=run.name,
            state=run.state,
            created_at=run.created_at,
            url=run.url,
            path=path,
            config=config,
        )

    def dict(self):
        return self.__dict__


class DataObserver(Protocol):
    """データ変更を観察するためのプロトコル"""

    def on_data_loading_started(self) -> None:
        """データ読み込み開始時に呼ばれる"""
        ...

    def on_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時に呼ばれる"""
        ...

    def on_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時に呼ばれる"""
        ...

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時に呼ばれる"""
        ...

    def on_filter_changed(
        self, filtered_runs: list[RunData], error: Exception | None
    ) -> None:
        """フィルターが変更された時に呼ばれる"""
        ...


class WandbDataSource(ABC):
    """WandBデータソースの抽象基底クラス"""

    @abstractmethod
    def fetch_runs(
        self,
        project_name: str,
        per_page: int,
        observer: DataObserver | None = None,
    ) -> None:
        """実行データを取得する"""
        ...


class WandbApiDataSource(WandbDataSource):
    """WandB APIを使用したデータソース実装"""

    def __init__(self) -> None:
        self.api = wandb.Api()

    def fetch_runs(
        self,
        project_name: str,
        per_page: int,
        observer: WandbRunsModel | None = None,
    ) -> None:
        """WandB APIから実行データを取得"""
        if observer:
            observer.notify_data_loading_started()

        try:
            runs_iterator = self.api.runs(
                project_name, per_page=per_page, order="-created_at"
            )

            count = 0
            for run in runs_iterator:
                run_data = RunData.from_wandb_run(run)
                if observer:
                    observer.notify_data_loaded(run_data)
                count += 1

            if observer:
                observer.notify_data_loading_completed(count)

        except Exception as e:
            if observer:
                observer.notify_data_loading_failed(e)
            raise


class WandbRunsModel:
    """WandB実行データを管理するモデル"""

    def __init__(self, data_source: WandbDataSource, filter_text: str) -> None:
        self.data_source = data_source
        self.runs: list[RunData] = []
        self._observers: list[DataObserver] = []
        self._filter: Filter = Filter(filter_text)

    def add_observer(self, observer: DataObserver) -> None:
        """オブザーバーを追加"""
        self._observers.append(observer)

    def remove_observer(self, observer: DataObserver) -> None:
        """オブザーバーを削除"""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, method_name: str, *args, **kwargs) -> None:
        """全オブザーバーに通知"""
        for observer in self._observers:
            method = getattr(observer, method_name)
            method(*args, **kwargs)

    def edit_filter(self, filter_text: str) -> None:
        """フィルターを編集"""
        try:
            self._filter.update_query(filter_text)
        except FilterError as e:
            self.notify_filter_changed(e)
            return

        self.notify_filter_changed(None)

    def get_filtered_runs(self) -> list[RunData]:
        """フィルターに基づいて実行データを取得"""
        return [run for run in self.runs if self._filter.matches(run.dict())]

    def filter_run(self, run_data: RunData) -> bool:
        """実行データがフィルターに一致するかチェック"""
        if self._filter is None:
            return True
        return self._filter.matches(run_data.dict())

    def find_run_by_id(self, run_id: str) -> RunData | None:
        """IDで実行データを検索"""
        for run in self.runs:
            if run.id == run_id:
                return run
        return None

    def notify_data_loading_started(self) -> None:
        """データ読み込み開始時の処理"""
        for obs in self._observers:
            obs.on_data_loading_started()

    def notify_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時の処理"""
        self.runs.append(run_data)
        for obs in self._observers:
            obs.on_data_loaded(run_data)

    def notify_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時の処理"""
        for obs in self._observers:
            obs.on_data_loading_completed(total_count)

    def notify_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時の処理"""
        for obs in self._observers:
            obs.on_data_loading_failed(error)

    def notify_filter_changed(self, error: Exception | None) -> None:
        """フィルターが変更された時の処理"""
        for obs in self._observers:
            obs.on_filter_changed(self.get_filtered_runs(), error=error)

    def load_runs(self, project_name: str, per_page: int = 50) -> None:
        """実行データを読み込む"""
        self.data_source.fetch_runs(project_name, per_page, self)

    def clear_runs(self) -> None:
        """実行データをクリア"""
        self.runs.clear()
