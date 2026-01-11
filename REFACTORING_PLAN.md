# Frontend Refactoring Plan

## Current State
- `frontend/app.py`: 6,084 lines - monolithic file with all functionality

## Proposed Structure

```
frontend/
├── app.py                    # Main entry point (thin orchestrator, ~200 lines)
├── utils.py                  # ✅ Created - API utilities, search, display helpers
├── query_params.py           # ✅ Created - Query parameter management
├── helpers.py                 # ✅ Created - Common UI helpers (year filters)
└── pages/
    ├── __init__.py
    ├── media_tracker.py      # Movies, TV Shows, Books, Music pages (~2000 lines)
    ├── habit_tracker.py      # Habit tracking pages (~800 lines)
    ├── portfolio_tracker.py  # Portfolio tracking pages (~1500 lines)
    ├── workout_tracker.py    # Workout tracking pages (~1000 lines)
    └── analytics.py          # Analytics page (~200 lines)
```

## Implementation Steps

1. ✅ Create `utils.py` - API utilities and display helpers
2. ✅ Create `query_params.py` - Query parameter management
3. ✅ Create `helpers.py` - Common UI helpers (year filters)
4. ⏳ Create `pages/__init__.py`
5. ⏳ Extract media tracker pages to `pages/media_tracker.py`
6. ⏳ Extract habit tracker pages to `pages/habit_tracker.py`
7. ⏳ Extract portfolio tracker pages to `pages/portfolio_tracker.py`
8. ⏳ Extract workout tracker pages to `pages/workout_tracker.py`
9. ⏳ Extract analytics page to `pages/analytics.py`
10. ⏳ Refactor `app.py` to be a thin orchestrator

## Function Mapping

### utils.py (✅ Done)
- `make_authenticated_request()`
- `search_media()`
- `get_tv_show_seasons()`
- `get_tv_show_thumbnail()`
- `display_search_results()`
- `display_media_thumbnail()`

### query_params.py (✅ Done)
- `get_query_params()`
- `initialize_state_from_query_params()`
- `update_query_params()`
- `get_filter_from_query_params()`

### helpers.py (✅ Done)
- `get_year_filter()`

### pages/media_tracker.py (⏳ TODO)
- `movies_page()`
- `tv_shows_page()`
- `books_page()`
- `music_page()`
- `manual_entry_page()`

### pages/habit_tracker.py (⏳ TODO)
- `habit_tracker_page()`
- `log_habits_tab()`
- `calendar_tab()`
- `display_monthly_calendar()`
- `display_quarterly_calendar()`
- `display_yearly_calendar()`
- `habit_analytics_tab()`

### pages/portfolio_tracker.py (⏳ TODO)
- `portfolio_overview_page()`
- `portfolio_transactions_page()`
- `portfolio_upload_page()`
- `portfolio_individual_holdings_page()`
- `portfolio_allocation_page()`

### pages/workout_tracker.py (⏳ TODO)
- `log_workout_page()`
- `workout_history_page()`
- `exercises_page()`
- `workout_templates_page()`
- `workout_progress_page()`
- `workout_analytics_page()`

### pages/analytics.py (⏳ TODO)
- `analytics_page()`

### app.py (⏳ TODO - Refactor to ~200 lines)
- Page configuration
- `main_app()` - routing logic only
