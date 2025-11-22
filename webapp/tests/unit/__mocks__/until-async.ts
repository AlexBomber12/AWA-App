export async function until<T>(promise: Promise<T>): Promise<[T | null, Error | null]> {
  try {
    const value = await promise;
    return [value, null];
  } catch (error) {
    return [null, error as Error];
  }
}
