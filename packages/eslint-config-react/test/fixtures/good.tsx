import { useState, type Ref } from 'react';

type Item = { id: string; label: string; price: number };

type CartProps = {
  items: Item[];
  ref?: Ref<HTMLDivElement>;
  onCheckout: (total: number) => void;
};

export function Cart({ items, ref, onCheckout }: CartProps) {
  const [query, setQuery] = useState('');

  // Derived during render, not synced through an effect.
  const visible = items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
  const total = visible.reduce((sum, item) => sum + item.price, 0);

  return (
    <div ref={ref}>
      <label htmlFor="cart-search">Search</label>
      <input
        id="cart-search"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
        }}
      />
      <ul>
        {visible.map((item) => (
          <li key={item.id}>{item.label}</li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => {
          onCheckout(total);
        }}
      >
        Checkout ({total})
      </button>
    </div>
  );
}
