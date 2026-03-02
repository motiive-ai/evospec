import { useState, useCallback } from 'react';
import { CartItem } from '../components/SmartCart';
import { checkAvailability, createOrder, reserveStock, authorizePayment } from '../api/client';

export function useCart() {
  const [items, setItems] = useState<CartItem[]>([]);

  const addItem = useCallback(async (productId: string, productName: string, unitPrice: number) => {
    // Check availability in real-time
    const available = await checkAvailability(productId, 1);
    setItems(prev => [...prev, {
      productId,
      productName,
      quantity: 1,
      unitPrice,
      available,
    }]);
  }, []);

  const removeItem = useCallback((productId: string) => {
    setItems(prev => prev.filter(item => item.productId !== productId));
  }, []);

  const updateQuantity = useCallback(async (productId: string, quantity: number) => {
    const available = await checkAvailability(productId, quantity);
    setItems(prev => prev.map(item =>
      item.productId === productId
        ? { ...item, quantity, available }
        : item
    ));
  }, []);

  const total = items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);

  // WARNING: This checkout flow may violate multiple backend invariants:
  // 1. Creates order without checking if items list is non-empty
  // 2. Reserves stock but doesn't handle 30-minute expiration
  // 3. Attempts payment after order creation (backend requires payment BEFORE confirmation)
  const checkout = useCallback(async () => {
    // Step 1: Create order with current cart items
    const order = await createOrder(items);

    // Step 2: Reserve stock for all items
    for (const item of items) {
      await reserveStock(item.productId, order.id, item.quantity);
    }

    // Step 3: Authorize payment
    const payment = await authorizePayment(order.id, total);

    // Step 4: What happens if payment fails? Stock is already reserved...
    // TODO: Handle rollback

    return { order, payment };
  }, [items, total]);

  return { items, addItem, removeItem, updateQuantity, total, checkout };
}
