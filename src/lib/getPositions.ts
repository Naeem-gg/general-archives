export const getPositionRange = (id: string | undefined) => {
  switch (id) {
    case "1":
      return { start: 1, end: 50 };
    case "2":
      return { start: 51, end: 100 };
    case "3":
      return { start: 101, end: 150 };
    default:
      return { start: 1, end: 50 }; // Default to the first range if id is not recognized
  }
};
