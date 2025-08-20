import { describe, it, expect, vi, beforeEach } from "vitest";
import {CSVService} from "../../src/services/csv.service";
import ApiService from "../../src/services/api.service";

vi.mock("@/services/api.service");

describe("CSVService", () => {
  const file = new File(["a,b\n1,2"], "test.csv", { type: "text/csv" });
  const fileId = "123";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should upload CSV file", async () => {
    (ApiService.uploadFile as any).mockResolvedValue({
      data: { preview: [] },
      success: true,
    });
    const res = await CSVService.uploadCSV(file);
    expect(res.success).toBe(true);
    expect(ApiService.uploadFile).toHaveBeenCalledWith(
      "/csv/upload",
      file,
      undefined
    );
  });

  it("should get metadata", async () => {
    (ApiService.get as any).mockResolvedValue({
      data: { columns: [] },
      success: true,
    });
    const res = await CSVService.getMetadata(fileId);
    expect(res.success).toBe(true);
    expect(ApiService.get).toHaveBeenCalledWith(`/csv/${fileId}/metadata`);
  });

  it("should delete file", async () => {
    (ApiService.delete as any).mockResolvedValue({ success: true });
    const res = await CSVService.deleteFile(fileId);
    expect(res.success).toBe(true);
    expect(ApiService.delete).toHaveBeenCalledWith(`/csv/${fileId}`);
  });

  it("should validate file (valid)", () => {
    const result = CSVService.validateFile(file);
    expect(result.isValid).toBe(true);
    expect(result.errors.length).toBe(0);
  });

  it("should validate file (invalid type)", () => {
    const badFile = new File([""], "bad.txt", { type: "text/plain" });
    const result = CSVService.validateFile(badFile);
    expect(result.isValid).toBe(false);
    expect(result.errors[0]).toMatch(/Only CSV files/);
  });

  it("should validate file (too large)", () => {
    const bigFile = new File(["a".repeat(11 * 1024 * 1024)], "big.csv", {
      type: "text/csv",
    });
    Object.defineProperty(bigFile, "size", { value: 11 * 1024 * 1024 });
    const result = CSVService.validateFile(bigFile);
    expect(result.isValid).toBe(false);
    expect(result.errors[0]).toMatch(/exceeds maximum/);
  });

  it("should validate file (empty)", () => {
    const emptyFile = new File([""], "empty.csv", { type: "text/csv" });
    Object.defineProperty(emptyFile, "size", { value: 0 });
    const result = CSVService.validateFile(emptyFile);
    expect(result.isValid).toBe(false);
    expect(result.errors[0]).toMatch(/cannot be empty/);
  });

  it("should return upload tips", () => {
    const tips = CSVService.getUploadTips();
    expect(Array.isArray(tips)).toBe(true);
    expect(tips.length).toBeGreaterThan(0);
  });
});
