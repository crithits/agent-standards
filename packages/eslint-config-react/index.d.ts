import type { Linter } from 'eslint';

export type ReactConfigOptions = {
  /** Directory containing tsconfig.json. Pass `import.meta.dirname`. */
  tsconfigRootDir: string;
  /** Extra glob patterns to ignore. */
  ignores?: string[];
  /**
   * Downgrade `react-hooks/set-state-in-effect` to a warning.
   * Use while migrating an existing repo; new repos should leave this off.
   */
  effectRulesAsWarnings?: boolean;
};

export declare function reactConfig(options: ReactConfigOptions): Linter.Config[];
export default reactConfig;
