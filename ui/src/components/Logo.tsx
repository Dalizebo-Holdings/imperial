"use client";

import { LogoMark, LogoWordmark, LogoFull } from "@/lib/brand";

interface LogoProps {
  size?: "small" | "medium" | "large";
  showWordmark?: boolean;
}

export function Logo({ size = "medium", showWordmark = true }: LogoProps) {
  if (showWordmark) {
    return <LogoFull size={size} />;
  }
  const width = size === "small" ? 24 : size === "medium" ? 32 : 40;
  const height = size === "small" ? 24 : size === "medium" ? 32 : 40;
  return <LogoMark width={width} height={height} />;
}

export { LogoMark, LogoWordmark, LogoFull };