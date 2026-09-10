/**
 * Formats an ISO date string or Date object into a readable string.
 *
 * @param {string | Date} dateInput
 * @param {boolean} [includeTime=false]
 * @returns {string}
 */
export function formatDate(dateInput, includeTime = false) {
  if (!dateInput) return "N/A";
  try {
    const date = new Date(dateInput);
    if (isNaN(date.getTime())) return "Invalid Date";

    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      ...(includeTime && { hour: "2-digit", minute: "2-digit" }),
    };
    return new Intl.DateTimeFormat("en-IN", options).format(date);
  } catch (error) {
    return String(dateInput);
  }
}
