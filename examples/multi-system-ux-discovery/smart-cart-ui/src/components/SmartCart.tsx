import React, { useState, useEffect } from 'react';
import { useCart } from '../hooks/useCart';
import { ProductCard } from './ProductCard';
import { CartSummary } from './CartSummary';
import { OneClickCheckout } from './OneClickCheckout';

export interface CartItem {
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  available: boolean;
}

export const SmartCart: React.FC = () => {
  const { items, addItem, removeItem, updateQuantity, total, checkout } = useCart();
  const [isChecking, setIsChecking] = useState(false);

  // NOTE: This allows checkout with zero items — may violate backend invariant!
  const handleOneClickCheckout = async () => {
    setIsChecking(true);
    try {
      await checkout();
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="smart-cart">
      <h2>Smart Cart</h2>
      <div className="cart-items">
        {items.map((item: CartItem) => (
          <ProductCard
            key={item.productId}
            item={item}
            onQuantityChange={(qty: number) => updateQuantity(item.productId, qty)}
            onRemove={() => removeItem(item.productId)}
          />
        ))}
      </div>
      <CartSummary total={total} itemCount={items.length} />
      <OneClickCheckout
        onCheckout={handleOneClickCheckout}
        disabled={isChecking}
        total={total}
      />
    </div>
  );
};

export default SmartCart;
