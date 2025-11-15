'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { isAuthenticated } from '../utils/auth';
import Link from 'next/link';

interface StartPilotButtonProps {
  className?: string;
}

export default function StartPilotButton({ className }: StartPilotButtonProps) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [isAuth, setIsAuth] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsAuth(isAuthenticated());
  }, []);

  if (!mounted) {
    // Return a placeholder during SSR
    return (
      <Link
        href="/auth"
        className={className}
      >
        Start a pilot
      </Link>
    );
  }

  // If authenticated, go to main chat interface
  // If not authenticated, go to auth page
  const href = isAuth ? '/' : '/auth';

  return (
    <Link
      href={href}
      className={className}
    >
      Start a pilot
    </Link>
  );
}

