export const calculateRacks = (rackCount: number) => {
  const racks = [];
  for (let i = 1; i <= rackCount; i++) {
    racks.push(i.toString());
  }
  return racks;
};
