export function Card({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="card" onClick={onOpen}>
      <img src="/hero.png" />
    </div>
  );
}
