// DEPRECATED: Use useSinglePaletteStore from hooks/store.ts instead
// This file is kept for backward compatibility but will be removed
import { useSinglePaletteStore } from "@/hooks/store";

/**
 * @deprecated Use useSinglePaletteStore hook instead
 * This is a hook that returns the single palette zone IDs from the server
 */
export const useSinglePaletteZoneIDs = () => {
  const { singlePaletteZoneIDs, fetchSinglePallets } = useSinglePaletteStore();
  return { singlePaletteZoneIDs, fetchSinglePallets };
};