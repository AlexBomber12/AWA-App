import { parseBoolean, parseNumber, parsePositiveInt, parseSort, parseString } from "@/lib/parsers";

describe("parsers", () => {
  describe("parsePositiveInt", () => {
    it("parses valid positive integers", () => {
      expect(parsePositiveInt("12", 1)).toBe(12);
      expect(parsePositiveInt("12.9", 1)).toBe(12);
      expect(parsePositiveInt(["25"], 1)).toBe(25);
    });

    it("falls back for invalid values", () => {
      expect(parsePositiveInt(undefined, 5)).toBe(5);
      expect(parsePositiveInt("0", 5)).toBe(5);
      expect(parsePositiveInt("-3", 5)).toBe(5);
      expect(parsePositiveInt("abc", 5)).toBe(5);
      expect(parsePositiveInt(String(Infinity), 5)).toBe(5);
      expect(parsePositiveInt([], 5)).toBe(5);
    });
  });

  describe("parseNumber", () => {
    it("parses floats and integers", () => {
      expect(parseNumber("1.5", 0)).toBeCloseTo(1.5);
      expect(parseNumber("-10", 0)).toBe(-10);
    });

    it("uses fallback for invalid numbers", () => {
      expect(parseNumber(undefined, 4)).toBe(4);
      expect(parseNumber("NaN", 4)).toBe(4);
      expect(parseNumber("infinity", 4)).toBe(4);
      expect(parseNumber([""], 4)).toBe(4);
    });
  });

  describe("parseBoolean", () => {
    it("handles truthy and falsy strings", () => {
      expect(parseBoolean("true", false)).toBe(true);
      expect(parseBoolean("YES", false)).toBe(true);
      expect(parseBoolean("1", false)).toBe(true);
      expect(parseBoolean("no", true)).toBe(false);
      expect(parseBoolean("0", true)).toBe(false);
    });

    it("falls back for unrecognised values", () => {
      expect(parseBoolean(undefined, true)).toBe(true);
      expect(parseBoolean("maybe", false)).toBe(false);
      expect(parseBoolean([], true)).toBe(true);
    });
  });

  describe("parseSort", () => {
    const allowed = ["name_asc", "name_desc"] as const;

    it("returns an allowed sort option", () => {
      expect(parseSort("name_desc", allowed, "name_asc")).toBe("name_desc");
      expect(parseSort(["name_asc"], allowed, "name_desc")).toBe("name_asc");
    });

    it("falls back to the provided default", () => {
      expect(parseSort("invalid", allowed, "name_asc")).toBe("name_asc");
      expect(parseSort(undefined, allowed, "name_desc")).toBe("name_desc");
    });
  });

  describe("parseString", () => {
    it("returns trimmed strings by default", () => {
      expect(parseString("  ASIN-1  ")).toBe("ASIN-1");
      expect(parseString(["  vendor "])).toBe("vendor");
    });

    it("treats empty values as undefined", () => {
      expect(parseString(" ", "fallback")).toBe("fallback");
      expect(parseString(undefined, "fallback")).toBe("fallback");
    });

    it("supports disabling trim/empty handling", () => {
      expect(parseString("  spaced  ", undefined, { trim: false })).toBe("  spaced  ");
      expect(parseString("   ", "keep-spaces", { emptyAsUndefined: false })).toBe("");
    });
  });
});
