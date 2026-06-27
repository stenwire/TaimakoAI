from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.order import Order
from app.schemas.order import OrderResponse, OrderStatusUpdate, ORDER_STATUSES
from app.core.response_wrapper import success_response

router = APIRouter(prefix="/orders", tags=["orders"])


def _get_business(db: Session, user_id: str) -> Business:
    business = db.query(Business).filter(Business.user_id == user_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found.")
    return business


@router.get("/", response_model=None)
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business(db, current_user.id)

    query = db.query(Order).filter(Order.business_id == business.id)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    orders = (
        query.order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return success_response(
        data={
            "items": [OrderResponse.from_orm(o) for o in orders],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    )


@router.get("/{order_id}", response_model=None)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business(db, current_user.id)
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return success_response(data=OrderResponse.from_orm(order))


@router.patch("/{order_id}/status", response_model=None)
async def update_order_status(
    order_id: str,
    body: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {ORDER_STATUSES}")

    business = _get_business(db, current_user.id)
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    order.status = body.status
    db.commit()
    db.refresh(order)
    return success_response(message="Order status updated.", data=OrderResponse.from_orm(order))
