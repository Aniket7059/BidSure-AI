import { z } from "zod";

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email address is required")
    .email("Enter a valid email address (e.g. officer@cpcl.gov.in)"),
  password: z
    .string()
    .min(1, "Password is required"),
});
