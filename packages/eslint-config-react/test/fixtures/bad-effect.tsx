import { useEffect, useState } from 'react';

type Props = { first: string; last: string };

export function FullName({ first, last }: Props) {
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    setFullName(`${first} ${last}`);
  }, [first, last]);

  return <p>{fullName}</p>;
}
