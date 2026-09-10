import { z } from "zod";

export const tenderSchema = z.object({
  tender_number: z.string().min(1, "Tender number is required"),
  title: z.string().min(3, "Title must be at least 3 characters"),
  department: z.string().optional(),
  estimated_value: z.number().optional(),
});
