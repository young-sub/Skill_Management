import { z } from "zod";

export const UNIT_LABELS = {
  ea: "개", bottle: "병", box: "박스", pack: "팩", sachet: "포", tablet: "정",
  capsule: "캡슐", vial: "바이알", sheet: "장", stick: "스틱", ml: "mL", g: "g", custom: "직접 입력",
} as const;

export const PRODUCT_XLSX_HEADERS = [
  "상품ID(수정금지)", "현재버전(수정금지)", "대분류", "중분류", "소분류", "상품명_한국어", "설명_한국어",
  "단품수량", "단품가격_원", "단위", "직접입력단위",
  ...Array.from({ length: 9 }, (_, index) => [`묶음수량_${index + 1}`, `묶음가격_원_${index + 1}`]).flat(), "통화",
] as const;
export const PREVIOUS_PRODUCT_XLSX_HEADERS = PRODUCT_XLSX_HEADERS.slice(0, -1);
export const LEGACY_PRODUCT_XLSX_HEADERS = [
  "상품ID(수정금지)", "현재버전(수정금지)", "분류", "상품명_한국어", "설명_한국어",
  "단품가격_원", "단위", "직접입력단위", "묶음수량", "묶음가격_원",
] as const;
export const PRODUCT_XLSX_ROW_KIND_HEADER = "_row_kind";
export const MAX_PRODUCT_OFFERS = 10;
export const PRODUCT_CURRENCIES = ["KRW", "USD", "CNY", "JPY", "EUR"] as const;
export type ProductCurrency = typeof PRODUCT_CURRENCIES[number];
export const formatProductPrice = (amount: number, currency: ProductCurrency = "KRW") => `${amount.toLocaleString("ko-KR", { minimumFractionDigits: currency === "KRW" ? 0 : 2, maximumFractionDigits: 2 })}${currency === "KRW" ? "원" : ` ${currency}`}`;

const unitCode = z.enum(Object.keys(UNIT_LABELS) as [keyof typeof UNIT_LABELS, ...(keyof typeof UNIT_LABELS)[]]);

export const offerSchema = z.object({
  quantity: z.number().int().min(1).max(999),
  unitCode,
  unitCustomKo: z.string().trim().min(1).max(20).optional(),
  priceKrw: z.number().min(0).max(99_999_999).refine((value) => Math.abs(value * 100 - Math.round(value * 100)) < 0.000001, "가격은 소수점 둘째 자리까지 입력해 주세요."),
}).superRefine((offer, context) => {
  if (offer.unitCode === "custom" && !offer.unitCustomKo) {
    context.addIssue({ code: "custom", message: "직접 입력 단위를 적어 주세요.", path: ["unitCustomKo"] });
  }
  if (offer.unitCode !== "custom" && offer.unitCustomKo) {
    context.addIssue({ code: "custom", message: "직접 입력 단위는 단위가 '직접 입력'일 때만 사용해 주세요.", path: ["unitCustomKo"] });
  }
});

const productFields = {
  categoryId: z.string().min(1),
  nameKo: z.string().trim().min(1).max(100),
  descriptionKo: z.string().trim().min(1).max(500),
  templateKeyOverride: z.string().trim().min(1).optional().nullable(),
  currencyCode: z.enum(PRODUCT_CURRENCIES).default("KRW"),
};
export const offersSchema = z.array(offerSchema).min(1).max(MAX_PRODUCT_OFFERS).superRefine((offers, context) => {
  const quantities = new Set<number>();
  const unit = offers[0] && offers[0].unitCode + "\0" + (offers[0].unitCustomKo ?? "");
  offers.forEach((offer, index) => {
    if (quantities.has(offer.quantity)) context.addIssue({
      code: "custom", message: "수량은 중복해서 등록할 수 없습니다.", path: [index, "quantity"],
    });
    quantities.add(offer.quantity);
    if (offer.unitCode + "\0" + (offer.unitCustomKo ?? "") !== unit) context.addIssue({
      code: "custom", message: "묶음 단위는 단품 단위와 같아야 합니다.", path: [index, "unitCode"],
    });
  });
});

export const createProductSchema = z.object({ ...productFields, offers: offersSchema });

export const updateProductSchema = z.object({
  expectedVersion: z.number().int().min(1),
  categoryId: z.string().min(1).optional(),
  nameKo: z.string().trim().min(1).max(100).optional(),
  descriptionKo: z.string().trim().min(1).max(500).optional(),
  templateKeyOverride: z.string().trim().min(1).optional().nullable(),
  currencyCode: z.enum(PRODUCT_CURRENCIES).optional(),
  offers: offersSchema.optional(),
  isActive: z.boolean().optional(),
});

export type ProductInput = z.infer<typeof createProductSchema>;
export type ProductUpdate = z.infer<typeof updateProductSchema>;

export const normalizeText = (value: string): string => value.normalize("NFKC").trim().replace(/\s+/g, " ");

export const sourceHash = async (source: {
  nameKo: string;
  descriptionKo: string;
  categoryId: string;
  categoryNameKo: string;
}): Promise<string> => {
  const normalized = JSON.stringify({
    nameKo: normalizeText(source.nameKo),
    descriptionKo: normalizeText(source.descriptionKo),
    categoryId: normalizeText(source.categoryId),
    categoryNameKo: normalizeText(source.categoryNameKo),
  });
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
};
