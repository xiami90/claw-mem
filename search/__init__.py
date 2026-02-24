"""
OpenClaw 轻量化三层记忆模型 - 搜索模块
Search module for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
"""

from .vector_search import VectorSearch, SearchResult, SearchSuggestion

__all__ = ['VectorSearch', 'SearchResult', 'SearchSuggestion']
__version__ = '1.0.0'
__author__ = 'DataBot'