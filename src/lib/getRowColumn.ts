/**
 * Compute the display row & column for a tube in any of your three layouts:
 *  - Default 5×10 reversed-chunk (rows 46–50 at top, down to 1–5 at bottom)
 *  - 4th-rack / zoneId="15": 10×5 column-major (1,6,11…46 in first row)
 *  - zoneId="17": 15×N row-major (1–15,16–30…)
 *  - zoneId="16": 10×10 reversed-chunk (91–100 at top, down to 1–10 at bottom)
 *
 * @param position      1-based tube position
 * @param isFourthRack  if true, use the 10×5 column-major layout
 * @param zoneId        optional zone ("15","16","17") to override layout
 */
export function getRowColumn(
  position: number,
  isFourthRack = false,
  zoneId?: string
): { row: number; column: number } {
  // --- zone 17: 15 columns, row-major 1–15,16–30,… ---
  if (zoneId === "17") {
    const columns = 15;
    const row = Math.ceil(position / columns);
    const column = ((position - 1) % columns) + 1;
    return { row, column };
  }

  // --- 4th rack or zone 15: 10 columns × 5 rows, column-major ---
  if (isFourthRack || zoneId === "15") {
    // const columns = 10;
    const rows = 5;
    const i = position - 1;             // zero-based
    const row = (i % rows) + 1;         // 1…5
    const column = Math.floor(i / rows) + 1; // 1…10
    return { row, column };
  }

  // --- zone 16: 10 columns × 10 rows, reversed-chunk (91–100 at top) ---
  if (zoneId === "16") {
    const columns = 10;
    const rows = 10;
    const i = position - 1;
    const chunk = Math.floor(i / columns);      // which group of 10
    const rev = rows - 1 - chunk;               // flip top/bottom
    const inner = i % columns;                  // offset in group
    return { row: rev + 1, column: inner + 1 };
  }

  // --- default: 5 columns × 10 rows, reversed-chunk (46–50 at top) ---
  {
    const columns = 5;
    const rows = 10;
    const i = position - 1;
    const chunk = Math.floor(i / columns);
    const rev = rows - 1 - chunk;
    const inner = i % columns;
    return { row: rev + 1, column: inner + 1 };
  }
}
