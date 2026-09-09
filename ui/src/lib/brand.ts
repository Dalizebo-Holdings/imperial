/**
 * Dalizebo Imperial Brand Identity
 * 
 * Based on "Sovereign Aesthetics" (Pillar 074):
 * Use consistent, high-quality design to signal reliability, confidence,
 * accessibility, technical quality, and brand identity.
 */

// Primary Brand Colors
export const brand = {
  // Deep navy/indigo - primary brand color
  // Signals: reliability, confidence, technical depth, institutional stability
  primary: {
    50: '#eef0f8',
    100: '#dce0f1',
    200: '#b9c1e3',
    300: '#8f9ad1',
    400: '#6b7abf',
    500: '#4f5cad',  // Main brand color
    600: '#3d4a8a',
    700: '#323d70',
    800: '#2a335a',
    900: '#232c4a',
    950: '#181d33',
  },

  // Warm gold/amber - accent color
  // Signals: premium quality, trust, value, excellence
  accent: {
    50: '#fffbf0',
    100: '#fff3cc',
    200: '#ffe799',
    300: '#ffd666',
    400: '#ffc533',
    500: '#ffb300',  // Main accent color
    600: '#cc8f00',
    700: '#996d00',
    800: '#735200',
    900: '#5c4100',
    950: '#332600',
  },

  // Semantic colors
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },

  // Neutral grays
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
    950: '#0a0a0a',
  },
} as const;

// Light theme
export const lightTheme = {
  name: 'light',
  colors: {
    // Background
    background: brand.neutral[50],
    backgroundElevated: '#ffffff',
    backgroundHover: brand.neutral[100],
    
    // Text
    textPrimary: brand.neutral[900],
    textSecondary: brand.neutral[600],
    textMuted: brand.neutral[400],
    textInverse: '#ffffff',
    
    // Brand
    brandPrimary: brand.primary[600],
    brandPrimaryHover: brand.primary[700],
    brandPrimaryLight: brand.primary[100],
    brandAccent: brand.accent[600],
    brandAccentHover: brand.accent[700],
    brandAccentLight: brand.accent[100],
    
    // Borders
    border: brand.neutral[200],
    borderStrong: brand.neutral[300],
    borderFocus: brand.primary[500],
    
    // Semantic
    success: brand.success[600],
    successLight: brand.success[100],
    warning: brand.warning[600],
    warningLight: brand.warning[100],
    error: brand.error[600],
    errorLight: brand.error[100],
    info: brand.info[600],
    infoLight: brand.info[100],
    
    // Status badges
    statusComplete: brand.success[600],
    statusCompleteBg: brand.success[100],
    statusPending: brand.warning[600],
    statusPendingBg: brand.warning[100],
    statusBlocked: brand.error[600],
    statusBlockedBg: brand.error[100],
    
    // Navigation
    navBackground: 'rgba(255, 255, 255, 0.9)',
    navBorder: brand.neutral[200],
    navLinkHover: brand.primary[50],
    navLinkActive: brand.primary[600],
    navLinkActiveText: '#ffffff',
  },
} as const;

