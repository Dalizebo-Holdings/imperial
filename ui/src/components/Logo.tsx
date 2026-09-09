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
  return <LogoMark style={{ width: size === "small" ? 24 : size === "medium" ? 32 : 40, height: size === "small" ? 24 : size === "medium" ? 32 : 40 }} />;
}

export { LogoMark, LogoWordmark, LogoFull };