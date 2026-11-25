import { forwardRef } from 'react';
import type React from 'react';

enum Status {
  Active = 'active',
  Inactive = 'inactive',
}

export function parse(input: any): string {
  return String(input);
}

export function first(list: string[]): string {
  const value = list.find((x) => x.length > 0);
  return value!;
}

export const Badge: React.FC<{ status: Status }> = ({ status }) => <span>{status}</span>;

export const Field = forwardRef<HTMLInputElement>(function Field(_props, ref) {
  return <input ref={ref} aria-label="field" />;
});
