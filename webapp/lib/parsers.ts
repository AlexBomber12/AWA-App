type QueryValue = string | string[] | null | undefined;

const extractFirstValue = (value: QueryValue): string | undefined => {
  if (value === null || value === undefined) {
    return undefined;
  }
  if (Array.isArray(value)) {
    return value.length > 0 ? value[0] : undefined;
  }
  return value;
};

const toTrimmedLowerCase = (value: QueryValue): string | undefined => {
  const first = extractFirstValue(value);
  return first ? first.trim().toLowerCase() : undefined;
};

export function parsePositiveInt(value: QueryValue, fallback: number): number {
  const first = extractFirstValue(value);
  if (!first) {
    return fallback;
  }
  const parsed = Number(first);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  const normalized = Math.floor(parsed);
  return normalized > 0 ? normalized : fallback;
}

export function parseNumber(value: QueryValue, fallback: number): number {
  const first = extractFirstValue(value);
  if (first === undefined || first.trim() === "") {
    return fallback;
  }
  const parsed = Number(first);
  return Number.isFinite(parsed) ? parsed : fallback;
}

const TRUE_VALUES = new Set(["true", "1", "yes", "y", "on"]);
const FALSE_VALUES = new Set(["false", "0", "no", "n", "off"]);

export function parseBoolean(value: QueryValue, fallback: boolean): boolean {
  const normalized = toTrimmedLowerCase(value);
  if (!normalized) {
    return fallback;
  }
  if (TRUE_VALUES.has(normalized)) {
    return true;
  }
  if (FALSE_VALUES.has(normalized)) {
    return false;
  }
  return fallback;
}

export function parseSort<TSort extends string>(
  value: QueryValue,
  allowed: readonly TSort[],
  fallback: TSort
): TSort {
  const first = extractFirstValue(value);
  if (first && (allowed as readonly string[]).includes(first)) {
    return first as TSort;
  }
  return fallback;
}

type ParseStringOptions = {
  trim?: boolean;
  emptyAsUndefined?: boolean;
};

export function parseString(
  value: QueryValue,
  fallback?: string,
  options?: ParseStringOptions
): string | undefined {
  const first = extractFirstValue(value);
  if (first === undefined) {
    return fallback;
  }

  const shouldTrim = options?.trim ?? true;
  const normalized = shouldTrim ? first.trim() : first;
  const emptyAsUndefined = options?.emptyAsUndefined ?? true;

  if (normalized.length === 0) {
    return emptyAsUndefined ? fallback : normalized;
  }
  return normalized;
}

export type { QueryValue };
