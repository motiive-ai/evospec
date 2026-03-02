import { CartItem } from '../components/SmartCart';

const ORDER_SERVICE_URL = process.env.REACT_APP_ORDER_SERVICE_URL || 'http://localhost:8080';
const INVENTORY_SERVICE_URL = process.env.REACT_APP_INVENTORY_SERVICE_URL || 'http://localhost:8000';

export async function checkAvailability(productId: string, quantity: number): Promise<boolean> {
  const res = await fetch(
    `${INVENTORY_SERVICE_URL}/api/products/${productId}/availability?quantity=${quantity}`
  );
  const data = await res.json();
  return data.available;
}

export async function createOrder(items: CartItem[]) {
  const res = await fetch(`${ORDER_SERVICE_URL}/api/orders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: items.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
      })),
    }),
  });
  return res.json();
}

export async function reserveStock(productId: string, orderId: string, quantity: number) {
  const res = await fetch(`${INVENTORY_SERVICE_URL}/api/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ productId, orderId, quantity }),
  });
  return res.json();
}

export async function authorizePayment(orderId: string, amount: number) {
  const res = await fetch(`${ORDER_SERVICE_URL}/api/payments/authorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ orderId, amount }),
  });
  return res.json();
}

export async function confirmReservation(reservationId: string) {
  const res = await fetch(
    `${INVENTORY_SERVICE_URL}/api/reservations/${reservationId}/confirm`,
    { method: 'POST' }
  );
  return res.json();
}
