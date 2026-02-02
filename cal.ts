function myFunction(rows: number, columns: number, corner: number, direction: number): number[][] {
    const total = rows * columns;
    const matrix: number[][] = Array.from({ length: rows }, () => Array(columns).fill(0));
    
    // Determine starting position based on corner
    let startRow = 0, startCol = 0;
    if (corner === 1) { // top-left
        startRow = 0; startCol = 0;
    } else if (corner === 2) { // top-right
        startRow = 0; startCol = columns - 1;
    } else if (corner === 3) { // bottom-right
        startRow = rows - 1; startCol = columns - 1;
    } else if (corner === 4) { // bottom-left
        startRow = rows - 1; startCol = 0;
    }
    
    // Direction vectors: [rowDelta, colDelta]
    const directions = [
        [0, 1],   // 1: right
        [1, 0],   // 2: down
        [0, -1],  // 3: left
        [-1, 0]   // 4: up
    ];
    
    const [primaryRowDelta, primaryColDelta] = directions[direction - 1];
    
    // Fill the matrix
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
    
    return matrix;
}
console.log(myFunction(10,5,4,4))

//{
        //     "corners":{1:"top-left",2:"top-right",3:"bottom-right",4:"bottom-left"},
        //     "directions":{1:"right",2:"down",3:"left",4:"up"}
        // }