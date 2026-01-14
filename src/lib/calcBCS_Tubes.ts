import { Tube } from "@/components/types";

export const calcTubes = (tubes: Tube[], rackNumber: string): number => {
  if (!tubes) return 0;
  const rackNumberInt = Number(rackNumber);
  let tubesCountStart = 0;
  let tubesCountEnd = 0;
  if (rackNumberInt === 1) {
    tubesCountStart = 0;
    tubesCountEnd = 50;
  } else if (rackNumberInt === 2) {
    tubesCountStart = 51;
    tubesCountEnd = 100;
  } else if (rackNumberInt === 3) {
    tubesCountStart = 101;
    tubesCountEnd = 150;
  }

  const length = tubes.filter(
    (tube) =>
      tube.position >= tubesCountStart && tube.position <= tubesCountEnd,
  ).length;
  return length;
};
