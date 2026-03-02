"""Inventory Service — manages products, stock levels, and reservations."""

from fastapi import FastAPI, HTTPException
from app.models import Product, StockReservation
from app.schemas import (
    CreateProductRequest,
    UpdateStockRequest,
    ReserveStockRequest,
    ReservationResponse,
)

app = FastAPI(title="Inventory Service", version="1.0.0")


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get a product by ID with current stock level."""
    pass


@app.get("/api/products")
async def list_products(category: str = None, in_stock: bool = None):
    """List products with optional filtering."""
    pass


@app.post("/api/products")
async def create_product(request: CreateProductRequest):
    """Create a new product in the catalog."""
    pass


@app.put("/api/products/{product_id}/stock")
async def update_stock(product_id: str, request: UpdateStockRequest):
    """Update stock level for a product (warehouse intake)."""
    pass


@app.get("/api/products/{product_id}/availability")
async def check_availability(product_id: str, quantity: int = 1):
    """Check if a product is available in the requested quantity."""
    pass


@app.post("/api/reservations")
async def reserve_stock(request: ReserveStockRequest):
    """Reserve stock for a pending order. Reservation expires in 30 minutes."""
    pass


@app.delete("/api/reservations/{reservation_id}")
async def release_reservation(reservation_id: str):
    """Release a stock reservation (order cancelled or expired)."""
    pass


@app.post("/api/reservations/{reservation_id}/confirm")
async def confirm_reservation(reservation_id: str):
    """Confirm a reservation (order paid). Permanently decrements stock."""
    pass


@app.get("/api/reservations/order/{order_id}")
async def get_order_reservations(order_id: str):
    """Get all reservations for a given order."""
    pass