// Dark theme
export const darkTheme = {
  name: 'dark',
  colors: {
    // Background
    background: brand.primary[950],
    backgroundElevated: brand.primary[900],
    backgroundHover: brand.primary[800],
    
    // Text
    textPrimary: brand.neutral[50],
    textSecondary: brand.neutral[300],
    textMuted: brand.neutral[500],
    textInverse: brand.primary[950],
    
    // Brand
    brandPrimary: brand.primary[400],
    brandPrimaryHover: brand.primary[300],
    brandPrimaryLight: 'rgba(107, 122, 191, 0.2)',
    brandAccent: brand.accent[400],
    brandAccentHover: brand.accent[300],
    brandAccentLight: 'rgba(255, 179, 0, 0.15)',
    
    // Borders
    border: brand.primary[800],
    borderStrong: brand.primary[700],
    borderFocus: brand.primary[400],
    
    // Semantic
    success: brand.success[500],
    successLight: 'rgba(34, 197, 94, 0.15)',
    warning: brand.warning[500],
    warningLight: 'rgba(245, 158, 11, 0.15)',
    error: brand.error[500],
    errorLight: 'rgba(239, 68, 68, 0.15)',
    info: brand.info[500],
    infoLight: 'rgba(59, 130, 246, 0.15)',
    
    // Status badges
    statusComplete: brand.success[500],
    statusCompleteBg: 'rgba(34, 197, 94, 0.15)',
    statusPending: brand.warning[500],
    statusPendingBg: 'rgba(245, 158, 11, 0.15)',
    statusBlocked: brand.error[500],
    statusBlockedBg: 'rgba(239, 68, 68, 0.15)',
    
    // Navigation
    navBackground: 'rgba(24, 29, 51, 0.9)',
    navBorder: brand.primary[800],
    navLinkHover: 'rgba(107, 122, 191, 0.15)',
    navLinkActive: brand.primary[500],
    navLinkActiveText: '#ffffff',
  },
} as const;

export type Theme = typeof lightTheme;
export type ColorTokens = typeof lightTheme.colors;

// CSS Custom Properties Generator
export function generateCSSVariables(theme: Theme): string {
  const vars: string[] = [];
  for (const [key, value] of Object.entries(theme.colors)) {
    const cssKey = key.replace(/([A-Z])/g, '-$1').toLowerCase();
    vars.push(`  --color-${cssKey}: ${value};`);
  }
  return `:root {\n${vars.join('\n')}\n}`;
}

// Combined CSS for both themes
export const brandCSS = `
${generateCSSVariables(lightTheme)}

@media (prefers-color-scheme: dark) {
${generateCSSVariables(darkTheme).replace(':root {', '').replace('}', '').trim()}
}
`;

// Logo SVG Component
export const LogoMark = () => (
  <svg
    width="32"
    height="32"
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    {/* Outer ring - institutional continuity */}
    <circle
      cx="16"
      cy="16"
      r="15"
      stroke="currentColor"
      strokeWidth="1.5"
      opacity="0.3"
    />
    {/* Inner diamond - precision, structure */}
    <path
      d="M16 4 L28 16 L16 28 L4 16 Z"
      fill="currentColor"
      opacity="0.9"
    />
    {/* Center dot - the kernel, the core */}
    <circle
      cx="16"
      cy="16"
      r="3.5"
      fill="currentColor"
      opacity="1"
    />
    {/* Accent mark - the upward trajectory */}
    <path
      d="M16 10 L16 7 M14 9 L16 7 L18 9"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      opacity="0.8"
    />
  </svg>
);

export const LogoWordmark = () => (
  <svg
    width="120"
    height="28"
    viewBox="0 0 120 28"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <text
      x="0"
      y="22"
      fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
      fontSize="24"
      fontWeight="700"
      fill="currentColor"
      letterSpacing="-0.02em"
    >
      Dalizebo
    </text>
    <text
      x="80"
      y="22"
      fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
      fontSize="14"
      fontWeight="500"
      fill="currentColor"
      opacity="0.7"
      letterSpacing="0.05em"
    >
      Imperial
    </text>
  </svg>
);

export const LogoFull = ({ size = 'medium' }: { size?: 'small' | 'medium' | 'large' }) => {
  const sizes = {
    small: { mark: 24, wordmark: 90, gap: 8 },
    medium: { mark: 32, wordmark: 120, gap: 10 },
    large: { mark: 40, wordmark: 150, gap: 12 },
  };
  const s = sizes[size];
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: s.gap }}>
      <LogoMark style={{ width: s.mark, height: s.mark }} />
      <LogoWordmark style={{ width: s.wordmark, height: s.mark * 0.875 }} />
    </div>
  );
};

export default brand;