"""Abstract contract every air-quality scraper must implement."""

from abc import ABC, abstractmethod
from typing import ClassVar, List, Optional

from scrapers.types import SensorReading


class BaseScraper(ABC):
    """One air-quality data source, identified by its ``source`` tag."""

    source: ClassVar[str]

    @abstractmethod
    async def fetch_by_area(
        self,
        lat: float,
        lng: float,
        radius_km: Optional[int] = None,
    ) -> List[SensorReading]:
        """Fetch readings within ``radius_km`` of ``(lat, lng)``.

        Implementations should fall back to a per-source default radius when
        ``radius_km`` is ``None``. Returned readings must carry the scraper's
        ``source`` tag so callers can merge readings from multiple scrapers
        without losing provenance.
        """
        raise NotImplementedError
