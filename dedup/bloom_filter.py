import hashlib
from pybloom_live import ScalableBloomFilter
from typing import Optional


class BloomFilter:
    def __init__(self, name: str, capacity: int = 1000000, error_rate: float = 0.001):
        self.name = name
        self.capacity = capacity
        self.error_rate = error_rate
        self._filter = ScalableBloomFilter(
            initial_capacity=capacity,
            error_rate=error_rate
        )

    def add(self, item: str):
        fingerprint = self._generate_fingerprint(item)
        self._filter.add(fingerprint)

    def contains(self, item: str) -> bool:
        fingerprint = self._generate_fingerprint(item)
        return fingerprint in self._filter

    def _generate_fingerprint(self, item: str) -> str:
        return hashlib.md5(item.encode('utf-8')).hexdigest()

    def __contains__(self, item: str) -> bool:
        return self.contains(item)

    def __len__(self) -> int:
        return len(self._filter)

    @property
    def capacity(self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self, value: int):
        self._capacity = value

    @property
    def error_rate(self) -> float:
        return self._error_rate

    @error_rate.setter
    def error_rate(self, value: float):
        self._error_rate = value