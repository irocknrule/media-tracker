import calendar
import re
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import InvestmentAccount, AccountSnapshot, PortfolioAggregateSnapshot
from backend import schemas

router = APIRouter(prefix="/fire", tags=["fire"])


# ---------------------------------------------------------------------------
# Account endpoints
# ---------------------------------------------------------------------------

def _enrich_account(account: InvestmentAccount) -> dict:
    """Convert an InvestmentAccount ORM object to a dict with latest snapshot info."""
    latest = account.snapshots[0] if account.snapshots else None
    return {
        "id": account.id,
        "name": account.name,
        "account_type": account.account_type,
        "owner": account.owner,
        "institution": account.institution,
        "last_four": account.last_four,
        "is_active": account.is_active,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "latest_balance": latest.balance if latest else None,
        "latest_snapshot_date": latest.snapshot_date if latest else None,
    }


@router.get("/accounts", response_model=List[schemas.InvestmentAccount])
def list_accounts(
    owner: Optional[str] = None,
    account_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(InvestmentAccount)
    if owner:
        query = query.filter(InvestmentAccount.owner == owner)
    if account_type:
        query = query.filter(InvestmentAccount.account_type == account_type)
    query = query.order_by(InvestmentAccount.owner, InvestmentAccount.name)
    return [_enrich_account(a) for a in query.all()]


@router.post("/accounts", response_model=schemas.InvestmentAccount)
def create_account(
    data: schemas.InvestmentAccountCreate,
    db: Session = Depends(get_db),
):
    account = InvestmentAccount(
        name=data.name,
        account_type=data.account_type,
        owner=data.owner,
        institution=data.institution,
        last_four=data.last_four,
        is_active=data.is_active,
    )
    db.add(account)
    db.flush()

    if data.balance is not None:
        snap = AccountSnapshot(
            account_id=account.id,
            snapshot_date=data.snapshot_date or date.today(),
            balance=data.balance,
        )
        db.add(snap)

    db.commit()
    db.refresh(account)
    return _enrich_account(account)


@router.put("/accounts/{account_id}", response_model=schemas.InvestmentAccount)
def update_account(
    account_id: int,
    data: schemas.InvestmentAccountUpdate,
    db: Session = Depends(get_db),
):
    account = db.query(InvestmentAccount).filter(InvestmentAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(account)
    return _enrich_account(account)


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(InvestmentAccount).filter(InvestmentAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
    return {"message": "Account and all snapshots deleted"}


# ---------------------------------------------------------------------------
# Monarch bulk import
# ---------------------------------------------------------------------------

ACCOUNT_TYPE_MAP = {
    "brokerage (taxable)": "BROKERAGE",
    "brokerage": "BROKERAGE",
    "individual retirement account (ira)": "IRA",
    "individual retirement (ira)": "IRA",
    "ira": "IRA",
    "roth ira": "ROTH_IRA",
    "roth": "ROTH_IRA",
    "401k": "401K",
    "401(k)": "401K",
    "health savings account (hsa)": "HSA",
    "hsa": "HSA",
    "stock plan": "STOCK_PLAN",
}


def _normalize_account_type(raw: str) -> str:
    lower = raw.strip().lower()
    for pattern, mapped in ACCOUNT_TYPE_MAP.items():
        if pattern in lower:
            return mapped
    return "OTHER"


def _parse_monarch_text(text: str) -> list[dict]:
    """
    Parse text copied/pasted from a Monarch Money investments view.
    Each account block typically looks like:
        Account Name (..XXXX)
        Account Type   Owner
        $123,456.78
    We capture: name, type hint, owner, balance.
    """
    results = []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    balance_re = re.compile(r'\$[\d,]+\.\d{2}')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip lines that are purely metadata like "19 hours ago", "Account disconnected", etc.
        if re.match(r'^\d+\s+(hours?|days?|minutes?)\s+ago$', line, re.IGNORECASE):
            i += 1
            continue
        if 'account disconnected' in line.lower():
            i += 1
            continue
        if line.lower().startswith('investments') or line.lower().startswith('1 month change'):
            i += 1
            continue

        # Check if this line has a dollar balance
        balance_match = balance_re.search(line)
        if balance_match:
            balance_str = balance_match.group().replace('$', '').replace(',', '')
            balance = float(balance_str)

            # Look backwards for account info
            name = ""
            account_type_hint = ""
            owner = ""

            # Search previous non-balance, non-metadata lines for account info
            lookback = i - 1
            info_lines = []
            while lookback >= 0 and len(info_lines) < 3:
                prev = lines[lookback]
                if balance_re.search(prev):
                    break
                if re.match(r'^\d+\s+(hours?|days?|minutes?)\s+ago$', prev, re.IGNORECASE):
                    lookback -= 1
                    continue
                if 'account disconnected' in prev.lower():
                    lookback -= 1
                    continue
                info_lines.insert(0, prev)
                lookback -= 1

            if len(info_lines) >= 2:
                name = info_lines[0]
                type_owner_line = info_lines[1]
                # Try to split type and owner – owner is typically the last word
                parts = type_owner_line.rsplit(None, 1)
                if len(parts) == 2:
                    account_type_hint = parts[0]
                    owner = parts[1]
                else:
                    account_type_hint = type_owner_line
            elif len(info_lines) == 1:
                name = info_lines[0]

            # Extract last_four from name if present
            last_four_match = re.search(r'[\.\*]+(\w{3,4})\)?$', name)
            last_four = last_four_match.group(1) if last_four_match else None

            results.append({
                "name": name,
                "account_type": _normalize_account_type(account_type_hint),
                "owner": owner,
                "institution": None,
                "last_four": last_four,
                "balance": balance,
            })

        i += 1

    return results


@router.post("/accounts/bulk", response_model=schemas.BulkAccountImportResult)
def bulk_import_accounts(
    data: schemas.BulkAccountImport,
    db: Session = Depends(get_db),
):
    parsed = _parse_monarch_text(data.text)
    snap_date = data.snapshot_date or date.today()

    accounts_created = 0
    accounts_updated = 0
    snapshots_created = 0
    result_accounts = []

    for entry in parsed:
        # Try to find existing account by name
        existing = db.query(InvestmentAccount).filter(
            InvestmentAccount.name == entry["name"]
        ).first()

        if existing:
            existing.account_type = entry["account_type"]
            existing.owner = entry["owner"]
            if entry["last_four"]:
                existing.last_four = entry["last_four"]
            existing.updated_at = datetime.utcnow()
            account = existing
            accounts_updated += 1
        else:
            account = InvestmentAccount(
                name=entry["name"],
                account_type=entry["account_type"],
                owner=entry["owner"],
                institution=entry["institution"],
                last_four=entry["last_four"],
            )
            db.add(account)
            db.flush()
            accounts_created += 1

        snap = AccountSnapshot(
            account_id=account.id,
            snapshot_date=snap_date,
            balance=entry["balance"],
        )
        db.add(snap)
        snapshots_created += 1
        result_accounts.append(account)

    db.commit()
    for a in result_accounts:
        db.refresh(a)

    return {
        "accounts_created": accounts_created,
        "accounts_updated": accounts_updated,
        "snapshots_created": snapshots_created,
        "accounts": [_enrich_account(a) for a in result_accounts],
    }


# ---------------------------------------------------------------------------
# Snapshot endpoints
# ---------------------------------------------------------------------------

@router.get("/accounts/{account_id}/snapshots", response_model=List[schemas.AccountSnapshot])
def list_snapshots(account_id: int, db: Session = Depends(get_db)):
    account = db.query(InvestmentAccount).filter(InvestmentAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.snapshots


@router.post("/snapshots/bulk", response_model=List[schemas.AccountSnapshot])
def bulk_create_snapshots(
    data: schemas.BulkSnapshotCreate,
    db: Session = Depends(get_db),
):
    created = []
    for entry in data.entries:
        account = db.query(InvestmentAccount).filter(InvestmentAccount.id == entry.account_id).first()
        if not account:
            continue
        snap = AccountSnapshot(
            account_id=entry.account_id,
            snapshot_date=data.snapshot_date,
            balance=entry.balance,
            contributions_since_last=entry.contributions_since_last,
        )
        db.add(snap)
        created.append(snap)
    db.commit()
    for s in created:
        db.refresh(s)
    return created


@router.put("/snapshots/{snapshot_id}", response_model=schemas.AccountSnapshot)
def update_snapshot(
    snapshot_id: int,
    data: schemas.AccountSnapshotUpdate,
    db: Session = Depends(get_db),
):
    snap = db.query(AccountSnapshot).filter(AccountSnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(snap, field, value)
    db.commit()
    db.refresh(snap)
    return snap


@router.delete("/snapshots/{snapshot_id}")
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.query(AccountSnapshot).filter(AccountSnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.delete(snap)
    db.commit()
    return {"message": "Snapshot deleted"}


# ---------------------------------------------------------------------------
# Dashboard / aggregation
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=schemas.FireDashboard)
def get_dashboard(db: Session = Depends(get_db)):
    accounts = db.query(InvestmentAccount).filter(InvestmentAccount.is_active == True).all()

    total_value = 0.0
    owner_map: dict[str, dict] = {}
    type_map: dict[str, dict] = {}

    for account in accounts:
        latest = account.snapshots[0] if account.snapshots else None
        bal = latest.balance if latest else 0.0
        total_value += bal

        if account.owner not in owner_map:
            owner_map[account.owner] = {"owner": account.owner, "total_value": 0.0, "account_count": 0}
        owner_map[account.owner]["total_value"] += bal
        owner_map[account.owner]["account_count"] += 1

        if account.account_type not in type_map:
            type_map[account.account_type] = {"account_type": account.account_type, "total_value": 0.0, "account_count": 0}
        type_map[account.account_type]["total_value"] += bal
        type_map[account.account_type]["account_count"] += 1

    # Month-over-month: compare latest snapshot set to previous snapshot set
    all_snapshots = (
        db.query(AccountSnapshot.snapshot_date)
        .distinct()
        .order_by(AccountSnapshot.snapshot_date.desc())
        .all()
    )
    unique_dates = [row[0] for row in all_snapshots]

    mom_change = None
    mom_change_pct = None
    total_income = None

    if len(unique_dates) >= 2:
        latest_date = unique_dates[0]
        prev_date = unique_dates[1]

        latest_total = (
            db.query(func.sum(AccountSnapshot.balance))
            .filter(AccountSnapshot.snapshot_date == latest_date)
            .scalar() or 0.0
        )
        prev_total = (
            db.query(func.sum(AccountSnapshot.balance))
            .filter(AccountSnapshot.snapshot_date == prev_date)
            .scalar() or 0.0
        )

        contributions = (
            db.query(func.sum(AccountSnapshot.contributions_since_last))
            .filter(AccountSnapshot.snapshot_date == latest_date)
            .scalar() or 0.0
        )

        mom_change = latest_total - prev_total
        mom_change_pct = (mom_change / prev_total * 100) if prev_total else None
        total_income = mom_change - contributions

    return {
        "total_portfolio_value": total_value,
        "by_owner": sorted(owner_map.values(), key=lambda x: x["total_value"], reverse=True),
        "by_account_type": sorted(type_map.values(), key=lambda x: x["total_value"], reverse=True),
        "total_investment_income": total_income,
        "month_over_month_change": mom_change,
        "month_over_month_change_pct": mom_change_pct,
    }


def _build_timeline(db: Session, account_ids: list[int] | None = None) -> list[dict]:
    """
    Build a unified timeline of (date, total_value, contributions) from both
    per-account snapshots and aggregate portfolio snapshots.
    When account_ids is provided, aggregate snapshots are scaled by the ratio
    of the selected accounts' value to the full per-account total, preserving
    the historical timeline while approximating the filtered view.
    """
    acct_query = db.query(
        AccountSnapshot.snapshot_date,
        func.sum(AccountSnapshot.balance),
        func.sum(AccountSnapshot.contributions_since_last),
    )
    if account_ids is not None:
        acct_query = acct_query.filter(AccountSnapshot.account_id.in_(account_ids))
    acct_rows = acct_query.group_by(AccountSnapshot.snapshot_date).all()
    acct_map = {row[0]: {"value": row[1] or 0.0, "contributions": row[2] or 0.0, "source": "accounts"} for row in acct_rows}

    agg_rows = db.query(PortfolioAggregateSnapshot).order_by(
        PortfolioAggregateSnapshot.snapshot_date
    ).all()

    if account_ids is None:
        agg_map = {row.snapshot_date: {"value": row.total_value, "contributions": row.contributions_since_last or 0.0, "source": "aggregate"} for row in agg_rows}
        combined = {**acct_map, **agg_map}
    else:
        # Compute the ratio of selected accounts to all accounts so we can
        # scale aggregate snapshots proportionally.
        all_acct_rows = (
            db.query(
                AccountSnapshot.snapshot_date,
                func.sum(AccountSnapshot.balance),
            )
            .group_by(AccountSnapshot.snapshot_date)
            .all()
        )
        all_acct_totals = {row[0]: (row[1] or 0.0) for row in all_acct_rows}

        ratios = []
        for d in sorted(acct_map.keys()):
            all_total = all_acct_totals.get(d, 0.0)
            if all_total > 0:
                ratios.append(acct_map[d]["value"] / all_total)

        ratio = sum(ratios) / len(ratios) if ratios else 1.0

        agg_map = {}
        for row in agg_rows:
            agg_map[row.snapshot_date] = {
                "value": row.total_value * ratio,
                "contributions": (row.contributions_since_last or 0.0) * ratio,
                "source": "aggregate_scaled",
            }

        # Per-account data takes precedence over scaled aggregates
        combined = {**agg_map, **acct_map}

    timeline = sorted(combined.items(), key=lambda x: x[0])
    return [{"date": d, **v} for d, v in timeline]


def _interpolate_value(d: date, timeline: list[dict]) -> float:
    """Linearly interpolate portfolio value at a given date from timeline points."""
    if not timeline:
        return 0.0
    if d <= timeline[0]["date"]:
        return timeline[0]["value"]
    if d >= timeline[-1]["date"]:
        return timeline[-1]["value"]
    for i in range(1, len(timeline)):
        if timeline[i]["date"] >= d:
            d0 = timeline[i - 1]["date"]
            d1 = timeline[i]["date"]
            v0 = timeline[i - 1]["value"]
            v1 = timeline[i]["value"]
            span = (d1 - d0).days
            if span == 0:
                return v1
            frac = (d - d0).days / span
            return v0 + (v1 - v0) * frac
    return timeline[-1]["value"]


def _interpolate_contributions(start: date, end: date, timeline: list[dict]) -> float:
    """Pro-rate contributions from timeline points that fall within [start, end]."""
    total = 0.0
    for pt in timeline:
        if pt["date"] <= start:
            continue
        if pt["date"] > end:
            break
        total += pt.get("contributions", 0.0)
    return total


def _generate_boundaries(start: date, end: date, interval: str) -> list[date]:
    """Generate calendar boundary dates between start and end (inclusive of both)."""
    boundaries = [start]
    if interval == "monthly":
        y, m = start.year, start.month
        while True:
            last_day = date(y, m, calendar.monthrange(y, m)[1])
            if last_day > end:
                break
            if last_day > start:
                boundaries.append(last_day)
            m += 1
            if m > 12:
                m = 1
                y += 1
    elif interval == "quarterly":
        quarter_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]
        y = start.year
        while True:
            for qm, qd in quarter_ends:
                qdate = date(y, qm, qd)
                if qdate > end:
                    break
                if qdate > start and qdate not in boundaries:
                    boundaries.append(qdate)
            else:
                y += 1
                continue
            break
    elif interval == "yearly":
        y = start.year
        while True:
            ydate = date(y, 12, 31)
            if ydate > end:
                break
            if ydate > start:
                boundaries.append(ydate)
            y += 1

    if boundaries[-1] != end:
        boundaries.append(end)
    return boundaries


@router.get("/income-history", response_model=schemas.IncomeHistory)
def get_income_history(
    interval: str = Query("quarterly", regex="^(monthly|quarterly|yearly)$"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs to filter by"),
    db: Session = Depends(get_db),
):
    """
    Compute investment income over standard calendar intervals by interpolating
    between snapshot data points.  Optionally filter to specific accounts.
    """
    parsed_ids = None
    if account_ids:
        parsed_ids = [int(x) for x in account_ids.split(",") if x.strip().isdigit()]
        if not parsed_ids:
            parsed_ids = None
    timeline = _build_timeline(db, account_ids=parsed_ids)

    if len(timeline) < 2:
        return {
            "entries": [],
            "total_investment_income": 0.0,
            "total_contributions": 0.0,
        }

    start = timeline[0]["date"]
    end = timeline[-1]["date"]
    boundaries = _generate_boundaries(start, end, interval)

    entries = []
    total_income = 0.0
    total_contributions = 0.0

    for i in range(1, len(boundaries)):
        period_start = boundaries[i - 1]
        period_end = boundaries[i]

        start_val = _interpolate_value(period_start, timeline)
        end_val = _interpolate_value(period_end, timeline)
        contributions = _interpolate_contributions(period_start, period_end, timeline)

        income = end_val - start_val - contributions
        growth_pct = (income / start_val * 100) if start_val else 0.0

        entries.append({
            "period_start": period_start,
            "period_end": period_end,
            "starting_balance": round(start_val, 2),
            "ending_balance": round(end_val, 2),
            "contributions": round(contributions, 2),
            "investment_income": round(income, 2),
            "growth_rate_pct": round(growth_pct, 2),
        })

        total_income += income
        total_contributions += contributions

    return {
        "entries": entries,
        "total_investment_income": round(total_income, 2),
        "total_contributions": round(total_contributions, 2),
    }


# ---------------------------------------------------------------------------
# Aggregate portfolio snapshots
# ---------------------------------------------------------------------------

@router.get("/aggregate-snapshots", response_model=List[schemas.PortfolioAggregateSnapshot])
def list_aggregate_snapshots(db: Session = Depends(get_db)):
    return (
        db.query(PortfolioAggregateSnapshot)
        .order_by(PortfolioAggregateSnapshot.snapshot_date.desc())
        .all()
    )


@router.post("/aggregate-snapshots", response_model=schemas.PortfolioAggregateSnapshot)
def create_aggregate_snapshot(
    data: schemas.PortfolioAggregateSnapshotCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(PortfolioAggregateSnapshot)
        .filter(PortfolioAggregateSnapshot.snapshot_date == data.snapshot_date)
        .first()
    )
    if existing:
        existing.total_value = data.total_value
        existing.contributions_since_last = data.contributions_since_last
        existing.notes = data.notes
        db.commit()
        db.refresh(existing)
        return existing

    snap = PortfolioAggregateSnapshot(
        snapshot_date=data.snapshot_date,
        total_value=data.total_value,
        contributions_since_last=data.contributions_since_last or 0.0,
        notes=data.notes,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


@router.put("/aggregate-snapshots/{snapshot_id}", response_model=schemas.PortfolioAggregateSnapshot)
def update_aggregate_snapshot(
    snapshot_id: int,
    data: schemas.PortfolioAggregateSnapshotUpdate,
    db: Session = Depends(get_db),
):
    snap = db.query(PortfolioAggregateSnapshot).filter(PortfolioAggregateSnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Aggregate snapshot not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(snap, field, value)
    db.commit()
    db.refresh(snap)
    return snap


@router.delete("/aggregate-snapshots/{snapshot_id}")
def delete_aggregate_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.query(PortfolioAggregateSnapshot).filter(PortfolioAggregateSnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Aggregate snapshot not found")
    db.delete(snap)
    db.commit()
    return {"message": "Aggregate snapshot deleted"}
