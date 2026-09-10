"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

export default function ValidationPage() {
  const pathname = usePathname();

  return (
    <div>
      <h1>Validation</h1>
    </div>
  );
}