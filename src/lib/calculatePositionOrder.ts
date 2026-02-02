/**
 * Calculate position order based on corner and direction
 * Logic adapted from cal.ts - returns positions in fill order
 * 
 * Corners: 1=top-left, 2=top-right, 3=bottom-right, 4=bottom-left
 * Directions: 1=right, 2=down, 3=left, 4=up
 * 
 * @param rows Number of rows
 * @param columns Number of columns
 * @param corner Starting corner (1-4)
 * @param direction Movement direction (1-4)
 * @returns Array of position numbers (1-based) in the order they should be filled
 */
export function calculatePositionOrder(
  rows: number,
  columns: number,
  corner: number,
  direction: number
): number[] {
  const total = rows * columns;
  
  // Helper to convert row,col (0-based) to position (1-based)
  const posToIndex = (r: number, c: number): number => {
    return r * columns + c + 1;
  };
  
  // Create matrix like cal.ts does
  const matrix: number[][] = Array.from({ length: rows }, () => Array(columns).fill(0));
  
  // Determine starting position based on corner (0-based)
  let startRow = 0, startCol = 0;
  if (corner === 1) { // top-left
    startRow = 0;
    startCol = 0;
  } else if (corner === 2) { // top-right
    startRow = 0;
    startCol = columns - 1;
  } else if (corner === 3) { // bottom-right
    startRow = rows - 1;
    startCol = columns - 1;
  } else if (corner === 4) { // bottom-left
    startRow = rows - 1;
    startCol = 0;
  }
  
  // Direction vectors: [rowDelta, colDelta]
  const directions = [
    [0, 1],   // 1: right
    [1, 0],   // 2: down
    [0, -1],  // 3: left
    [-1, 0]   // 4: up
  ];
  
  const [primaryRowDelta, primaryColDelta] = directions[direction - 1];
  
  // Fill the matrix exactly like cal.ts
  let currentRow = startRow;
  let currentCol = startCol;
  let count = 0;
  
  for (let num = 1; num <= total; num++) {
    matrix[currentRow][currentCol] = num;
    count++;
    
    if (num < total) {
      // Check if we need to wrap to next line
      if (count >= (primaryColDelta !== 0 ? columns : rows)) {
        count = 0;
        // Move perpendicular to the primary direction
        if (primaryColDelta !== 0) { // Moving horizontally
          currentRow += (corner === 1 || corner === 2) ? 1 : -1;
          currentCol = startCol; // Reset to starting column
        } else { // Moving vertically
          currentCol += (corner === 1 || corner === 4) ? 1 : -1;
          currentRow = startRow; // Reset to starting row
        }
      } else {
        // Continue in primary direction
        currentRow += primaryRowDelta;
        currentCol += primaryColDelta;
      }
    }
  }
  
  // Convert matrix to 1D array of positions in fill order
  // The matrix contains numbers 1, 2, 3, ... representing fill order
  // We need to find position for each number and return them in order
  const result: number[] = new Array(total);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < columns; c++) {
      const fillOrder = matrix[r][c]; // 1-based fill order (1, 2, 3, ...)
      const position = posToIndex(r, c); // 1-based position number
      result[fillOrder - 1] = position; // Store position at its fill order index
    }
  }
  
  return result;
}
