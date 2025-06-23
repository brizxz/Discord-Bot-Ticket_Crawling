"""
票券爬蟲模組
"""
from .base import BaseCrawler, TicketInfo
from .tixcraft import TixcraftCrawler
from .kktix import KktixCrawler
from .ibon import IbonCrawler

__all__ = [
    'BaseCrawler',
    'TicketInfo', 
    'TixcraftCrawler',
    'KktixCrawler',
    'IbonCrawler'
]